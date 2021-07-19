import ffmpeg
import subprocess
import re
import numpy as np
import cv2

from multiprocessing import Queue, Process, Pipe
from io import BytesIO
from PIL import Image
from flask import Flask, Response, render_template, jsonify, request
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

FPS = 30
BITRATE = '25M'         
CHUNK_SIZE = 2**14      # How many bytes for ffmpeg to write/read 
FORMAT = 'mjpeg'

# Apply the default camera settings
subprocess.check_call(
    'bash default-v4l2-settings.sh'.split())

capture_queue = Queue()
record_flag_read, record_flag_write = Pipe()

class VideoReader:
    def __init__(self):
        self.reader = self.create_reader()
        self.image_size = self.get_frame_size()

    def get_frame_size(self):
        """Get the number of bytes in each image"""
        image_size = CHUNK_SIZE
        return image_size

    def create_reader(self):
        """Creates an FFMpeg VIdeo Reader"""
        return (ffmpeg
            .input(
                '/dev/video0', 
                input_format=FORMAT,
                format="v4l2",
                framerate=FPS,
            )
            .output(
                'pipe:',
                loglevel='error',
                bufsize='128M',
                format=FORMAT,
                codec='copy',
                chunk_size=CHUNK_SIZE,
                **{'b:v': BITRATE}
            )
            .run_async(pipe_stdout=True))

    def get_frame(self):
        """Return a frame"""
        return self.reader.stdout.read(self.image_size)

def get_writer():
    """Created an FFMpeg Video Writer"""
    return (ffmpeg
        .input(
            'pipe:', 
            framerate=FPS,
            format=FORMAT,
        )
        .output(
            'test.mp4',
            # loglevel='error',
            bufsize='128M',
            codec='copy',
            **{'b:v': BITRATE}
        )
        .overwrite_output()
        .run_async(pipe_stdin=True))

def get_decoder():
    """Created an FFMpeg Video Writer"""
    return (ffmpeg
        .input(
            'pipe:', 
            framerate=FPS,
            format=FORMAT,
        )
        .filter('fps', fps=12, round='up')
        .filter('scale', 640, 480) # width, height
        .output(
            'pipe:',
            loglevel='error',
            bufsize='128M',
            format='rawvideo',
            pix_fmt='rgb24',
            **{'b:v': '128K'}
        )
        .overwrite_output()
        .run_async(pipe_stdin=True, pipe_stdout=True))

decoder = get_decoder()

def consume_frames(decoder, record_flag_read, **kwargs):
    reader = VideoReader()
    count = 0
    record = False 
    writer = None
    while True:
        if record_flag_read.poll():
            old_record = record
            record = record_flag_read.recv()
            
            # Create or stop a writer
            if record and not writer:   
                writer = get_writer()
            elif not record and writer:
                writer.stdin.close()
                writer.wait()
                writer = None

        count += 1
        raw_frame = reader.get_frame()
        decoder.stdin.write(raw_frame)
        if record and writer:
            writer.stdin.write(raw_frame)

def make_jpg(capture_queue, decoder, **kwargs):
    shape = (480, 640, 3) # Height, Width, Channels

    while True:
        frame = decoder.stdout.read(np.product(shape))
        data = np.frombuffer(frame, np.uint8)
        image = Image.fromarray(data.reshape(*shape))
        out = BytesIO()
        image.save(out, 'JPEG')
        out.seek(0)
        capture_queue.put(out.read())

def gen():
    while True:
        out = capture_queue.get()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + out + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_recording')
def start_recording():
    record_flag_write.send(True)
    return Response()

@app.route('/stop_recording')
def stop_recording():
    record_flag_write.send(False)
    return Response()

@app.route('/settings', methods=['GET'])
def settings():
    result = subprocess.check_output(['v4l2-ctl', '-d', '0', '-L']).decode('utf-8')

    # Split v4l2 options
    split_options = re.compile(
        r"(\w+\s+[\w\d]+\s+\(\w+\)\s+\:.*(?:\n\s+\d+.*)*)",
    )

    # Extract options from lines
    extract_option_details = re.compile(
        '^\s*(?P<name>[\w\_]+)'             # Name
        '\s[\w\d]+'
        '\s\((?P<dtype>\w+)\)'              # Dtype
        '.*?\:\s' 
        '(min\=(?P<min>\-?\d+)\s)?'         # Min
        '(max\=(?P<max>\d+)\s)?'            # Max
        '(step\=(?P<step>\d+)\s)?'          # Step
        '(default\=(?P<default>\d+)\s?)?'   # Default
        '(value\=(?P<value>\d+)\s?)?'       # Value
    )

    # Extract menu items 
    extract_menu_items = re.compile(
        '\s*(?P<value>\d+)\:\s*(?P<display>\w+)'
    )

    results = []
    options = split_options.findall(result)
    for option in options:
        main, *items = option.split('\n')
        result = extract_option_details.match(main).groupdict()
        result['options'] = [
            extract_menu_items.match(i).groupdict() for i in items]
        results.append(result)

    print(results)
    return jsonify({'data': results})

@app.route('/settings/<string:setting>', methods=['PUT'])
def set_setting(setting):
    value = request.get_data(cache=False, as_text=True)
    print('update:', setting, value)
    try: 
        result = subprocess.check_output(['v4l2-ctl', '-c', f"{setting}={value}"])
        return jsonify({'results': 'good'})
    except Exception as e:
        print(e)
        return jsonify({'errmsg': str(e)}), 500

shared_kwargs = {
    'capture_queue': capture_queue,
    'decoder': decoder,
    'record_flag_read': record_flag_read
}

capture_process = Process(
    name="capture", target=consume_frames, kwargs=shared_kwargs)
capture_process.start()

decoder_process = Process(
    name="decoder", target=make_jpg, kwargs=shared_kwargs)
decoder_process.start()
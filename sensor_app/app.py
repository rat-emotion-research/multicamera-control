import ffmpeg
import subprocess
import re
import numpy as np
import cv2

from multiprocessing import Queue, Process, Pipe()
from io import BytesIO
from PIL import Image
from flask import Flask, Response, render_template

app = Flask(__name__)

FPS = 30
FORMAT = 'h264'
BITRATE = '25M'
CHUNK_SIZE = 2**14

capture_queue = Queue()
record_flag_read, record_flag_write = Pipe()

class VideoReader:
    def __init__(self):
        self.reader = self.create_reader()
        self.image_size = self.get_frame_size()

    def get_frame_size(self):
        """Get the number of bytes in each image"""
        # vidcap_settings = subprocess.check_output('v4l2-ctl -V'.split())
        # vidcap_settings = vidcap_settings.decode()
        # match = re.search(r'Size Image\s*\:\s*(\d+)', vidcap_settings)
        # image_size = int(match.groups()[0])
        # print(image_size)
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
            # pix_fmt='yuv420p',
        )
        .filter('fps', fps=24, round='up')
        .filter('scale', 640, 480) # width, height
        .output(
            'pipe:',
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
        if record_flag_read.poll()
            old_record = record
            record = pipe.recv()
            
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
    return 

@app.route('/stop_recording')
def start_recording():
    record_flag_write.send(False)
    return 

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
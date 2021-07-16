import ffmpeg
import subprocess
import re
from io import BytesIO
from PIL import Image
from flask import Flask, Response, render_template

app = Flask(__name__)

FPS = 30
FORMAT = 'mjpeg'
BITRATE = '25M'

class VideoReader:
    def __init__(self):
        self.reader = self.create_reader()
        self.image_size = self.get_frame_size()

    def get_frame_size(self):
        """Get the number of bytes in each image"""
        vidcap_settings = subprocess.check_output('v4l2-ctl -V'.split())
        vidcap_settings = vidcap_settings.decode()
        match = re.search(r'Size Image\s*\:\s*(\d+)', vidcap_settings)
        image_size = int(match.groups()[0])
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
                t=10,
                bufsize='128M',
                format=FORMAT,
                codec='copy',
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

reader = VideoReader()

def gen():
    while True:
        raw_frame = reader.get_frame()
        small_frame = raw_frame.to_bytes()
        # decoded_frame = Image.open(BytesIO(raw_frame))
        # small_frame = decoded_frame.resize((320, 240))
        # small_frame = small_frame.tobytes("jpg", "rgb")
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + small_frame + b'\r\n\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(),
        mimetype='multipart/x-mixed-replace; boundary=frame')
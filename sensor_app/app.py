from flask import Flask, Response

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

def gen(camera):
    while True:
        #get camera frame
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
               
@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
        mimetype='multipart/x-mixed-replace; boundary=frame')


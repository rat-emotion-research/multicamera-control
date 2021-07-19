# Setting descriptions
# https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/ext-ctrls-camera.html

# Manual exposure time (so that FPS doesn't change)
v4l2-ctl -c auto_exposure=1

# Set to sports which increases iso speed (faster shutter speed = clearer images of motion)
v4l2-ctl -c scene_mode=0

# Change absolute exposure time, the argument is in 1/10000th of a second. eg if set to 100
# then exposure time = 100/10000->1ms
v4l2-ctl -c exposure_time_absolute=100

# Quality 
v4l2-ctl -v width=1920,height=1080
v4l2-ctl -c video_bitrate=25000000
v4l2-ctl -c video_bitrate_mode=1        

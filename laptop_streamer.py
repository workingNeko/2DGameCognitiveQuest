import cv2

from flask import Flask, Response

app = Flask(__name__)

# Open laptop camera (0 is default built-in webcam)
cap = cv2.VideoCapture(0)

# Set resolution low for ultra-low latency over Wi-Fi
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

def generate_frames():
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            # Re-ensure size is exactly 320x240
            frame = cv2.resize(frame, (320, 240))
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            # Stream frames continuously
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # Listen on all local interfaces on port 5000
    print("🚀 Starting Laptop Streamer...")
    print("Press Ctrl+C to stop.")
    app.run(host='0.0.0.0', port=5000, threaded=True)

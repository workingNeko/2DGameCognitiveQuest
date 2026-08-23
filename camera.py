import cv2

# Replace this with your A9 camera's IP stream URL
camera_url = "rtsp://192.168.1.15:554/live/ch0"

cap = cv2.VideoCapture(camera_url)

if not cap.isOpened():
    print("❌ Cannot open the IP camera stream. Check IP address or URL!")
else:
    print("✅ Connected to the camera stream successfully!")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to receive frame. Stream might have dropped.")
        break
        
    # Display the camera feed in a window
    cv2.imshow("A9 Camera Feed Test", frame)
    
    # Press 'q' on your keyboard to close the window
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

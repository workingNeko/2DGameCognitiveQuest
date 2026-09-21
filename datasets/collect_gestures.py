# datasets/collect_gestures.py
"""
Webcam Gesture Dataset Collector for MediaPipe Hand Landmarks.
Use this script to collect landmark coordinate samples (63 floats) for any gesture:
- fist_left / fist_right
- open_left / open_right
- peace_left / peace_right

Press 's' to start/stop continuous recording samples.
Press 'q' or 'ESC' to save and exit.
"""

import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import os
import time

def collect_gesture_data(gesture_label="peace_right", num_samples=150, output_csv="datasets/gesture_dataset.csv"):
    os.makedirs("datasets", exist_ok=True)
    
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6
    )
    
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
        
    print(f"=== COLLECTING SAMPLES FOR: {gesture_label} ===")
    print("Press SPACE or 'S' to start/pause recording samples.")
    print("Press 'Q' to quit and save.")
    
    samples = []
    recording = False
    
    while cap.isOpened() and len(samples) < num_samples:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.flip(frame, 1)
        h, w, c = frame.shape
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        hand_detected = False
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp.solutions.drawing_utils.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
            )
            hand_detected = True
            
            if recording:
                # Wrist centered normalization (63 features)
                wrist = hand_landmarks.landmark[0]
                row = []
                for lm in hand_landmarks.landmark:
                    row.extend([lm.x - wrist.x, lm.y - wrist.y, lm.z - wrist.z])
                row.append(gesture_label)
                samples.append(row)
                time.sleep(0.04) # ~25 samples per second
                
        status_text = f"Recording: {len(samples)}/{num_samples}" if recording else "PAUSED (Press SPACE to record)"
        color = (0, 255, 0) if recording else (0, 165, 255)
        cv2.putText(frame, f"Label: {gesture_label}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, status_text, (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow("Gesture Data Collector", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord(' ') or key == ord('s'):
            recording = not recording
            
    cap.release()
    cv2.destroyAllWindows()
    
    if samples:
        cols = []
        for i in range(21):
            cols.extend([f"x{i}", f"y{i}", f"z{i}"])
        cols.append("label")
        
        new_df = pd.DataFrame(samples, columns=cols)
        if os.path.exists(output_csv):
            existing_df = pd.read_csv(output_csv)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df.to_csv(output_csv, index=False)
            print(f"[OK] Added {len(samples)} rows to {output_csv} (Total: {len(combined_df)} rows).")
        else:
            new_df.to_csv(output_csv, index=False)
            print(f"[OK] Saved {len(samples)} rows to new file {output_csv}.")
    else:
        print("[INFO] No samples recorded.")

if __name__ == "__main__":
    import sys
    label = sys.argv[1] if len(sys.argv) > 1 else "peace_right"
    collect_gesture_data(gesture_label=label)

import cv2
import face_recognition
import pickle
import os
import numpy as np

def running_scan() :
    try:
        with open('face_dataset.dat', 'rb') as f:
            data = pickle.load(f)
            
    except FileNotFoundError:
        print("Dataset wajah tidak ditemukan. Pastikan kamu sudah mendaftarkan setidaknya satu wajah.")
        return
    
    known_face_names = list(data.keys())
    known_face_encodings = list(data.values())
    
    video_capture = cv2.VideoCapture(0)
    
    print("Scanner Activated : Push 'Q' to quit.")
    
    while True:
        ret, frame = video_capture.read()
        
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                
            if name == "Unknown":
                color = (0, 0, 255)
            else:
                color = (0, 255, 0)

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

            text = name
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            thickness = 1
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            label_left = left
            label_top = bottom + 8
            label_right = left + text_width + 12
            label_bottom = bottom + text_height + baseline + 12

            cv2.rectangle(frame, (label_left, label_top), (label_right, label_bottom), color, cv2.FILLED)
            cv2.putText(frame, text, (left + 6, label_bottom - 6), font, font_scale, (255, 255, 255), thickness)

        cv2.imshow('Face Recognition Scanner', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        
    video_capture.release()
    cv2.destroyAllWindows()
    
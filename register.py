import cv2
import numpy as np
import face_recognition
import pickle
import os
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.*=false"

def face_register():

    name = input("Masukkan nama untuk didaftarkan: ")

    video_capture = cv2.VideoCapture(0)
    print("Mencari wajah... Pastikan pencahayaan cukup dan lihat ke kamera.")
    if not video_capture.isOpened():
        print("Cannot open camera")
        exit()
    while True:
        ret, frame = video_capture.read()
        
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break

        display_frame = frame.copy()
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        for top, right, bottom, left in face_locations:
            cv2.rectangle(display_frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.imshow('Proses Pendaftaran - tekan Space untuk mengambil gambar', display_frame)
        
        k = cv2.waitKey(1)
        
        if k %256 == 32:
            
            if len(face_locations) > 0:
                print(f"Face detected for {name}.")
            
                new_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
                old_data = {}
                
                if os.path.exists('face_dataset.dat') :
                    with open('face_dataset.dat', 'rb') as f:
                        old_data = pickle.load(f)

                if old_data:
                    known_encodings = list(old_data.values())
                    matches = face_recognition.compare_faces(known_encodings, new_encoding, tolerance=0.6)

                    if True in matches:
                        index = matches.index(True)
                        existing_name = list(old_data.keys())[index]
                        print(f"Peringatan: Wajah ini sudah terdaftar sebagai '{existing_name}'!")
                        
                old_data[name] = new_encoding
                
                with open('face_dataset.dat', 'wb') as f:
                    pickle.dump(old_data, f)
                    
                print(f"Face encoding for {name} has been registered.")
                break
            else:
                print("No face detected. Please try again.")
        
        elif k % 256 == 27:
            print("Registration cancelled.")
            break
        
    video_capture.release()
    cv2.destroyAllWindows()

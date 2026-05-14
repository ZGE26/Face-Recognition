"""
Demo standalone face recognition menggunakan webcam.
Dataset disimpan secara lokal di demo/face_dataset.dat (tidak terhubung ke database API).

Jalankan:
    python demo/main.py
"""

import register
import scan


def main():
    while True:
        print("\nMenu:")
        print("1. Register Face")
        print("2. Scan Face")
        print("3. Exit")

        choice = input("Pilih opsi (1/2/3): ")

        if choice == "1":
            register.face_register()
        elif choice == "2":
            scan.running_scan()
        elif choice == "3":
            print("Exiting program.")
            break
        else:
            print("Invalid choice. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()

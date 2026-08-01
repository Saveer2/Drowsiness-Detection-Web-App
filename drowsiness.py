import threading

import cv2
import dlib
import pyttsx3
import os
import time
from scipy.spatial import distance

from queue import Queue

engine = pyttsx3.init()
engine.setProperty("rate", 170)

speech_queue = Queue()


def speech_worker():

    while True:

        text = speech_queue.get()

        engine.say(text)
        engine.runAndWait()

        speech_queue.task_done()


threading.Thread(
    target=speech_worker,
    daemon=True
).start()


def speak(text):

    if speech_queue.empty():

        speech_queue.put(text)


face_detector = dlib.get_frontal_face_detector()

dat_file = "shape_predictor_68_face_landmarks.dat"

if not os.path.exists(dat_file):
    raise FileNotFoundError(f"{dat_file} not found in current folder.")

dlib_facelandmark = dlib.shape_predictor(dat_file)

current_status = "Monitoring..."
current_ear = 0.0
current_mar = 0.0

EAR_THRESHOLD = 0.24
EAR_ALERT_DELAY = 5

MAR_THRESHOLD = 0.60
MAR_ALERT_DELAY = 3

eye_closed_start = None
mouth_open_start = None

eye_alert_triggered = False
yawn_alert_triggered = False


def detect_eye(eye_points):

    A = distance.euclidean(eye_points[1], eye_points[5])
    B = distance.euclidean(eye_points[2], eye_points[4])
    C = distance.euclidean(eye_points[0], eye_points[3])

    return (A + B) / (2.0 * C)


def detect_mouth(mouth_points):

    A = distance.euclidean(mouth_points[2], mouth_points[10])
    B = distance.euclidean(mouth_points[4], mouth_points[8])
    C = distance.euclidean(mouth_points[0], mouth_points[6])

    return (A + B) / (2.0 * C)


def generate_frames():

    global current_status
    global current_ear
    global current_mar

    global eye_closed_start
    global mouth_open_start

    global eye_alert_triggered
    global yawn_alert_triggered

    cap = cv2.VideoCapture(0)

    while True:

        success, frame = cap.read()

        if not success:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = face_detector(gray)

        current_status = "Monitoring..."

        for face in faces:

            landmarks = dlib_facelandmark(gray, face)

            left_eye = []
            right_eye = []

            for n in range(42, 48):

                x = landmarks.part(n).x
                y = landmarks.part(n).y

                right_eye.append((x, y))

                next_point = 42 if n == 47 else n + 1

                cv2.line(
                    frame,
                    (x, y),
                    (landmarks.part(next_point).x,
                     landmarks.part(next_point).y),
                    (0, 255, 0),
                    1
                )

            for n in range(36, 42):

                x = landmarks.part(n).x
                y = landmarks.part(n).y

                left_eye.append((x, y))

                next_point = 36 if n == 41 else n + 1

                cv2.line(
                    frame,
                    (x, y),
                    (landmarks.part(next_point).x,
                     landmarks.part(next_point).y),
                    (0, 255, 0),
                    1
                )

            left_EAR = detect_eye(left_eye)
            right_EAR = detect_eye(right_eye)

            EAR = (left_EAR + right_EAR) / 2.0

            current_ear = round(EAR, 2)

            mouth = []

            for n in range(48, 68):

                x = landmarks.part(n).x
                y = landmarks.part(n).y

                mouth.append((x, y))

                next_point = 48 if n == 67 else n + 1

                cv2.line(
                    frame,
                    (x, y),
                    (landmarks.part(next_point).x,
                     landmarks.part(next_point).y),
                    (255, 255, 0),
                    1
                )

            MAR = detect_mouth(mouth)

            current_mar = round(MAR, 2)

            # ---- Eye / drowsiness check ----
            if EAR < EAR_THRESHOLD:

                if eye_closed_start is None:
                    eye_closed_start = time.time()

                elapsed_eye = time.time() - eye_closed_start

                if elapsed_eye >= EAR_ALERT_DELAY:

                    current_status = "Drowsiness Detected"

                    cv2.putText(
                        frame,
                        "DROWSINESS DETECTED",
                        (40, 80),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

                    cv2.putText(
                        frame,
                        "WAKE UP!",
                        (40, 130),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

                    if not eye_alert_triggered:

                        speak("Wake up buddy")

                        eye_alert_triggered = True

            else:
                # eyes reopened -> reset so the alert can fire again next time
                eye_closed_start = None
                eye_alert_triggered = False

            # ---- Mouth / yawn check ----
            if MAR > MAR_THRESHOLD:

                if mouth_open_start is None:
                    mouth_open_start = time.time()

                elapsed_mouth = time.time() - mouth_open_start

                if elapsed_mouth >= MAR_ALERT_DELAY:

                    current_status = "Yawning"

                    cv2.putText(
                        frame,
                        "YAWN DETECTED",
                        (40, 190),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

                    cv2.putText(
                        frame,
                        "TAKE A BREAK!",
                        (40, 240),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        3
                    )

                    if not yawn_alert_triggered:

                        speak("Please take a break")

                        yawn_alert_triggered = True

            else:

                mouth_open_start = None
                yawn_alert_triggered = False

            cv2.putText(
                frame,
                f"EAR : {current_ear:.2f}",
                (450, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"MAR : {current_mar:.2f}",
                (450, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Status : {current_status}",
                (20, 460),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 255),
                2
            )

        # moved outside the face loop so it always runs, even with 0 faces
        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )

    cap.release()


def get_status():

    return {
        "status": current_status,
        "ear": current_ear,
        "mar": current_mar
    }
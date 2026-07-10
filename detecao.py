from scipy.spatial import distance as dist
from imutils import face_utils
from threading import Thread
import time
import dlib
import cv2
import os
import subprocess
import sys


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

VIDEO_PATH = os.path.join(BASE_DIR, "video/sonolencia.mov")
PREDITOR_PATH = os.path.join(BASE_DIR, "shape_predictor_68_face_landmarks.dat")

LIMIAR_EAR = 0.25
TEMPO_PARA_ALERTA = 1.5

tempo_olhos_fechados = None
alarme_on = False


def tocar_alarme():
    try:
        subprocess.run(
            ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        print("\a", end="", flush=True)


def calcular_ear(olho):
    A = dist.euclidean(olho[1], olho[5])
    B = dist.euclidean(olho[2], olho[4])
    C = dist.euclidean(olho[0], olho[3])
    return (A + B) / (2.0 * C)


if not os.path.exists(VIDEO_PATH):
    print("erro video não encontrado.")
    sys.exit(1)

if not os.path.exists(PREDITOR_PATH):
    print("erro arquivo shape_predictor_68_face_landmarks.dat não encontrado.")
    sys.exit(1)


detector = dlib.get_frontal_face_detector()
preditor = dlib.shape_predictor(PREDITOR_PATH)

(inicio_esq, fim_esq) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(inicio_dir, fim_dir) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

video = cv2.VideoCapture(VIDEO_PATH)

while True:
    ret, frame = video.read()

    if not ret:
        break

    frame = cv2.resize(frame, (700, int(frame.shape[0] * 700 / frame.shape[1])))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rostos = detector(gray, 0)

    for rosto in rostos:
        pontos = preditor(gray, rosto)
        pontos = face_utils.shape_to_np(pontos)

        olho_esq = pontos[inicio_esq:fim_esq]
        olho_dir = pontos[inicio_dir:fim_dir]

        ear_esq = calcular_ear(olho_esq)
        ear_dir = calcular_ear(olho_dir)
        ear = (ear_esq + ear_dir) / 2.0

        cv2.drawContours(frame, [cv2.convexHull(olho_esq)], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [cv2.convexHull(olho_dir)], -1, (0, 255, 0), 1)

        if ear < LIMIAR_EAR:
            if tempo_olhos_fechados is None:
                tempo_olhos_fechados = time.time()

            tempo_fechado = time.time() - tempo_olhos_fechados

            cv2.putText(frame, "Tempo: {:.1f}s".format(tempo_fechado), (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if tempo_fechado >= TEMPO_PARA_ALERTA:
                if not alarme_on:
                    alarme_on = True
                    Thread(target=tocar_alarme, daemon=True).start()

                cv2.putText(frame, "SONOLENCIA!", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        else:
            tempo_olhos_fechados = None
            alarme_on = False

        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow("Detector de Sonolencia", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


video.release()
cv2.destroyAllWindows()
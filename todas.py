from scipy.spatial import distance as dist
from imutils import face_utils
from threading import Thread
from collections import deque
import time
import dlib
import cv2
import os
import ctypes
import ctypes.util
import platform
import subprocess
import sys
import statistics


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PREDITOR_PATH = os.path.join(BASE_DIR, "shape_predictor_68_face_landmarks.dat")

CAMERA_INDEX = int(sys.argv[1]) if len(sys.argv) > 1 else None
MAX_CAMERAS_PROCURA = 5

TECNICAS = ["ear", "mar"]

FRAMES_CALIBRACAO = 30
JANELA_SUAVIZACAO = 5


RATIO_EAR = 0.80
RATIO_MAR = 2.4

INTERVALO_REDETECCAO_COMPLETA = 20
MARGEM_ROI_ROSTO = 0.25

SUAVIZACAO_QUADRADO = 0.3

COR_TEXTO = (0, 0, 255)

TEXTO_ALERTA = "SONOLENCIA"
ESCALA_ALERTA = 1.6
ESPESSURA_ALERTA = 4

NOME_JANELA = "Detector de Sonolencia"

POSICOES_TIMER = {
    "ear": (10, 60),
    "mar": (10, 85),
}

CONFIG_TECNICAS = {
    "ear": {"limiar": None, "tempo": 1.0},
    "mar": {"limiar": None, "tempo": 1.2},
}

estado = {
    tecnica: {
        "tempo_evento": None,
        "alarme_on": False,
    }
    for tecnica in TECNICAS
}

ear_calibracao = []
ear_base = None

mar_calibracao = []
mar_base = None

ultima_regiao_rosto = None
frames_desde_deteccao_completa = 0

quadrado_suave = None

buffer_ear = deque(maxlen=JANELA_SUAVIZACAO)
buffer_mar = deque(maxlen=JANELA_SUAVIZACAO)


def tocar_alarme():
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Sosumi.aiff"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif sistema == "Windows":
            import winsound
            winsound.Beep(1000, 500)
        else:
            print("\a", end="", flush=True)
    except Exception:
        print("\a", end="", flush=True)


def abrir_camera(indice=None):
    indices = [indice] if indice is not None else range(MAX_CAMERAS_PROCURA)

    for i in indices:
        camera = cv2.VideoCapture(i)
        if camera.isOpened():
            ret, _ = camera.read()
            if ret:
                print("Usando a camera de indice {}".format(i))
                return camera
        camera.release()

    return None


def calcular_ear(olho):
    A = dist.euclidean(olho[1], olho[5])
    B = dist.euclidean(olho[2], olho[4])
    C = dist.euclidean(olho[0], olho[3])
    return (A + B) / (2.0 * C)


def calcular_mar(boca):
    A = dist.euclidean(boca[2], boca[10])
    B = dist.euclidean(boca[4], boca[8])
    C = dist.euclidean(boca[0], boca[6])
    return (A + B) / (2.0 * C)


def obter_tamanho_tela():
    sistema = platform.system()
    try:
        if sistema == "Darwin":
            class CGRect(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double),
                            ("largura", ctypes.c_double), ("altura", ctypes.c_double)]

            cg = ctypes.CDLL(ctypes.util.find_library("CoreGraphics"))
            cg.CGMainDisplayID.restype = ctypes.c_uint32
            cg.CGDisplayBounds.restype = CGRect
            cg.CGDisplayBounds.argtypes = [ctypes.c_uint32]
            tela = cg.CGDisplayBounds(cg.CGMainDisplayID())
            return int(tela.largura), int(tela.altura)
        elif sistema == "Windows":
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        else:
            saida = subprocess.run(["xrandr"], capture_output=True, text=True).stdout
            atual = saida.split("current")[1].split(",")[0]
            largura, altura = atual.split("x")
            return int(largura), int(altura)
    except Exception:
        return 1280, 720


def calcular_tamanho_exibicao(largura_frame, altura_frame):
    largura_tela, altura_tela = obter_tamanho_tela()
    escala = min((largura_tela - 20) / largura_frame, (altura_tela - 100) / altura_frame)
    largura_janela = int(largura_frame * escala)
    altura_janela = int(altura_frame * escala)
    posicao = ((largura_tela - largura_janela) // 2, 25)
    return (largura_janela, altura_janela), posicao


def desenhar_alerta(frame, x1, x2, y2):
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    (largura_texto, altura_texto), _ = cv2.getTextSize(TEXTO_ALERTA, fonte, ESCALA_ALERTA, ESPESSURA_ALERTA)
    altura_frame, largura_frame = frame.shape[:2]

    x = (x1 + x2) // 2 - largura_texto // 2
    x = max(5, min(x, largura_frame - largura_texto - 5))
    y = y2 + altura_texto + 40
    y = min(y, altura_frame - 10)

    cv2.putText(frame, TEXTO_ALERTA, (x, y), fonte, ESCALA_ALERTA, COR_TEXTO, ESPESSURA_ALERTA)

    (largura_antes, _), _ = cv2.getTextSize("SONOL", fonte, ESCALA_ALERTA, ESPESSURA_ALERTA)
    (largura_e, _), _ = cv2.getTextSize("E", fonte, ESCALA_ALERTA, ESPESSURA_ALERTA)
    base_acento = y - altura_texto - 6
    topo_acento = base_acento - int(altura_texto * 0.35)
    esquerda = x + largura_antes + int(largura_e * 0.2)
    meio = x + largura_antes + largura_e // 2
    direita = x + largura_antes + int(largura_e * 0.8)
    cv2.line(frame, (esquerda, base_acento), (meio, topo_acento), COR_TEXTO, ESPESSURA_ALERTA - 1)
    cv2.line(frame, (meio, topo_acento), (direita, base_acento), COR_TEXTO, ESPESSURA_ALERTA - 1)


def detectar_rostos(gray, detector):
    global ultima_regiao_rosto, frames_desde_deteccao_completa

    forcar_frame_completo = (
        ultima_regiao_rosto is None
        or frames_desde_deteccao_completa >= INTERVALO_REDETECCAO_COMPLETA
    )

    if not forcar_frame_completo:
        x0, y0, w0, h0 = ultima_regiao_rosto
        margem_x = int(w0 * MARGEM_ROI_ROSTO)
        margem_y = int(h0 * MARGEM_ROI_ROSTO)
        rx0 = max(0, x0 - margem_x)
        ry0 = max(0, y0 - margem_y)
        rx1 = min(gray.shape[1], x0 + w0 + margem_x)
        ry1 = min(gray.shape[0], y0 + h0 + margem_y)

        if rx1 > rx0 and ry1 > ry0:
            recorte = gray[ry0:ry1, rx0:rx1]
            rostos_roi = detector(recorte, 0)

            if len(rostos_roi) > 0:
                frames_desde_deteccao_completa += 1
                rostos_transladados = [
                    dlib.rectangle(r.left() + rx0, r.top() + ry0, r.right() + rx0, r.bottom() + ry0)
                    for r in rostos_roi
                ]
                primeiro = rostos_transladados[0]
                ultima_regiao_rosto = (primeiro.left(), primeiro.top(), primeiro.width(), primeiro.height())
                return rostos_transladados

    rostos = detector(gray, 0)
    frames_desde_deteccao_completa = 0

    if len(rostos) > 0:
        primeiro = rostos[0]
        ultima_regiao_rosto = (primeiro.left(), primeiro.top(), primeiro.width(), primeiro.height())
    else:
        ultima_regiao_rosto = None

    return rostos


if not os.path.exists(PREDITOR_PATH):
    print("erro arquivo shape_predictor_68_face_landmarks.dat não encontrado.")
    sys.exit(1)


detector = dlib.get_frontal_face_detector()
preditor = dlib.shape_predictor(PREDITOR_PATH)

(inicio_esq, fim_esq) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
(inicio_dir, fim_dir) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]
(inicio_boca, fim_boca) = face_utils.FACIAL_LANDMARKS_IDXS["mouth"]

camera = abrir_camera(CAMERA_INDEX)

if camera is None:
    print("erro nenhuma camera encontrada.")
    sys.exit(1)

cv2.namedWindow(NOME_JANELA, cv2.WINDOW_NORMAL)

tamanho_exibicao = None

while True:
    ret, frame = camera.read()

    if not ret:
        print("erro falha ao ler a imagem da camera.")
        break

    tocar_som = False

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (700, int(frame.shape[0] * 700 / frame.shape[1])))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    rostos = detectar_rostos(gray, detector)

    if len(rostos) == 0:
        quadrado_suave = None

        for tecnica in TECNICAS:
            st = estado[tecnica]
            st["tempo_evento"] = None
            st["alarme_on"] = False

    for rosto in rostos:
        pontos = preditor(gray, rosto)
        pontos = face_utils.shape_to_np(pontos)

        olho_esq = pontos[inicio_esq:fim_esq]
        olho_dir = pontos[inicio_dir:fim_dir]
        boca = pontos[inicio_boca:fim_boca]

        ear_esq = calcular_ear(olho_esq)
        ear_dir = calcular_ear(olho_dir)
        ear = (ear_esq + ear_dir) / 2.0
        mar = calcular_mar(boca)

        quadrado_atual = (rosto.left(), rosto.top(), rosto.right(), rosto.bottom())
        if quadrado_suave is None:
            quadrado_suave = quadrado_atual
        else:
            quadrado_suave = tuple(
                anterior + SUAVIZACAO_QUADRADO * (atual - anterior)
                for anterior, atual in zip(quadrado_suave, quadrado_atual)
            )
        x1, y1, x2, y2 = (int(round(v)) for v in quadrado_suave)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        cv2.drawContours(frame, [cv2.convexHull(olho_esq)], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [cv2.convexHull(olho_dir)], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [cv2.convexHull(boca)], -1, (255, 255, 0), 1)

        buffer_ear.append(ear)
        ear_suave = sum(buffer_ear) / len(buffer_ear)

        buffer_mar.append(mar)
        mar_suave = sum(buffer_mar) / len(buffer_mar)

        if ear_base is None:
            ear_calibracao.append(ear)
            mar_calibracao.append(mar)
            cv2.putText(frame, "Calibrando... {}/{}".format(
                len(ear_calibracao), FRAMES_CALIBRACAO), (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, COR_TEXTO, 2)
            if len(ear_calibracao) >= FRAMES_CALIBRACAO:
                ear_base = statistics.median(ear_calibracao)
                mar_base = statistics.median(mar_calibracao)
                CONFIG_TECNICAS["ear"]["limiar"] = ear_base * RATIO_EAR
                CONFIG_TECNICAS["mar"]["limiar"] = mar_base * RATIO_MAR
                print("Calibracao concluida - EAR base: {:.3f} (limiar {:.3f}) | "
                      "MAR base: {:.3f} (limiar {:.3f})".format(
                          ear_base, CONFIG_TECNICAS["ear"]["limiar"],
                          mar_base, CONFIG_TECNICAS["mar"]["limiar"]))

        valores_suavizados = {
            "ear": ear_suave,
            "mar": mar_suave,
        }

        tecnicas_em_alerta = []

        for tecnica in TECNICAS:
            st = estado[tecnica]
            limiar = CONFIG_TECNICAS[tecnica]["limiar"]
            valor_suavizado = valores_suavizados[tecnica]

            if limiar is None:
                condicao = False
            elif tecnica == "ear":
                condicao = valor_suavizado < limiar
            else:
                condicao = valor_suavizado > limiar

            if condicao:
                if st["tempo_evento"] is None:
                    st["tempo_evento"] = time.time()

                tempo_decorrido = time.time() - st["tempo_evento"]

                cv2.putText(frame, "{}: {:.1f}/{:.1f}s".format(
                    tecnica.upper(), tempo_decorrido, CONFIG_TECNICAS[tecnica]["tempo"]),
                    POSICOES_TIMER[tecnica], cv2.FONT_HERSHEY_SIMPLEX, 0.55, COR_TEXTO, 2)

                if tempo_decorrido >= CONFIG_TECNICAS[tecnica]["tempo"]:
                    if not st["alarme_on"]:
                        st["alarme_on"] = True
                        tocar_som = True
                    tecnicas_em_alerta.append(tecnica.upper())
            else:
                st["tempo_evento"] = None
                st["alarme_on"] = False

        if tecnicas_em_alerta:
            desenhar_alerta(frame, x1, x2, y2)

        cv2.putText(frame, "EAR: {:.2f}".format(ear), (300, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COR_TEXTO, 2)
        cv2.putText(frame, "MAR: {:.2f}".format(mar), (300, 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, COR_TEXTO, 2)

    if tocar_som:
        Thread(target=tocar_alarme, daemon=True).start()

    if tamanho_exibicao is None:
        tamanho_exibicao, posicao_janela = calcular_tamanho_exibicao(frame.shape[1], frame.shape[0])
        cv2.imshow(NOME_JANELA, cv2.resize(frame, tamanho_exibicao))
        cv2.moveWindow(NOME_JANELA, *posicao_janela)

    cv2.imshow(NOME_JANELA, cv2.resize(frame, tamanho_exibicao))

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


camera.release()
cv2.destroyAllWindows()

"""
ImgFootball — Body Tracker + OSC Sender
========================================
Script principal de captura de corpo com envio OSC.
Configurações em config.ini
"""

import cv2
import mediapipe as mp
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import math
from pythonosc import udp_client
import configparser
import time
import json
import os
from datetime import datetime

# ============================================================
# Carrega configurações do config.ini
# ============================================================
config = configparser.ConfigParser()
config.read("config.ini")

CAM_INDEX = config.getint("camera", "index", fallback=1)
CAM_WIDTH = config.getint("camera", "width", fallback=1280)
CAM_HEIGHT = config.getint("camera", "height", fallback=720)
USE_DSHOW = config.getboolean("camera", "use_dshow", fallback=True)

OSC_IP = config.get("osc", "ip", fallback="127.0.0.1")
OSC_PORT = config.getint("osc", "port", fallback=9000)

POSE_DET_CONF = config.getfloat("detection", "pose_detection_confidence", fallback=0.5)
POSE_TRACK_CONF = config.getfloat("detection", "pose_tracking_confidence", fallback=0.5)
POSE_COMPLEXITY = config.getint("detection", "pose_model_complexity", fallback=2)
HAND_DET_CONF = config.getfloat("detection", "hand_detection_confidence", fallback=0.6)
KICK_THRESHOLD = config.getfloat("detection", "kick_speed_threshold", fallback=15)

SMOOTH_ENABLED = config.getboolean("smoothing", "enabled", fallback=True)
SMOOTH_FACTOR = config.getfloat("smoothing", "factor", fallback=0.4)

SAVE_TO_FILE = config.getboolean("logging", "save_to_file", fallback=False)
LOG_FOLDER = config.get("logging", "output_folder", fallback="logs")
LOG_INTERVAL = config.getint("logging", "terminal_log_interval", fallback=30)

# ============================================================
# Inicialização
# ============================================================
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    min_detection_confidence=POSE_DET_CONF,
    min_tracking_confidence=POSE_TRACK_CONF,
    model_complexity=POSE_COMPLEXITY
)

# flipType=True inverte a lógica da mão, corrigindo o espelhamento
hand_detector = HandDetector(detectionCon=HAND_DET_CONF, maxHands=2)

osc_client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)

if USE_DSHOW:
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(CAM_INDEX)
cap.set(3, CAM_WIDTH)
cap.set(4, CAM_HEIGHT)

# ============================================================
# Cores
# ============================================================
COR_DIREITO = (0, 0, 255)
COR_ESQUERDO = (255, 100, 0)
COR_DIREITO_CLARO = (100, 100, 255)
COR_ESQUERDO_CLARO = (255, 180, 100)
COR_TRONCO = (180, 180, 180)
COR_ZONA_SAPATO_D = (0, 80, 200)
COR_ZONA_SAPATO_E = (200, 80, 0)

RAIO_TRONCO = 4
RAIO_PERNA = 6
RAIO_PE = 8

# ============================================================
# CORREÇÃO DE LADOS (EFEITO ESPELHO)
# Como usamos cv2.flip, o lado DIREITO físico do usuário aparece
# no lado DIREITO da tela. Porém, o MediaPipe acha que é o ombro
# ESQUERDO de alguém de frente para a câmera. 
# Por isso, mapeamos "direito" -> LEFT e "esquerdo" -> RIGHT.
# ============================================================
OSC_LANDMARKS = {
    "/body/direito/ombro":       mp_pose.PoseLandmark.LEFT_SHOULDER,
    "/body/esquerdo/ombro":      mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "/body/direito/cotovelo":    mp_pose.PoseLandmark.LEFT_ELBOW,
    "/body/esquerdo/cotovelo":   mp_pose.PoseLandmark.RIGHT_ELBOW,
    "/body/direito/pulso":       mp_pose.PoseLandmark.LEFT_WRIST,
    "/body/esquerdo/pulso":      mp_pose.PoseLandmark.RIGHT_WRIST,
    "/body/direito/quadril":     mp_pose.PoseLandmark.LEFT_HIP,
    "/body/esquerdo/quadril":    mp_pose.PoseLandmark.RIGHT_HIP,
    "/body/direito/joelho":      mp_pose.PoseLandmark.LEFT_KNEE,
    "/body/esquerdo/joelho":     mp_pose.PoseLandmark.RIGHT_KNEE,
    "/body/direito/tornozelo":   mp_pose.PoseLandmark.LEFT_ANKLE,
    "/body/esquerdo/tornozelo":  mp_pose.PoseLandmark.RIGHT_ANKLE,
    "/body/direito/calcanhar":   mp_pose.PoseLandmark.LEFT_HEEL,
    "/body/esquerdo/calcanhar":  mp_pose.PoseLandmark.RIGHT_HEEL,
    "/body/direito/pe":          mp_pose.PoseLandmark.LEFT_FOOT_INDEX,
    "/body/esquerdo/pe":         mp_pose.PoseLandmark.RIGHT_FOOT_INDEX,
}

UPPER_BODY = {
    "Ombro D": mp_pose.PoseLandmark.LEFT_SHOULDER,
    "Ombro E": mp_pose.PoseLandmark.RIGHT_SHOULDER,
    "Cotovelo D": mp_pose.PoseLandmark.LEFT_ELBOW,
    "Cotovelo E": mp_pose.PoseLandmark.RIGHT_ELBOW,
    "Pulso D": mp_pose.PoseLandmark.LEFT_WRIST,
    "Pulso E": mp_pose.PoseLandmark.RIGHT_WRIST,
}

LOWER_BODY = {
    "Quadril D": mp_pose.PoseLandmark.LEFT_HIP,
    "Quadril E": mp_pose.PoseLandmark.RIGHT_HIP,
    "Joelho D": mp_pose.PoseLandmark.LEFT_KNEE,
    "Joelho E": mp_pose.PoseLandmark.RIGHT_KNEE,
    "Tornozelo D": mp_pose.PoseLandmark.LEFT_ANKLE,
    "Tornozelo E": mp_pose.PoseLandmark.RIGHT_ANKLE,
    "Calcanhar D": mp_pose.PoseLandmark.LEFT_HEEL,
    "Calcanhar E": mp_pose.PoseLandmark.RIGHT_HEEL,
    "Ponta Pe D": mp_pose.PoseLandmark.LEFT_FOOT_INDEX,
    "Ponta Pe E": mp_pose.PoseLandmark.RIGHT_FOOT_INDEX,
}

CONNECTIONS = [
    ("tronco", mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.RIGHT_SHOULDER),
    ("tronco", mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_HIP),
    ("tronco", mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_HIP),
    ("tronco", mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.RIGHT_HIP),
    
    ("D", mp_pose.PoseLandmark.LEFT_SHOULDER, mp_pose.PoseLandmark.LEFT_ELBOW),
    ("D", mp_pose.PoseLandmark.LEFT_ELBOW, mp_pose.PoseLandmark.LEFT_WRIST),
    ("E", mp_pose.PoseLandmark.RIGHT_SHOULDER, mp_pose.PoseLandmark.RIGHT_ELBOW),
    ("E", mp_pose.PoseLandmark.RIGHT_ELBOW, mp_pose.PoseLandmark.RIGHT_WRIST),
    
    ("D", mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE),
    ("D", mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE),
    ("D", mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_HEEL),
    ("D", mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_FOOT_INDEX),
    ("D", mp_pose.PoseLandmark.LEFT_HEEL, mp_pose.PoseLandmark.LEFT_FOOT_INDEX),
    
    ("E", mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE),
    ("E", mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE),
    ("E", mp_pose.PoseLandmark.RIGHT_ANKLE, mp_pose.PoseLandmark.RIGHT_HEEL),
    ("E", mp_pose.PoseLandmark.RIGHT_ANKLE, mp_pose.PoseLandmark.RIGHT_FOOT_INDEX),
    ("E", mp_pose.PoseLandmark.RIGHT_HEEL, mp_pose.PoseLandmark.RIGHT_FOOT_INDEX),
]

class Smoother:
    def __init__(self, factor=0.4):
        self.factor = factor
        self.prev = {}

    def smooth(self, key, value):
        if not SMOOTH_ENABLED:
            return value
        if key not in self.prev:
            self.prev[key] = value
            return value
        if isinstance(value, (list, tuple)):
            smoothed = []
            for i, v in enumerate(value):
                prev_v = self.prev[key][i] if i < len(self.prev[key]) else v
                smoothed.append(round(prev_v * self.factor + v * (1 - self.factor), 4))
            self.prev[key] = smoothed
            return smoothed
        else:
            smoothed = round(self.prev[key] * self.factor + value * (1 - self.factor), 4)
            self.prev[key] = smoothed
            return smoothed

smoother = Smoother(SMOOTH_FACTOR)

def calcular_angulo(a, b, c):
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

def get_point(landmarks, landmark_id, w, h):
    lm = landmarks.landmark[landmark_id]
    return int(lm.x * w), int(lm.y * h), lm.visibility

def get_normalized(landmarks, landmark_id):
    lm = landmarks.landmark[landmark_id]
    return round(lm.x, 4), round(lm.y, 4), round(lm.visibility, 4)

def cor_lado(nome):
    if " D" in nome:
        return COR_DIREITO
    elif " E" in nome:
        return COR_ESQUERDO
    return COR_TRONCO

confirmed_side = None
prev_foot_pos = {"E": None, "D": None}
frame_count = 0
fps_start_time = time.time()
fps = 0

print("\nImgFootball — Body Tracker + OSC")
print("VERMELHO = DIREITO | AZUL = ESQUERDO")

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.flip(img, 1)
    h, w, _ = img.shape
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    frame_count += 1

    if frame_count % 10 == 0:
        elapsed = time.time() - fps_start_time
        fps = 10 / max(elapsed, 0.001)
        fps_start_time = time.time()

    # Mãos (flipType=True já corrige o espelho no cvzone)
    hands, img = hand_detector.findHands(img, draw=False, flipType=True)

    if hands:
        for hand in hands:
            hand_type = hand["type"]
            hx, hy = hand["center"]

            cor_mao = COR_DIREITO if hand_type == "Right" else COR_ESQUERDO
            label_mao = "D" if hand_type == "Right" else "E"
            cv2.circle(img, (hx, hy), 5, cor_mao, -1)
            cv2.putText(img, f"Mao {label_mao}", (hx + 10, hy - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, cor_mao, 1)

            osc_addr = "/body/direito/mao" if hand_type == "Right" else "/body/esquerdo/mao"
            hand_coords = smoother.smooth(osc_addr, [round(hx / w, 4), round(hy / h, 4)])
            osc_client.send_message(osc_addr, hand_coords)

            if hand_type == "Right" and hx > w // 2:
                confirmed_side = "normal"
            elif hand_type == "Right" and hx < w // 2:
                confirmed_side = "invertido"

    results = pose.process(img_rgb)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks

        for osc_addr, landmark_id in OSC_LANDMARKS.items():
            nx, ny, nv = get_normalized(landmarks, landmark_id)
            smoothed = smoother.smooth(osc_addr, [nx, ny, nv])
            osc_client.send_message(osc_addr, smoothed)

        for side, hip_id, knee_id, ankle_id in [
            ("direito", mp_pose.PoseLandmark.LEFT_HIP, mp_pose.PoseLandmark.LEFT_KNEE, mp_pose.PoseLandmark.LEFT_ANKLE),
            ("esquerdo", mp_pose.PoseLandmark.RIGHT_HIP, mp_pose.PoseLandmark.RIGHT_KNEE, mp_pose.PoseLandmark.RIGHT_ANKLE),
        ]:
            hip = get_point(landmarks, hip_id, w, h)
            knee = get_point(landmarks, knee_id, w, h)
            ankle = get_point(landmarks, ankle_id, w, h)
            if hip[2] > 0.3 and knee[2] > 0.3 and ankle[2] > 0.3:
                ang = calcular_angulo(hip[:2], knee[:2], ankle[:2])
                ang_smooth = smoother.smooth(f"/body/{side}/joelho_angulo", ang)
                osc_client.send_message(f"/body/{side}/joelho_angulo", [round(ang_smooth, 2)])

        for side, side_key, ankle_id, heel_id, toe_id in [
            ("direito", "D", mp_pose.PoseLandmark.LEFT_ANKLE, mp_pose.PoseLandmark.LEFT_HEEL, mp_pose.PoseLandmark.LEFT_FOOT_INDEX),
            ("esquerdo", "E", mp_pose.PoseLandmark.RIGHT_ANKLE, mp_pose.PoseLandmark.RIGHT_HEEL, mp_pose.PoseLandmark.RIGHT_FOOT_INDEX),
        ]:
            ax, ay, av = get_point(landmarks, ankle_id, w, h)
            hx_f, hy_f, hv = get_point(landmarks, heel_id, w, h)
            tx, ty, tv = get_point(landmarks, toe_id, w, h)
            if av > 0.3 and hv > 0.3 and tv > 0.3:
                foot_cx = (ax + hx_f + tx) // 3
                foot_cy = (ay + hy_f + ty) // 3

                speed = 0.0
                if prev_foot_pos[side_key] is not None:
                    speed = math.dist((foot_cx, foot_cy), prev_foot_pos[side_key])
                prev_foot_pos[side_key] = (foot_cx, foot_cy)
                
                # DEBUG DA VELOCIDADE DO PÉ
                cv2.putText(img, f"Vel: {int(speed)}", (foot_cx + 40, foot_cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                osc_client.send_message(f"/body/{side}/pe_velocidade", [round(speed, 2)])
                shoe_coords = smoother.smooth(f"/body/{side}/sapato_centro", [round(foot_cx / w, 4), round(foot_cy / h, 4)])
                osc_client.send_message(f"/body/{side}/sapato_centro", shoe_coords)

                is_kick = 1 if speed > KICK_THRESHOLD else 0
                osc_client.send_message(f"/body/{side}/chute", [is_kick])
                if is_kick == 1:
                    cor_mov = COR_DIREITO if side_key == "D" else COR_ESQUERDO
                    cv2.putText(img, "CHUTE!", (foot_cx - 30, foot_cy + 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, cor_mov, 2)

        side_status = 1 if confirmed_side == "normal" else (0 if confirmed_side == "invertido" else -1)
        osc_client.send_message("/body/lado_confirmado", [side_status])

        # DESENHO (Conexões)
        for side, p1_id, p2_id in CONNECTIONS:
            p1x, p1y, p1v = get_point(landmarks, p1_id, w, h)
            p2x, p2y, p2v = get_point(landmarks, p2_id, w, h)
            if p1v > 0.3 and p2v > 0.3:
                if side == "D":
                    cor = COR_DIREITO_CLARO
                    thickness = 2
                elif side == "E":
                    cor = COR_ESQUERDO_CLARO
                    thickness = 2
                else:
                    cor = COR_TRONCO
                    thickness = 1
                cv2.line(img, (p1x, p1y), (p2x, p2y), cor, thickness)

        # DESENHO (Pontos)
        for nome, landmark_id in {**UPPER_BODY, **LOWER_BODY}.items():
            x, y, vis = get_point(landmarks, landmark_id, w, h)
            if vis > 0.3:
                is_foot = "Pe" in nome or "Calcanhar" in nome or "Tornozelo" in nome
                cor = cor_lado(nome)
                raio = RAIO_PE if is_foot else RAIO_PERNA
                cv2.circle(img, (x, y), raio, cor, -1)
                cv2.circle(img, (x, y), raio + 1, (255, 255, 255), 1)
                if "Joelho" in nome or "Tornozelo" in nome:
                    cv2.putText(img, nome, (x + raio + 4, y + 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.35, cor, 1)

    # Painel de infos
    overlay = img.copy()
    cv2.rectangle(overlay, (10, 10), (330, 145), (0, 0, 0), -1)
    img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
    cv2.putText(img, f"ImgFootball | FPS: {fps:.0f}", (20, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 220, 120), 2)
    cv2.circle(img, (30, 55), 5, COR_DIREITO, -1)
    cv2.putText(img, "= DIREITO (Vermelho)", (42, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COR_DIREITO, 1)
    cv2.circle(img, (30, 78), 5, COR_ESQUERDO, -1)
    cv2.putText(img, "= ESQUERDO (Azul)", (42, 83), cv2.FONT_HERSHEY_SIMPLEX, 0.4, COR_ESQUERDO, 1)
    cv2.putText(img, f"OSC -> {OSC_IP}:{OSC_PORT}", (20, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)

    status = "Lados OK (corrigidos)" if confirmed_side == "normal" else ("Levante a mao direita p/ confirmar" if confirmed_side is None else "Lados Invertidos!")
    cor_status = (0, 255, 0) if confirmed_side == "normal" else ((0, 200, 255) if confirmed_side is None else (0, 0, 255))
    cv2.putText(img, status, (20, 137), cv2.FONT_HERSHEY_SIMPLEX, 0.35, cor_status, 1)

    cv2.imshow("ImgFootball - Body Tracker + OSC", img)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

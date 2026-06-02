import cv2
from cvzone.HandTrackingModule import HandDetector

# Inicia a câmera (tente mudar o 0 para 1 se não abrir a câmera certa)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
cap.set(3, 1280) # Largura
cap.set(4, 720)  # Altura

# Inicializa o detector de mãos (maxHands=2 para duas mãos)
detector = HandDetector(detectionCon=0.8, maxHands=2)

print("Pressione 'q' para fechar a janela de teste.")

while True:
    success, img = cap.read()
    if not success:
        print("Erro: Não foi possível acessar a câmera.")
        break

    # Inverte a imagem como um espelho
    img = cv2.flip(img, 1)

    # Encontra as mãos e já desenha os pontos e a caixa delimitadora na imagem
    hands, img = detector.findHands(img, draw=True, flipType=False)

    # Se quiser imprimir no terminal qual mão foi detectada e a posição:
    if hands:
        for hand in hands:
            handType = hand["type"] # "Left" ou "Right"
            center = hand["center"] # Centro da mão (cx, cy)
            print(f"Mão detectada: {handType} | Centro: {center}")

    # Mostra a imagem na tela
    cv2.imshow("Teste de Mapeamento das Maos", img)

    # Espera a tecla 'q' ser pressionada para sair
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

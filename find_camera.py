import cv2

print("Buscando câmeras conectadas...")

for i in range(5):
    # Tenta abrir sem forçar DSHOW nem resolução, para evitar tela preta
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        success, img = cap.read()
        if success and img is not None:
            # Verifica se a imagem não é 100% preta
            if img.max() > 0:
                print(f"[SUCESSO] Câmera encontrada no índice: {i}")
                cv2.putText(img, f"Camera Index: {i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow(f"Camera {i}", img)
            else:
                print(f"[AVISO] Índice {i} abriu, mas a tela está preta (provavelmente câmera virtual ou tampada).")
        else:
            print(f"[ERRO] Índice {i} abriu, mas falhou ao ler a imagem.")
        cap.release()
    else:
        print(f"[FALHA] Nenhuma câmera no índice {i}.")

print("\nPressione qualquer tecla em cima da janela da imagem para fechar.")
cv2.waitKey(0)
cv2.destroyAllWindows()

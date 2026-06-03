import cv2
import cvzone
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import mediapipe as mp

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(3, 1280)
cap.set(4, 720)

#Importing images
imgBackground = cv2.imread("Background.png")
if imgBackground is None:
    print("Error: Background image not found.")

imgGameOver = cv2.imread("gameOver.png")
if imgGameOver is None:
    print("Error: Game over image not found.")

imgBall = cv2.imread("Ball.png", cv2.IMREAD_UNCHANGED)
if imgBall is None:
    print("Error: Ball image not found.")

imgBat1 = cv2.imread("bat1.png", cv2.IMREAD_UNCHANGED)
if imgBat1 is None:
    print("Error: Bat1 image not found.")

imgBat2 = cv2.imread("bat2.png", cv2.IMREAD_UNCHANGED)
if imgBat2 is None:
    print("Error: Bat2 image not found.")

#Hand Detector with accuracy
detector = HandDetector(detectionCon=0.8, maxHands=2)




#Vars
ballPos = [100, 100]
speedX = 15
speedY = 15
gameOver = False
score = [0, 0]

while True:
    _, img = cap.read()
    if not _:
        print("Error: Unable to capture video.")
        break

    img = cv2.flip(img, 1)
    imgRaw = img.copy()

    #Finds the hand and its landmarks area
    hands, img = detector.findHands(img, flipType=False)
    img = cv2.addWeighted(img, 0.2, imgBackground, 0.8, 0)

    #Checks for hands
    if hands:
        for hand in hands:
            x, y, w, h = hand['bbox']
            h1, w1, _ = imgBat1.shape
            y1 = y - h1 // 2
            y1 = np.clip(y1, 20, 415)

            if hand['type'] == "Left":#Draws left bat
                img = cvzone.overlayPNG(img, imgBat1, (59, y1))
                #Check for impact with the left bat
                if 59 < ballPos[0] < 59 + w1 and y1 < ballPos[1] < y1 + h1:
                    speedX = -speedX
                    ballPos[0] += 30
                    score[0] += 1

            if hand['type'] == "Right":#Draws right bat
                img = cvzone.overlayPNG(img, imgBat2, (1195, y1))
                #Checks for impact with the right bat
                if 1195 - 50 < ballPos[0] < 1195 and y1 < ballPos[1] < y1 + h1:
                    speedX = -speedX
                    ballPos[0] -= 30
                    score[1] += 1

    #Game Over statement
    if ballPos[0] < 40 or ballPos[0] > 1200:
        gameOver = True

    if gameOver:
        img = imgGameOver
        #Determines winner and displays their score
        if score[0] > score[1]:
            winner_text = f"Player 1 Wins! Score: {score[0]}"
        elif score[1] > score[0]:
            winner_text = f"Player 2 Wins! Score: {score[1]}"
        else:
            winner_text = "It's a Tie!"

        #Displays the winner and their score on the game-over screen
        cv2.putText(img, winner_text, (500, 360), cv2.FONT_HERSHEY_COMPLEX, 1, (200, 0, 200), 2)

    else:  #Moves the ball if the game is not over
        if ballPos[1] >= 500 or ballPos[1] <= 10:
            speedY = -speedY

        ballPos[0] += speedX
        ballPos[1] += speedY

        #Draws the ball
        img = cvzone.overlayPNG(img, imgBall, ballPos)

        #Displays scores
        cv2.putText(img, str(score[0]), (300, 650), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 255, 255), 5)
        cv2.putText(img, str(score[1]), (900, 650), cv2.FONT_HERSHEY_COMPLEX, 3, (255, 255, 255), 5)

    img[580:700, 20:233] = cv2.resize(imgRaw, (213, 120))

    cv2.imshow("Image", img)
    key = cv2.waitKey(1)
    if key == ord('r'):
        ballPos = [100, 100]
        speedX = 15
        speedY = 15
        gameOver = False
        score = [0, 0]
        imgGameOver = cv2.imread("gameOver.png")
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

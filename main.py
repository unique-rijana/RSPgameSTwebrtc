import streamlit as st
import cv2
import cvzone
import random
import time
import av
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration
from cvzone.HandTrackingModule import HandDetector

# Load resources
bg_img = cv2.imread("Resources/BG.png")
ai_imgs = {
    1: cv2.imread("Resources/1.png", cv2.IMREAD_UNCHANGED),
    2: cv2.imread("Resources/2.png", cv2.IMREAD_UNCHANGED),
    3: cv2.imread("Resources/3.png", cv2.IMREAD_UNCHANGED),
}

class RockPaperScissorsProcessor(VideoProcessorBase):
    def __init__(self):
        self.detector = HandDetector(maxHands=1)
        self.score = [0, 0]
        self.timer = 0
        self.stateResult = False
        self.startTime = time.time()
        self.imgAI = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        imgBg = bg_img.copy()

        # Resize and crop player cam
        img = cv2.resize(img, (0, 0), fx=0.875, fy=0.875)
        img = img[:, 80:480]

        hands, img = self.detector.findHands(img, draw=False)

        imgBg[234:654, 794:1194] = img

        # Game timer
        timer = time.time() - self.startTime

        # Show countdown timer only before the move is decided
        if not self.stateResult:
            countdown = 3 - int(timer)
            if countdown >= 0:
                cv2.putText(imgBg, str(countdown), (605, 435), cv2.FONT_HERSHEY_PLAIN, 6, (255, 0, 255), 4)

        if not self.stateResult and timer > 3:
            self.stateResult = True
            self.startTime = time.time()

            playerMove = None
            if hands:
                fingers = self.detector.fingersUp(hands[0])
                if fingers == [0, 0, 0, 0, 0]:
                    playerMove = 1
                elif fingers == [1, 1, 1, 1, 1]:
                    playerMove = 2
                elif fingers == [0, 1, 1, 0, 0]:
                    playerMove = 3

            aiMove = random.randint(1, 3)
            self.imgAI = ai_imgs[aiMove]

            # Scoring
            if playerMove:
                if (playerMove == 1 and aiMove == 3) or \
                   (playerMove == 2 and aiMove == 1) or \
                   (playerMove == 3 and aiMove == 2):
                    self.score[1] += 1
                elif (aiMove == 1 and playerMove == 3) or \
                     (aiMove == 2 and playerMove == 1) or \
                     (aiMove == 3 and playerMove == 2):
                    self.score[0] += 1

        if self.stateResult and self.imgAI is not None:
            imgBg = cvzone.overlayPNG(imgBg, self.imgAI, (149, 310))

        # Scores
        cv2.putText(imgBg, str(self.score[0]), (410, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)
        cv2.putText(imgBg, str(self.score[1]), (1112, 215), cv2.FONT_HERSHEY_PLAIN, 4, (255, 255, 255), 6)

        # Reset timer after 2 seconds
        if self.stateResult and (time.time() - self.startTime) > 2:
            self.stateResult = False
            self.imgAI = None
            self.startTime = time.time()

        return av.VideoFrame.from_ndarray(imgBg, format="bgr24")


# 🔁 Auto-start game and camera
st.title("✋ Rock Paper Scissors - Auto Start Game")

webrtc_streamer(
    key="auto-rps",
    video_processor_factory=RockPaperScissorsProcessor,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    media_stream_constraints={"video": True, "audio": False},
)

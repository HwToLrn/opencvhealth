from typing import List

from django.shortcuts import render

from django.views.decorators import gzip
from django.http import StreamingHttpResponse
import cv2
import mediapipe as mp
import numpy as np
import threading
# Create your views here.

def home(request):
    return render(request, 'healthapp/home.html')

class VideoCamera(object):
    def __init__(self):
        self.cap = cv2.VideoCapture(0)

        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose = mp.solutions.pose

        # count variables
        self.left_counter: int = 0
        self.right_counter: int = 0
        self.counter: int = 0
        self.stage: str = ''  # down or up

        # 사용자가 미리 정해 놓은 루틴 / 한 운동의 반복횟수 / 한 운동의 세트횟수
        self.ROUTE: List[str] = ['아령들기', '스쿼트','팔굽혀펴기']
        self.REPEATS: int = 5
        self.SET: int = 2
        self.current_route: int = 0  # ROUTE[0] .. ROUTE[2] 순으로 사용
        self.current_set: int = 0

        # color
        self.WHITE_COLOR = (224, 224, 224)
        self.BLACK_COLOR = (0, 0, 0)
        self.RED_COLOR = (0, 0, 255)
        self.GREEN_COLOR = (0, 128, 0)
        self.BLUE_COLOR = (255, 0, 0)

    def __del__(self):
        self.cap.release()

    # coor == coordinates: 좌표
    def calculate_angle(self, coor_fst: List[float], coor_scd: List[float], coor_trd: List[float]) -> float:
        shoulder = np.array(coor_fst)
        elbow = np.array(coor_scd)
        wrist = np.array(coor_trd)

        radius = np.arctan2(wrist[1] - elbow[1], wrist[0] - elbow[0]) - np.arctan2(shoulder[1] - elbow[1],
                                                                                   shoulder[0] - elbow[0])
        angle = np.abs(radius * 180 / np.pi)

        if angle > 180.0:
            angle = 360 - angle
        return angle

    def get_frame(self):
        with self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
            ret, frame = self.cap.read()
            # Recolor image to RGB
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make detection
            results = pose.process(image)

            # Recolor back to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Extract landmarks
            try:
                landmarks = results.pose_landmarks.landmark

                if self.ROUTE[self.current_route] == '아령들기':
                # if self.ROUTE[self.current_route] == '아령들기':
                    # 어깨, 팔꿈치, 손목
                    coor_left_shoulder: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                                       landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    coor_left_elbow: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                                                    landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                    coor_left_wrist: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                                                    landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]

                    coor_right_shoulder: List[float] = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,
                                                        landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
                    coor_right_elbow: List[float] = [landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,
                                                     landmarks[self.mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
                    coor_right_wrist: List[float] = [landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].x,
                                                     landmarks[self.mp_pose.PoseLandmark.RIGHT_WRIST.value].y]

                    left_angle: float = self.calculate_angle(coor_left_shoulder, coor_left_elbow, coor_left_wrist)
                    right_angle: float = self.calculate_angle(coor_right_shoulder, coor_right_elbow, coor_right_wrist)

                    if left_angle > 160:
                        self.stage = 'DOWN'
                    if left_angle < 30 and self.stage == 'DOWN':
                        self.stage = 'UP'
                        self.left_counter += 1

                    if right_angle > 160:
                        self.stage = 'DOWN'
                    if right_angle < 30 and self.stage == 'DOWN':
                        self.stage = 'UP'
                        self.right_counter += 1

                    if self.left_counter >= 1 and self.right_counter >= 1:
                        self.counter += 1
                        self.left_counter = 0
                        self.right_counter = 0
                        if self.counter == self.REPEATS:  # 15회
                            self.current_set += 1
                            self.counter = 0
                            if self.current_set == self.SET:  # 3세트면 다음 운동 / 혹은 종료(구현 필요)
                                self.current_set = 0
                                self.current_route += 1


                elif self.ROUTE[self.current_route]  == '스쿼트':
                    # 골반(hip), 무릎(knee), 발목(ankle)
                    coor_left_hip: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                                                  landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    coor_left_knee: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                                                   landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    coor_left_ankle: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                                                    landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    coor_right_hip: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x,
                                                   landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    coor_right_knee: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                                                    landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    coor_right_ankle: List[float] = [landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                                                     landmarks[self.mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

                    left_angle: float = self.calculate_angle(coor_left_hip, coor_left_knee, coor_left_ankle)
                    right_angle: float = self.calculate_angle(coor_right_hip, coor_right_knee, coor_right_ankle)

                    # 정면에서 보면 다리 각도가 잘 보이는지 확인하기
                    if left_angle >= 170 and right_angle >= 170 and self.stage == 'DOWN':
                        self.stage = 'UP'
                        self.counter += 1
                    if left_angle <= 120 and right_angle <= 120:
                        self.stage = 'DOWN'

                    if self.counter == self.REPEATS:  # 15회
                        self.current_set += 1
                        self.counter = 0
                        if self.current_set == self.SET:  # 3세트면 다음 운동 / 혹은 종료(구현 필요)
                            self.current_set = 0
                            self.current_route += 1
                    #
                    # cv2.putText(img=image, text=str(int(left_angle)), org=(1000, 100),
                    #             # tuple(np.multiply(coor_elbow, [image.shape[0], image.shape[1]]).astype(int))
                    #             fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=self.BLUE_COLOR, thickness=2,
                    #             lineType=cv2.LINE_AA)

                # landmarks = results.pose_landmarks.landmark
                #
                # # Get coordinates
                # shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                #             landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                # elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                #          landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
                # wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                #          landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y]
                #
                # # Calculate angle
                # angle = self.calculate_angle(shoulder, elbow, wrist)
                #
                # # Visualize angle
                # cv2.putText(image, str(angle),
                #             tuple(np.multiply(elbow, [640, 480]).astype(int)),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA
                #             )
                #
                # # Curl counter logic
                # if angle > 160:
                #     self.stage = "down"
                # if angle < 30 and self.stage == 'down':
                #     self.stage = "up"
                #     self.counter += 1

            except:
                pass

            # Render curl counter
            # Setup status box
            cv2.rectangle(img=image, pt1=(0, 0), pt2=(400, 70), color=(245, 117, 16), thickness=-1)  # 280

            # Repeat data
            cv2.putText(img=image, text='REPS', org=(11, 12), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5, color=(0, 0, 0), thickness=1, lineType=cv2.LINE_AA)
            cv2.putText(img=image, text=str(self.counter), org=(10, 60), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=2, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
            # Stage data
            cv2.putText(img=image, text='STAGE', org=(100, 12), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5, color=(0, 0, 0), thickness=1, lineType=cv2.LINE_AA)
            cv2.putText(img=image, text=self.stage, org=(100, 60), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=2, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)
            # Set data
            cv2.putText(img=image, text='SET', org=(290, 12), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=0.5, color=(0, 0, 0), thickness=1, lineType=cv2.LINE_AA)
            cv2.putText(img=image, text=str(self.current_set), org=(290, 60), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                        fontScale=2, color=(255, 255, 255), thickness=2, lineType=cv2.LINE_AA)

            # Render detections
            self.mp_drawing.draw_landmarks(image, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS,
                                      self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                      self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                      )

            # cv2.imshow('Mediapipe Feed', image)
             # image = self.frame
            _, jpeg = cv2.imencode('.jpg', image)
            return jpeg.tobytes()


    # def update(self):
    #     while True:
    #         (self.grabbed, self.frame) = self.video.read()

def gen(camera):
    while True:
        frame = camera.get_frame()
        yield(b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


@gzip.gzip_page
def detectme(request):
    try:
        cam = VideoCamera()
        return StreamingHttpResponse(gen(cam), content_type='multipart/x-mixed-replace;boundary=frame')
    except:
        print("에러입니다")
        pass
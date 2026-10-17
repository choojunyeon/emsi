import cv2
import mediapipe as mp
import math
import serial
import time


# ============================================================
# 1. 설정
# ============================================================

CAMERA_INDEX = 0

# ============================================================
# 아두이노 USB 시리얼 통신 설정 (추가)
# ============================================================

SERIAL_PORT = "COM8"  # 장치 관리자에서 확인한 아두이노 포트
BAUD_RATE = 9600       # 아두이노 코드의 Serial.begin(9600)과 같아야 함

arduino = None

try:
    arduino = serial.Serial(
        port=SERIAL_PORT,
        baudrate=BAUD_RATE,
        timeout=1
    )

    # USB 시리얼 연결 직후 아두이노가 재시작되는 시간을 기다림
    time.sleep(2)
    print(f"아두이노 USB 연결 성공: {SERIAL_PORT}")

except serial.SerialException as e:
    print(f"아두이노 USB 연결 실패: {e}")
    print("COM8 포트와 USB 연결 상태를 확인하세요.")

# 좌우 모터의 목표 각도 범위
LR_MIN_ANGLE = 60
LR_MAX_ANGLE = 120

# 상하 모터의 목표 각도 범위
UD_MIN_ANGLE = 0
UD_MAX_ANGLE = 180

# 그리퍼 모터의 목표 각도 범위
GRIP_MIN_ANGLE = 0
GRIP_MAX_ANGLE = 180


# 거리 범위: 우선 테스트용 예시값
# 카메라 화면에서 실제 거리값을 확인한 뒤 조정해야 한다.

LR_DIST_MIN = 0.05
LR_DIST_MAX = 0.50

UD_DIST_MIN = 0.05
UD_DIST_MAX = 0.60

GRIP_DIST_MIN = 0.02
GRIP_DIST_MAX = 0.20


# True로 바꾸면 거리가 커질 때 각도가 작아진다.
LR_REVERSE = False
UD_REVERSE = False
GRIP_REVERSE = True

# 모터 제어 설정

SEND_INTERVAL = 0.1  # 0.1초마다 명령 전송
MAX_ANGLE_STEP = 1   # 한 번에 최대 2도씩 변경

last_send_time = 0

# 실제 모터에 전달할 각도
current_lr = 90
current_ud = 90
current_grip = 90


# ============================================================
# 2. 거리 및 중점 계산 함수
# ============================================================

def distance(p1, p2):
    """두 랜드마크의 x, y 좌표 사이의 거리"""

    dx = p1.x - p2.x
    dy = p1.y - p2.y

    return math.sqrt(dx * dx + dy * dy)


def midpoint(p1, p2):
    """두 랜드마크 사이의 중점 좌표를 계산"""

    mid_x = (p1.x + p2.x) / 2
    mid_y = (p1.y + p2.y) / 2

    return (mid_x, mid_y)


def distance_to_point(p, center):
    """랜드마크 p와 중점 center 사이의 거리"""

    dx = p.x - center[0]
    dy = p.y - center[1]

    return math.sqrt(dx * dx + dy * dy)


def map_angle(value, d_min, d_max,
              a_min, a_max, reverse=False):
    """거리값을 서보모터 목표 각도로 변환"""

    # 거리 범위 설정 오류 방지
    if d_max <= d_min:
        raise ValueError("최대 거리는 최소 거리보다 커야 합니다.")

    # 거리가 지정 범위를 벗어나지 않도록 제한
    value = max(d_min, min(d_max, value))

    # 거리 범위에서 현재 값의 비율 계산: 0~1
    ratio = (value - d_min) / (d_max - d_min)

    # 모터 방향 반전
    if reverse:
        ratio = 1.0 - ratio

    # 비율을 목표 각도 범위로 변환
    angle = a_min + ratio * (a_max - a_min)

    return int(round(angle))


# ============================================================
# 3. MediaPipe Pose와 Hands 모델 준비
# ============================================================

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


# 몸 관절 인식 모델
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# 손가락 인식 모델
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ============================================================
# 4. 카메라 시작
# ============================================================

cap = cv2.VideoCapture(CAMERA_INDEX)

if not cap.isOpened():
    print("카메라를 열 수 없습니다.")

    pose.close()
    hands.close()

    raise SystemExit


print("Pose + Hands 인식을 시작합니다.")
print("종료하려면 카메라 창에서 Q를 누르세요.")


# 관절이 잠시 인식되지 않아도 이전 목표 각도를 유지
angle_lr = 90
angle_ud = 90
angle_grip = 90


# 화면에 표시할 거리의 초기값
lr_dist = None
ud_dist = None
grip_dist = None


# ============================================================
# 5. 실시간 인식
# ============================================================

try:
    while True:

        # 카메라에서 한 프레임 읽기
        success, frame = cap.read()

        if not success:
            print("카메라 영상을 읽을 수 없습니다.")
            break

        # 거울처럼 좌우 반전
        frame = cv2.flip(frame, 1)

        # BGR을 RGB로 변환
        rgb_frame = cv2.cvtColor(
            frame, cv2.COLOR_BGR2RGB
        )

        # 몸과 손을 각각 인식
        pose_results = pose.process(rgb_frame)
        hand_results = hands.process(rgb_frame)

        h, w = frame.shape[:2]


        # ====================================================
        # 6. 좌우 및 상하 모터: Pose 모델
        # ====================================================

        if pose_results.pose_landmarks:

            body = pose_results.pose_landmarks.landmark

            # Pose 랜드마크 번호
            # 11 = 왼쪽 어깨
            # 12 = 오른쪽 어깨
            # 19 = 왼쪽 검지
            # 24 = 오른쪽 엉덩이

            p11 = body[11]
            p12 = body[12]
            p19 = body[19]
            p24 = body[24]

            # ------------------------------------------------
            # 좌우 모터
            # Pose 12번과 24번의 중점 계산
            # Pose 19번과 그 중점 사이의 거리 계산
            # ------------------------------------------------

            center = midpoint(p12, p24)

            lr_dist = distance_to_point(p19, center)

            angle_lr = map_angle(
                lr_dist,
                LR_DIST_MIN,
                LR_DIST_MAX,
                LR_MIN_ANGLE,
                LR_MAX_ANGLE,
                LR_REVERSE
            )

            # ------------------------------------------------
            # 상하 모터
            # Pose 19번과 Pose 11번 사이의 거리 계산
            # ------------------------------------------------

            ud_dist = distance(p19, p11)

            angle_ud = map_angle(
                ud_dist,
                UD_DIST_MIN,
                UD_DIST_MAX,
                UD_MIN_ANGLE,
                UD_MAX_ANGLE,
                UD_REVERSE
            )

            # 몸 관절과 연결선 그리기
            mp_draw.draw_landmarks(
                frame,
                pose_results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS
            )

            # 사용 중인 관절 번호 표시
            for idx in [11, 12, 19, 24]:

                point = body[idx]

                x = int(point.x * w)
                y = int(point.y * h)

                cv2.circle(
                    frame, (x, y), 7,
                    (0, 255, 255), -1
                )

                cv2.putText(
                    frame, str(idx), (x + 8, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 255), 2
                )

            # 12번과 24번의 중점 표시
            cx = int(center[0] * w)
            cy = int(center[1] * h)

            cv2.circle(
                frame, (cx, cy), 8,
                (255, 0, 255), -1
            )

            cv2.putText(
                frame, "MID 12-24", (cx + 8, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (255, 0, 255), 2
            )

        else:
            cv2.putText(
                frame, "POSE NOT DETECTED",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 0, 255), 2
            )


        # ====================================================
        # 7. 그리퍼 모터: 오른손 Hands 모델만 사용
        # ====================================================

        right_hand_found = False

        if (
            hand_results.multi_hand_landmarks
            and hand_results.multi_handedness
        ):

            # 인식된 모든 손을 확인한다.
            for hand_landmarks, handedness in zip(
                hand_results.multi_hand_landmarks,
                hand_results.multi_handedness
            ):

                # MediaPipe가 판단한 손의 종류
                # 'Left' 또는 'Right'
                label = handedness.classification[0].label

                # 왼손이면 건너뛰고 오른손만 처리
                if label != "Left":
                    continue

                right_hand_found = True

                # 오른손의 21개 랜드마크
                hand = hand_landmarks.landmark

                # Hands 번호
                # 4 = 엄지 끝
                # 8 = 검지 끝
                thumb_tip = hand[4]
                index_tip = hand[8]

                # 엄지 끝과 검지 끝 사이 거리
                grip_dist = distance(
                    thumb_tip,
                    index_tip
                )

                # 거리를 그리퍼 목표 각도로 변환
                angle_grip = map_angle(
                    grip_dist,
                    GRIP_DIST_MIN,
                    GRIP_DIST_MAX,
                    GRIP_MIN_ANGLE,
                    GRIP_MAX_ANGLE,
                    GRIP_REVERSE
                )

                # 오른손 관절 연결선 표시
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                # 엄지 끝과 검지 끝 강조
                for idx in [4, 8]:

                    point = hand[idx]

                    x = int(point.x * w)
                    y = int(point.y * h)

                    cv2.circle(
                        frame, (x, y), 8,
                        (255, 0, 255), -1
                    )

                    cv2.putText(
                        frame, str(idx),
                        (x + 8, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255, 0, 255), 2
                    )

                # 손목 근처에 오른손과 신뢰도 표시
                wrist = hand[0]

                wx = int(wrist.x * w)
                wy = int(wrist.y * h)

                score = handedness.classification[0].score

                cv2.putText(
                    frame,
                    f"Right hand ({score:.2f})",
                    (wx, wy - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 0, 255), 2
                )

                # 오른손만 사용하므로 한 손을 처리한 뒤 종료
                break


        # 오른손을 찾지 못하면 그리퍼 각도는 이전 값 유지
        if not right_hand_found:
            cv2.putText(
                frame,
                "LEFT HAND NOT DETECTED",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 0, 255), 2
            )


        # ====================================================
        # 8. 거리 및 목표 각도 표시
        # ====================================================

        if lr_dist is None or not pose_results.pose_landmarks:
            lr_text = "LR distance: --"
            ud_text = "UD distance: --"
        else:
            lr_text = f"LR distance: {lr_dist:.3f}"
            ud_text = f"UD distance: {ud_dist:.3f}"

        if grip_dist is None or not right_hand_found:
            grip_text = "Grip distance: --"
        else:
            grip_text = f"Grip distance: {grip_dist:.3f}"

        info = [
            lr_text,
            f"LR target: {angle_lr} deg",
            ud_text,
            f"UD target: {angle_ud} deg",
            grip_text,
            f"Grip target: {angle_grip} deg"
        ]

        for i, text in enumerate(info):

            cv2.putText(
                frame,
                text,
                (10, 100 + i * 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (0, 255, 0), 2
            )


        if arduino is not None and arduino.is_open:

    # 세 모터의 목표 각도를 쉼표로 구분하고
    # 마지막에 줄바꿈 문자(\n)를 붙여 전송한다.
            data = f"{angle_lr},{angle_ud},{angle_grip}\n"

            try:
        # Arduino로 명령 전송
                arduino.write(data.encode("utf-8"))

        # 전송된 값 확인
                print(f"전송: {angle_lr},{angle_ud},{angle_grip}")

            except (serial.SerialException, OSError) as e:
                print(f"USB 데이터 전송 오류: {e}")

        # ====================================================
        # 9. 화면 표시 및 종료
        # ====================================================

        cv2.imshow(
            "Robot Arm - Pose + Right Hand",
            frame
        )

        # Q를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


finally:

    # 카메라와 모델 정리
    cap.release()
    pose.close()
    hands.close()
    cv2.destroyAllWindows()

    # 아두이노 USB 연결 종료 (추가)
    if arduino is not None and arduino.is_open:
        arduino.close()
        print("아두이노 USB 연결을 종료했습니다.")

    print("Pose + Hands 테스트를 종료했습니다.")

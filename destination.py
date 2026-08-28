import cv2
import numpy as np
import mediapipe as mp


# ============================================================
# 1. 카메라
# ============================================================

cap = cv2.VideoCapture(0)


# ============================================================
# 2. ArUco 설정
# ============================================================

aruco_dict = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_4X4_50
)

parameters = cv2.aruco.DetectorParameters()

detector = cv2.aruco.ArucoDetector(
    aruco_dict,
    parameters
)


# ============================================================
# 3. 사용할 ArUco
# ============================================================

# 0 = 왼쪽 위
# 1 = 오른쪽 위
# 2 = 오른쪽 아래
# 3 = 왼쪽 아래

MARKER_IDS = [0, 1, 2, 3]


# ============================================================
# 4. 평면 크기
# ============================================================

# 실제 평면 크기를 아직 모르기 때문에
# 현재는 800 x 800 좌표계를 사용

OUTPUT_WIDTH = 800
OUTPUT_HEIGHT = 800


# ============================================================
# 5. 목적지 설정
# ============================================================

# 사람으로부터 목적지를 얼마나 멀리 떨어뜨릴지
#
# 현재 단위:
# 평면 좌표 기준
#
# 나중에 실제 cm 단위로 변경 가능

NORMAL_LENGTH = 100


# ============================================================
# 6. Homography
# ============================================================

H = None
H_INV = None


# ============================================================
# 7. MediaPipe Pose
# ============================================================

mp_pose = mp.solutions.pose

pose_model = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# ============================================================
# 8. ArUco 중심 계산
# ============================================================

def get_marker_center(corners):

    points = corners.reshape(4, 2)

    center = np.mean(
        points,
        axis=0
    )

    return center


# ============================================================
# 9. 픽셀 → 평면 좌표
# ============================================================

def pixel_to_plane(point):

    global H

    if H is None:
        return None

    point = np.array(
        [[point]],
        dtype=np.float32
    )

    transformed = cv2.perspectiveTransform(
        point,
        H
    )

    return transformed[0][0]


# ============================================================
# 10. 평면 → 픽셀 좌표
# ============================================================

def plane_to_pixel(point):

    global H_INV

    if H_INV is None:
        return None

    point = np.array(
        [[point]],
        dtype=np.float32
    )

    transformed = cv2.perspectiveTransform(
        point,
        H_INV
    )

    return transformed[0][0]


# ============================================================
# 11. 두 점의 중점
# ============================================================

def get_midpoint(point1, point2):

    return (
        point1 + point2
    ) / 2.0


# ============================================================
# 12. 목적지 계산
# ============================================================

def calculate_destination(
    shoulder,
    hip
):

    # --------------------------------------------------------
    # 어깨 → 허리 방향 벡터
    # --------------------------------------------------------

    body_vector = hip - shoulder


    length = np.linalg.norm(
        body_vector
    )


    # 너무 가까운 경우 계산 불가능
    if length < 1e-6:

        return None, None, None


    # --------------------------------------------------------
    # 사람의 몸 방향 단위벡터
    # --------------------------------------------------------

    body_unit = (
        body_vector / length
    )


    # --------------------------------------------------------
    # 법선 벡터
    #
    # 몸 방향 벡터:
    #
    #       어깨
    #        |
    #        |
    #       허리
    #
    # 이 벡터에 수직인 방향을 계산
    # --------------------------------------------------------

    normal = np.array(
        [
            -body_unit[1],
            body_unit[0]
        ],
        dtype=np.float32
    )


    # --------------------------------------------------------
    # 어깨 + 허리 중점
    # --------------------------------------------------------

    midpoint = get_midpoint(
        shoulder,
        hip
    )


    # --------------------------------------------------------
    # 법선 벡터 방향으로 목적지 계산
    # --------------------------------------------------------

    destination = (
        midpoint +
        normal * NORMAL_LENGTH
    )


    return (
        midpoint,
        normal,
        destination
    )


# ============================================================
# 13. 메인 루프
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "카메라에서 영상을 가져올 수 없습니다."
        )

        break


    # ========================================================
    # 14. 좌우 반전
    # ========================================================

    frame = cv2.flip(
        frame,
        1
    )


    h, w, _ = frame.shape


    # ========================================================
    # 15. ArUco 검출
    # ========================================================

    corners, ids, rejected = (
        detector.detectMarkers(frame)
    )


    marker_points = {}


    if ids is not None:

        ids = ids.flatten()


        for i, marker_id in enumerate(ids):

            if marker_id not in MARKER_IDS:
                continue


            marker_corners = corners[i][0]


            center = get_marker_center(
                corners[i]
            )


            marker_points[marker_id] = center


            # 마커 표시
            cv2.aruco.drawDetectedMarkers(
                frame,
                corners[i:i + 1],
                np.array([[marker_id]])
            )


            # 중심 표시
            cv2.circle(
                frame,
                tuple(
                    center.astype(int)
                ),
                5,
                (255, 0, 255),
                -1
            )


    # ========================================================
    # 16. 평면 준비
    # ========================================================

    plane_ready = all(
        marker_id in marker_points
        for marker_id in MARKER_IDS
    )


    if plane_ready:

        src_points = np.array(
            [
                marker_points[0],
                marker_points[1],
                marker_points[2],
                marker_points[3]
            ],
            dtype=np.float32
        )


        dst_points = np.array(
            [
                [0, 0],
                [OUTPUT_WIDTH, 0],
                [OUTPUT_WIDTH, OUTPUT_HEIGHT],
                [0, OUTPUT_HEIGHT]
            ],
            dtype=np.float32
        )


        # Homography
        H = cv2.getPerspectiveTransform(
            src_points,
            dst_points
        )


        H_INV = np.linalg.inv(H)


    else:

        H = None
        H_INV = None


    # ========================================================
    # 17. MediaPipe Pose
    # ========================================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    results = pose_model.process(
        rgb
    )


    # ========================================================
    # 18. 사람 인식
    # ========================================================

    if results.pose_landmarks:

        landmarks = (
            results.pose_landmarks.landmark
        )


        # ----------------------------------------------------
        # 왼쪽 어깨
        # MediaPipe Pose:
        # LEFT_SHOULDER = 11
        # ----------------------------------------------------

        left_shoulder = np.array(
            [
                landmarks[11].x * w,
                landmarks[11].y * h
            ],
            dtype=np.float32
        )


        # ----------------------------------------------------
        # 왼쪽 허리
        # MediaPipe Pose:
        # LEFT_HIP = 23
        # ----------------------------------------------------

        left_hip = np.array(
            [
                landmarks[23].x * w,
                landmarks[23].y * h
            ],
            dtype=np.float32
        )


        # ====================================================
        # 19. 어깨 + 허리 중점
        # ====================================================

        midpoint_pixel = (
            get_midpoint(
                left_shoulder,
                left_hip
            )
        )


        # ====================================================
        # 20. 법선 방향 및 목적지 계산
        # ====================================================

        midpoint_pixel, normal, destination_pixel = (
            calculate_destination(
                left_shoulder,
                left_hip
            )
        )


        if destination_pixel is not None:


            # =================================================
            # 21. 법선 벡터 표시
            # =================================================

            cv2.arrowedLine(
                frame,
                tuple(
                    midpoint_pixel.astype(int)
                ),
                tuple(
                    destination_pixel.astype(int)
                ),
                (255, 0, 0),
                3,
                tipLength=0.2
            )


            # -------------------------------------------------
            # 어깨 표시
            # -------------------------------------------------

            cv2.circle(
                frame,
                tuple(
                    left_shoulder.astype(int)
                ),
                7,
                (0, 255, 255),
                -1
            )


            # -------------------------------------------------
            # 허리 표시
            # -------------------------------------------------

            cv2.circle(
                frame,
                tuple(
                    left_hip.astype(int)
                ),
                7,
                (0, 255, 255),
                -1
            )


            # -------------------------------------------------
            # 중점 표시
            # -------------------------------------------------

            cv2.circle(
                frame,
                tuple(
                    midpoint_pixel.astype(int)
                ),
                8,
                (255, 0, 255),
                -1
            )


            # =================================================
            # 22. 평면 좌표로 변환
            # =================================================

            if plane_ready:

                destination_plane = (
                    pixel_to_plane(
                        destination_pixel
                    )
                )


                midpoint_plane = (
                    pixel_to_plane(
                        midpoint_pixel
                    )
                )


                if (
                    destination_plane is not None
                    and midpoint_plane is not None
                ):

                    destination_x = float(
                        destination_plane[0]
                    )

                    destination_y = float(
                        destination_plane[1]
                    )


                    midpoint_x = float(
                        midpoint_plane[0]
                    )

                    midpoint_y = float(
                        midpoint_plane[1]
                    )


                    # =========================================
                    # 23. 목적지 좌표 화면 표시
                    # =========================================

                    cv2.putText(
                        frame,
                        "DESTINATION",
                        (
                            int(destination_pixel[0]) + 10,
                            int(destination_pixel[1]) - 30
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 0, 0),
                        2
                    )


                    cv2.putText(
                        frame,
                        f"X: {destination_x:.1f}",
                        (
                            int(destination_pixel[0]) + 10,
                            int(destination_pixel[1])
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 0, 0),
                        2
                    )


                    cv2.putText(
                        frame,
                        f"Y: {destination_y:.1f}",
                        (
                            int(destination_pixel[0]) + 10,
                            int(destination_pixel[1]) + 25
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 0, 0),
                        2
                    )


                    # =========================================
                    # 터미널 출력
                    # =========================================

                    print(
                        f"DESTINATION -> "
                        f"X: {destination_x:.1f}, "
                        f"Y: {destination_y:.1f}"
                    )


                    # =========================================
                    # 중점 좌표도 출력
                    # =========================================

                    print(
                        f"BODY MIDPOINT -> "
                        f"X: {midpoint_x:.1f}, "
                        f"Y: {midpoint_y:.1f}"
                    )


            else:

                cv2.putText(
                    frame,
                    "PLANE NOT READY",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )


    # ========================================================
    # 24. 상태 표시
    # ========================================================

    if plane_ready:

        cv2.putText(
            frame,
            "PLANE READY",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            frame,
            "PLANE NOT READY",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


    # ========================================================
    # 25. 화면 출력
    # ========================================================

    cv2.imshow(
        "Destination Detection",
        frame
    )


    # ========================================================
    # 26. ESC 종료
    # ========================================================

    if cv2.waitKey(1) & 0xFF == 27:

        break


# ============================================================
# 27. 종료
# ============================================================

cap.release()

pose_model.close()

cv2.destroyAllWindows()

import cv2
import numpy as np
from ultralytics import YOLO


# ============================================================
# 1. YOLO 모델
# ============================================================

# 현재는 COCO 기본 모델 사용
# 사람 = class 0
# 자동차 = class 2
model = YOLO("yolo11n.pt")


# ============================================================
# 2. 카메라
# ============================================================

cap = cv2.VideoCapture(0)


# ============================================================
# 3. ArUco 설정
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
# 4. 사용할 ArUco
# ============================================================

# 0 = 왼쪽 위
# 1 = 오른쪽 위
# 2 = 오른쪽 아래
# 3 = 왼쪽 아래

MARKER_IDS = [0, 1, 2, 3]


# ============================================================
# 5. 평면 화면 크기
# ============================================================

# plane.py와 반드시 동일해야 함

OUTPUT_WIDTH = 800
OUTPUT_HEIGHT = 800


# ============================================================
# 6. Homography
# ============================================================

H = None
H_INV = None


# ============================================================
# 7. ArUco 중심 좌표
# ============================================================

def get_marker_center(corners):

    points = corners.reshape(4, 2)

    center = np.mean(
        points,
        axis=0
    )

    return center


# ============================================================
# 8. 카메라 좌표 → 평면 좌표
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
# 9. 평면 좌표 → 카메라 좌표
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
# 10. 객체 좌표 저장
# ============================================================

# 나중에 다른 파일에서 사용할 값

person_positions = []

car_positions = []


# ============================================================
# 11. 메인 루프
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "카메라에서 영상을 가져올 수 없습니다."
        )

        break


    # ========================================================
    # 12. ArUco 검출
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


            # 중심점
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
    # 13. 4개의 ArUco가 모두 있는지 확인
    # ========================================================

    plane_ready = all(
        marker_id in marker_points
        for marker_id in MARKER_IDS
    )


    if plane_ready:

        # ----------------------------------------------------
        # 카메라 좌표
        # ----------------------------------------------------

        src_points = np.array(
            [
                marker_points[0],
                marker_points[1],
                marker_points[2],
                marker_points[3]
            ],
            dtype=np.float32
        )


        # ----------------------------------------------------
        # 평면 좌표
        # ----------------------------------------------------

        dst_points = np.array(
            [
                [0, 0],
                [OUTPUT_WIDTH, 0],
                [OUTPUT_WIDTH, OUTPUT_HEIGHT],
                [0, OUTPUT_HEIGHT]
            ],
            dtype=np.float32
        )


        # ----------------------------------------------------
        # Homography 계산
        # ----------------------------------------------------

        H = cv2.getPerspectiveTransform(
            src_points,
            dst_points
        )


        H_INV = np.linalg.inv(H)


    else:

        H = None
        H_INV = None


    # ========================================================
    # 14. YOLO 객체 검출
    # ========================================================

    results = model(
        frame,
        verbose=False
    )


    # 이전 프레임의 좌표 초기화
    person_positions = []
    car_positions = []


    # ========================================================
    # 15. 객체 처리
    # ========================================================

    for result in results:

        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )


            # ------------------------------------------------
            # 사람(0), 자동차(2)만 사용
            # ------------------------------------------------

            if class_id not in [0, 2]:
                continue


            # ------------------------------------------------
            # 신뢰도
            # ------------------------------------------------

            if confidence < 0.5:
                continue


            # ------------------------------------------------
            # Bounding Box
            # ------------------------------------------------

            x1, y1, x2, y2 = (
                box.xyxy[0]
                .cpu()
                .numpy()
            )


            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)


            # =================================================
            # 16. 객체 바닥 중심점
            # =================================================

            object_x = int(
                (x1 + x2) / 2
            )

            object_y = y2


            object_pixel = np.array(
                [
                    object_x,
                    object_y
                ],
                dtype=np.float32
            )


            # =================================================
            # 17. 객체 종류
            # =================================================

            if class_id == 0:

                object_name = "PERSON"

            else:

                object_name = "CAR"


            # =================================================
            # 18. Bounding Box 표시
            # =================================================

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            # 바닥 중심점
            cv2.circle(
                frame,
                (
                    object_x,
                    object_y
                ),
                7,
                (0, 0, 255),
                -1
            )


            # =================================================
            # 19. 평면 좌표 변환
            # =================================================

            if plane_ready and H is not None:

                plane_position = (
                    pixel_to_plane(
                        object_pixel
                    )
                )


                if plane_position is not None:

                    plane_x = float(
                        plane_position[0]
                    )

                    plane_y = float(
                        plane_position[1]
                    )


                    # =========================================
                    # 사람 좌표 저장
                    # =========================================

                    if class_id == 0:

                        person_positions.append(
                            np.array(
                                [
                                    plane_x,
                                    plane_y
                                ],
                                dtype=np.float32
                            )
                        )


                    # =========================================
                    # 자동차 좌표 저장
                    # =========================================

                    elif class_id == 2:

                        car_positions.append(
                            np.array(
                                [
                                    plane_x,
                                    plane_y
                                ],
                                dtype=np.float32
                            )
                        )


                    # =========================================
                    # 화면에 좌표 표시
                    # =========================================

                    cv2.putText(
                        frame,
                        object_name,
                        (
                            x1,
                            y1 - 45
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )


                    cv2.putText(
                        frame,
                        f"X: {plane_x:.1f}",
                        (
                            x1,
                            y1 - 25
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )


                    cv2.putText(
                        frame,
                        f"Y: {plane_y:.1f}",
                        (
                            x1,
                            y1 - 5
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2
                    )


                    # 터미널 출력
                    print(
                        f"{object_name} -> "
                        f"X: {plane_x:.1f}, "
                        f"Y: {plane_y:.1f}"
                    )


            else:

                cv2.putText(
                    frame,
                    f"{object_name}: "
                    f"PLANE NOT READY",
                    (
                        x1,
                        y1 - 10
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )


    # ========================================================
    # 20. 평면 상태 표시
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
    # 21. 화면 출력
    # ========================================================

    cv2.imshow(
        "Person & Car Position",
        frame
    )


    # ESC 종료
    if cv2.waitKey(1) & 0xFF == 27:
        break


# ============================================================
# 22. 종료
# ============================================================

cap.release()

cv2.destroyAllWindows()

import cv2
import numpy as np


# ============================================================
# 1. 카메라 설정
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
# 3. 사용할 ArUco ID
# ============================================================

# 0 = 왼쪽 위
# 1 = 오른쪽 위
# 2 = 오른쪽 아래
# 3 = 왼쪽 아래

MARKER_IDS = [0, 1, 2, 3]


# ============================================================
# 4. 변환된 평면 화면 크기
# ============================================================

# 실제 평면 크기가 아직 정해지지 않았으므로
# 여기서는 단순히 화면상의 좌표계로 사용한다.

OUTPUT_WIDTH = 800
OUTPUT_HEIGHT = 800


# ============================================================
# 5. 현재 평면 변환 행렬
# ============================================================

H = None
H_INV = None


# ============================================================
# 6. ArUco 중심 좌표
# ============================================================

def get_marker_center(corners):

    points = corners.reshape(4, 2)

    center = np.mean(
        points,
        axis=0
    )

    return center


# ============================================================
# 7. 카메라 좌표 → 평면 좌표
# ============================================================

def pixel_to_plane(point):

    """
    카메라 화면상의 픽셀 좌표를
    변환된 평면 좌표로 변환한다.

    예:

        카메라 좌표
        (x, y)
            ↓
        평면 좌표
        (x, y)

    주의:
    현재 평면의 실제 크기를 모르기 때문에
    결과의 단위는 cm가 아니라
    평면 화면 기준 좌표이다.
    """

    global H

    if H is None:
        return None

    point = np.array(
        [
            [point]
        ],
        dtype=np.float32
    )

    transformed = cv2.perspectiveTransform(
        point,
        H
    )

    return transformed[0][0]


# ============================================================
# 8. 평면 좌표 → 카메라 좌표
# ============================================================

def plane_to_pixel(point):

    """
    평면 좌표를 다시 카메라 화면 좌표로 변환한다.
    """

    global H_INV

    if H_INV is None:
        return None

    point = np.array(
        [
            [point]
        ],
        dtype=np.float32
    )

    transformed = cv2.perspectiveTransform(
        point,
        H_INV
    )

    return transformed[0][0]


# ============================================================
# 9. 평면 준비 여부 확인
# ============================================================

def is_plane_ready():

    return H is not None


# ============================================================
# 10. 메인 루프
# ============================================================

while True:

    ret, frame = cap.read()

    if not ret:

        print(
            "카메라에서 영상을 가져올 수 없습니다."
        )

        break


    # --------------------------------------------------------
    # ArUco 검출
    # --------------------------------------------------------

    corners, ids, rejected = (
        detector.detectMarkers(frame)
    )


    marker_points = {}


    # ========================================================
    # 11. ArUco 검출
    # ========================================================

    if ids is not None:

        ids = ids.flatten()


        for i, marker_id in enumerate(ids):

            if marker_id not in MARKER_IDS:
                continue


            # 마커 네 꼭짓점
            marker_corners = corners[i][0]


            # 마커 중심
            center = get_marker_center(
                corners[i]
            )


            marker_points[marker_id] = center


            # ------------------------------------------------
            # 마커 표시
            # ------------------------------------------------

            cv2.aruco.drawDetectedMarkers(
                frame,
                corners[i:i + 1],
                np.array([[marker_id]])
            )


            cv2.circle(
                frame,
                tuple(
                    center.astype(int)
                ),
                6,
                (0, 255, 0),
                -1
            )


            cv2.putText(
                frame,
                f"ID {marker_id}",
                (
                    int(center[0]) + 10,
                    int(center[1])
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )


    # ========================================================
    # 12. 4개의 마커가 모두 발견된 경우
    # ========================================================

    if all(
        marker_id in marker_points
        for marker_id in MARKER_IDS
    ):


        # ----------------------------------------------------
        # 카메라 화면상의 4개 점
        # ----------------------------------------------------

        src_points = np.array(
            [
                marker_points[0],  # 왼쪽 위
                marker_points[1],  # 오른쪽 위
                marker_points[2],  # 오른쪽 아래
                marker_points[3]   # 왼쪽 아래
            ],
            dtype=np.float32
        )


        # ----------------------------------------------------
        # 변환 후 평면 좌표
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


        # 역변환 행렬
        H_INV = np.linalg.inv(H)


        # ====================================================
        # 13. 평면으로 변환
        # ====================================================

        plane = cv2.warpPerspective(
            frame,
            H,
            (
                OUTPUT_WIDTH,
                OUTPUT_HEIGHT
            )
        )


        # ====================================================
        # 14. 평면 좌표계 표시
        # ====================================================

        # X축
        cv2.line(
            plane,
            (0, OUTPUT_HEIGHT // 2),
            (OUTPUT_WIDTH, OUTPUT_HEIGHT // 2),
            (255, 255, 255),
            1
        )


        # Y축
        cv2.line(
            plane,
            (OUTPUT_WIDTH // 2, 0),
            (OUTPUT_WIDTH // 2, OUTPUT_HEIGHT),
            (255, 255, 255),
            1
        )


        # ----------------------------------------------------
        # 좌표 표시
        # ----------------------------------------------------

        cv2.putText(
            plane,
            "(0, 0)",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        cv2.putText(
            plane,
            f"({OUTPUT_WIDTH}, {OUTPUT_HEIGHT})",
            (
                OUTPUT_WIDTH - 180,
                OUTPUT_HEIGHT - 15
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )


        # ====================================================
        # 15. 평면 상태
        # ====================================================

        cv2.putText(
            frame,
            "PLANE READY",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 0),
            3
        )


        # 평면 출력
        cv2.imshow(
            "Plane",
            plane
        )


    else:

        # ====================================================
        # 16. 마커가 부족한 경우
        # ====================================================

        cv2.putText(
            frame,
            "Find all 4 ArUco markers",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )


        cv2.putText(
            frame,
            f"Detected: "
            f"{len(marker_points)} / 4",
            (30, 85),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )


        # 기존 평면 행렬 초기화
        H = None
        H_INV = None


    # ========================================================
    # 17. 카메라 화면 출력
    # ========================================================

    cv2.imshow(
        "Camera",
        frame
    )


    # ========================================================
    # 18. ESC 종료
    # ========================================================

    key = cv2.waitKey(1)

    if key == 27:
        break


# ============================================================
# 19. 종료
# ============================================================

cap.release()

cv2.destroyAllWindows()

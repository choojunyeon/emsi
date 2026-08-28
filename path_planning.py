if pose_result.pose_landmarks:

        landmarks = (
            pose_result.pose_landmarks.landmark
        )


        # ----------------------------------------------------
        # 사람 관절점
        # ----------------------------------------------------

        person_points_pixel = (
            get_person_points(
                landmarks,
                w,
                h
            )
        )


        if len(
            person_points_pixel
        ) >= 3:

            hull_pixel = (
                make_convex_hull(
                    person_points_pixel
                )
            )


            # ------------------------------------------------
            # 사람 안전거리 확보
            # ------------------------------------------------

            hull_pixel = expand_hull(
                hull_pixel,
                30
            )


            # ------------------------------------------------
            # 평면 좌표로 변환
            # ------------------------------------------------

            if H is not None:

                hull_plane = []


                for point in hull_pixel:

                    plane_point = (
                        pixel_to_plane(
                            point
                        )
                    )


                    if plane_point is not None:

                        hull_plane.append(
                            plane_point
                        )


                if len(
                    hull_plane
                ) >= 3:

                    person_hull = make_convex_hull(
                        hull_plane
                    )


        # ====================================================
        # 28. 왼쪽 어깨 + 왼쪽 허리
        # ====================================================

        shoulder = np.array(
            [
                landmarks[11].x * w,
                landmarks[11].y * h
            ],
            dtype=np.float32
        )


        hip = np.array(
            [
                landmarks[23].x * w,
                landmarks[23].y * h
            ],
            dtype=np.float32
        )


        # ----------------------------------------------------
        # 몸 방향
        # ----------------------------------------------------

        body_vector = (
            hip - shoulder
        )


        body_length = np.linalg.norm(
            body_vector
        )


        if body_length > 0:

            body_unit = (
                body_vector
                / body_length
            )


            # ------------------------------------------------
            # 법선 벡터
            # ------------------------------------------------

            normal = np.array(
                [
                    -body_unit[1],
                    body_unit[0]
                ],
                dtype=np.float32
            )


            # ------------------------------------------------
            # 어깨 + 허리 중점
            # ------------------------------------------------

            midpoint = (
                shoulder + hip
            ) / 2


            # ------------------------------------------------
            # 목적지 픽셀
            # ------------------------------------------------

            destination_pixel = (
                midpoint
                + normal * 100
            )


            # ------------------------------------------------
            # 평면 좌표
            # ------------------------------------------------

            if H is not None:

                destination_plane = (
                    pixel_to_plane(
                        destination_pixel
                    )
                )


                # 목적지 표시
                destination_screen = (
                    plane_to_pixel(
                        destination_plane
                    )
                )


                if destination_screen is not None:

                    cv2.arrowedLine(
                        frame,
                        tuple(
                            midpoint.astype(int)
                        ),
                        tuple(
                            destination_screen.astype(int)
                        ),
                        (255, 0, 0),
                        3
                    )


                    cv2.circle(
                        frame,
                        tuple(
                            destination_screen.astype(int)
                        ),
                        10,
                        (255, 0, 0),
                        -1
                    )


    # ========================================================
    # 29. 경로 계산
    # ========================================================

if (
        plane_ready
        and
        robot_position is not None
        and
        destination_plane is not None
    ):


        # ----------------------------------------------------
        # Convex Hull을 피해서 목적지까지 경로 계산
        # ----------------------------------------------------

        path = find_best_path(
            robot_position,
            destination_plane,
            person_hull
        )


        if path is not None:


            # ================================================
            # 경로 표시
            # ================================================

            for i in range(
                len(path) - 1
            ):

                p1 = plane_to_pixel(
                    path[i]
                )

                p2 = plane_to_pixel(
                    path[i + 1]
                )


                if (
                    p1 is None
                    or
                    p2 is None
                ):

                    continue


                cv2.line(
                    frame,
                    tuple(
                        p1.astype(int)
                    ),
                    tuple(
                        p2.astype(int)
                    ),
                    (0, 255, 255),
                    4
                )


            # ================================================
            # 다음 목표점
            # ================================================

            if len(path) >= 2:

                next_target = path[1]


                # ============================================
                # 자동차 제어
                # ============================================

                arrived = control_robot(
                    robot_position,
                    next_target,
                    robot_heading
                )


                if arrived:

                    send_command("S")


        else:

            # 안전한 경로가 없으면 정지
            send_command("S")


else:

        # 평면/자동차/목적지 중 하나라도 없으면 정지
        send_command("S")


    # ========================================================
    # 30. 상태 표시
    # ========================================================

if plane_ready:

        cv2.putText(
            frame,
            "PLANE READY",
            (
                20,
                35
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

else:

        cv2.putText(
            frame,
            "PLANE NOT READY",
            (
                20,
                35
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        )


    # ========================================================
    # 31. 화면 출력
    # ========================================================

cv2.imshow(
        "Path Planning",
        frame
    )


    # ========================================================
    # 32. ESC
    # ========================================================

if cv2.waitKey(1) & 0xFF == 27:

        send_command("S")
        break


# ============================================================
# 33. 종료
# ============================================================

send_command("S")

cap.release()

pose_model.close()

sock.close()

cv2.destroyAllWindows()

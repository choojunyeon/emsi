#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A0;    // 조이스틱 좌우 (X축)
const int JOY_Y_PIN = A1;    // 조이스틱 상하 (Y축)
const int JOY_SW_PIN = 2;    // 조이스틱 버튼 (SW)

const int SERVO_LR_PIN = 9;   // 1번: 좌우 서보모터
const int SERVO_UD_PIN = 10;  // 2번: 상하 서보모터
const int SERVO_SW_PIN = 11;  // 3번: 스위치 전용 신규 서보모터

Servo servoLR;
Servo servoUD;
Servo servoSW; // 새 서보모터 객체

// 서보모터 현재 각도 변수 (초기값: 90도)
float angleLR = 90.0;
float angleUD = 90.0;
float angleSW = 90.0; // 새 서보모터 각도

// 각도 제한
const float MIN_LR = 60.0;   // ±30도 -> 60 ~ 120도
const float MAX_LR = 120.0;

const float MIN_UD = 0.0;    // ±90도 -> 0 ~ 180도
const float MAX_UD = 180.0;

const float MIN_SW = 0.0;    // 신규 모터 범위 -> 0 ~ 180도
const float MAX_SW = 180.0;

// 모터 이동 속도
const float STEP_SIZE = 0.5;

// 스위치 상태 및 방향 관리 변수
bool lastBtnState = HIGH;
bool swDirectionToggle = true; // true: 180도 방향, false: 0도 방향

void setup() {
  // 3개 서보모터 핀 연결
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);
  servoSW.attach(SERVO_SW_PIN);

  // 초기 위치 설정 (모두 90도)
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoSW.write((int)angleSW);

  // 조이스틱 버튼 핀 (내부 풀업 저항)
  pinMode(JOY_SW_PIN, INPUT_PULLUP);
}

void loop() {
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);
  int currentBtnState = digitalRead(JOY_SW_PIN);

  // -------------------------------------------------------------
  // 1. 조이스틱 아날로그 레버 동작 (1, 2번 서보모터)
  // -------------------------------------------------------------
  // [좌우 서보모터]
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  } else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }

  // [상하 서보모터]
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  } else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  // -------------------------------------------------------------
  // 2. 조이스틱 스위치 동작 (3번 신규 서보모터 전용)
  // -------------------------------------------------------------
  // 버튼을 눌렀을 때 이동 방향 전환 (토글)
  if (lastBtnState == HIGH && currentBtnState == LOW) {
    swDirectionToggle = !swDirectionToggle;
    delay(50); // 버튼 튐(디바운스) 방지
  }
  lastBtnState = currentBtnState;

  // 버튼을 눌르고 있는 동안(LOW) 신규 서보모터만 이동
  if (currentBtnState == LOW) {
    if (swDirectionToggle == true) {
      angleSW += STEP_SIZE; // 180도 방향으로 증가
    } else {
      angleSW -= STEP_SIZE; // 0도 방향으로 감소
    }
  }
  // (스위치에서 손을 떼면 currentBtnState가 HIGH가 되어 angleSW 조작이 멈춤 -> 현 위치 유지)

  // -------------------------------------------------------------
  // 3. 각도 범위 제한 및 모터 출력
  // -------------------------------------------------------------
  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);
  angleSW = constrain(angleSW, MIN_SW, MAX_SW);

  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoSW.write((int)angleSW);

  delay(15);
}

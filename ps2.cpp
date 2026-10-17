#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A1;   // 조이스틱 좌우 (X축)
const int JOY_Y_PIN = A0;   // 조이스틱 상하 (Y축)
const int JOY_SW_PIN = 2;   // 조이스틱 버튼 (SW)

const int SERVO_LR_PIN = 9;  // 좌우 서보모터
const int SERVO_UD_PIN = 10; // 상하 서보모터
const int SERVO_GRIP_PIN = 11; // 집게 서보모터 (추가)

// 서보모터 객체
Servo servoLR;
Servo servoUD;
Servo servoGrip; // 집게 서보모터 (추가)

// 서보모터 현재 각도 변수 (초기값: 중앙)
float angleLR = 90.0;
float angleUD = 90.0;
float angleGrip = 90.0; // 집게 초기 각도 (추가)

// 각도 제한
const float MIN_LR = 60.0;
const float MAX_LR = 120.0;

const float MIN_UD = 0.0;
const float MAX_UD = 180.0;

// 집게 각도 제한 (추가)
const float MIN_GRIP = 0.0;
const float MAX_GRIP = 180.0;

// 조이스틱 감도
const float STEP_SIZE = 0.5;

// 집게 움직임 속도 (추가)
const float GRIP_STEP_SIZE = 1.0;

// 집게 동작 상태 (추가)
// 0 = 정지
// 1 = 집게 좁히기
// -1 = 집게 풀기
int gripMode = 0;

// 버튼 상태 확인용 변수 (추가)
int lastButtonState = HIGH;
int buttonState = HIGH;

void setup() {
  // 서보모터 핀 연결
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);
  servoGrip.attach(SERVO_GRIP_PIN); // 추가

  // PS2 조이스틱 버튼 설정 (추가)
  pinMode(JOY_SW_PIN, INPUT_PULLUP);

  // 초기 위치 설정
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoGrip.write((int)angleGrip); // 집게를 90도로 초기화

  Serial.begin(9600);
}

void loop() {
  // 조이스틱 아날로그 값 읽기
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);

  Serial.println(yVal);

  // 1. 좌우 서보모터 제어 (기존 코드)
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  }
  else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }

  // 2. 상하 서보모터 제어 (기존 코드)
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  }
  else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  // 각도 한계값 제한 (기존 코드)
  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);

  // 서보모터에 각도 전달 (기존 코드)
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  // =====================================
  // 3. 집게 서보모터 제어 (추가)
  // =====================================

  buttonState = digitalRead(JOY_SW_PIN);

  // 버튼을 새롭게 눌렀을 때만 동작 변경
  // INPUT_PULLUP이므로 눌림 상태는 LOW
  if (buttonState == LOW && lastButtonState == HIGH) {

    if (gripMode == 0) {
      // 정지 상태에서 누르면 좁히기 시작
      gripMode = 1;
    }
    else if (gripMode == 1) {
      // 좁히는 중 누르면 정지
      gripMode = 0;
    }
    else if (gripMode == -1) {
      // 푸는 중 누르면 정지
      gripMode = 0;
    }
  }

  // 다음 반복에서 버튼 상태 비교용
  lastButtonState = buttonState;

  // 집게 각도 변경
  if (gripMode == 1) {
    // 집게 좁히기
    angleGrip -= GRIP_STEP_SIZE;

    // 좁히기 끝에 도달하면 정지
    if (angleGrip <= MIN_GRIP) {
      angleGrip = MIN_GRIP;
      gripMode = 0;
    }
  }
  else if (gripMode == 0) {
    // 정지 상태에서 다음 동작을 결정하기 위한 처리
    // 아래의 별도 변수로 방향을 관리
  }

  // 집게 서보모터에 각도 전달
  angleGrip = constrain(angleGrip, MIN_GRIP, MAX_GRIP);
  servoGrip.write((int)angleGrip);

  delay(15);
}

#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A0;
const int JOY_Y_PIN = A1;
const int JOY_SW_PIN = A2;

const int SERVO_LR_PIN = 9;
const int SERVO_UD_PIN = 10;
const int SERVO_GRIP_PIN = 11;

// 서보모터 객체
Servo servoLR;
Servo servoUD;
Servo servoGrip;

// 현재 각도
float angleLR = 90.0;
float angleUD = 90.0;
float angleGrip = 120.0;

// 좌우 및 상하 각도 제한
const float MIN_LR = 0.0;
const float MAX_LR = 180.0;

const float MIN_UD = 0.0;
const float MAX_UD = 180.0;

// 집게 각도 설정
const float OPEN_ANGLE = 70.0;   // 열기
const float CLOSE_ANGLE = 105.0; // 잡기(닫기)

// 이동 속도
const float STEP_SIZE = 0.5;
const float GRIP_STEP_SIZE = 1;

// 집게 상태: false = 닫힘, true = 열림
bool isOpen = false;

int lastButtonState = HIGH;
int buttonState = HIGH;

void setup() {
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);
  servoGrip.attach(SERVO_GRIP_PIN);

  pinMode(JOY_SW_PIN, INPUT_PULLUP);

  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoGrip.write((int)angleGrip);

  Serial.begin(9600);
}

void loop() {
  // 조이스틱 값 읽기
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);

  // 1. 좌우 제어
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  } else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }

  // 2. 상하 제어
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  } else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);

  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  // 3. 집게 버튼 입력
  buttonState = digitalRead(JOY_SW_PIN);

  // 버튼을 누르는 순간 열기/닫기 전환
  if (buttonState == LOW && lastButtonState == HIGH) {
    isOpen = !isOpen;

    Serial.print("집게 상태: ");
    Serial.println(isOpen ? "열기" : "닫기");
  }

  lastButtonState = buttonState;

  // 4. 집게를 목표 각도까지 부드럽게 이동
  if (isOpen) {
    // 열기: 70도
    if (angleGrip > OPEN_ANGLE) {
      angleGrip -= GRIP_STEP_SIZE;
    }
  } else {
    // 잡기(닫기): 120도
    if (angleGrip < CLOSE_ANGLE) {
      angleGrip += GRIP_STEP_SIZE;
    }
  }

  angleGrip = constrain(angleGrip, OPEN_ANGLE, CLOSE_ANGLE);
  servoGrip.write((int)angleGrip);

  delay(15);
}

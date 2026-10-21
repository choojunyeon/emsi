#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A1;   // 조이스틱 좌우 (X축)
const int JOY_Y_PIN = A0;   // 조이스틱 상하 (Y축)
const int JOY_SW_PIN = 2;   // 조이스틱 버튼 (SW)

const int SERVO_LR_PIN = 9;   // 좌우 서보모터
const int SERVO_UD_PIN = 10;  // 상하 서보모터
const int SERVO_GRIP_PIN = 11;// 집게 서보모터#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A0;   // 조이스틱 좌우 (X축)
const int JOY_Y_PIN = A1;   // 조이스틱 상하 (Y축)
const int JOY_SW_PIN = A2;   // 조이스틱 버튼 (SW)

const int SERVO_LR_PIN = 9;   // 좌우 서보모터
const int SERVO_UD_PIN = 10;  // 상하 서보모터
const int SERVO_GRIP_PIN = 11;// 집게 서보모터

// 서보모터 객체
Servo servoLR;
Servo servoUD;
Servo servoGrip;

// 서보모터 현재 각도 변수 (초기값: 중앙)
float angleLR = 90.0;
float angleUD = 90.0;
float angleGrip = 90.0; // 집게 초기 각도

// 각도 제한
const float MIN_LR = 0.0;
const float MAX_LR = 180.0; 

const float MIN_UD = 0.0;
const float MAX_UD = 180.0;

// 집게 각도 제한 (0도: 닫힘 / 180도: 열림)
const float MIN_GRIP = 30.0;   // 닫혔을 때 각도
const float MAX_GRIP = 120.0; // 열렸을 때 각도

// 조이스틱 감도 및 집게 이동 속도
const float STEP_SIZE = 0.5;
const float GRIP_STEP_SIZE = 2.0; // 집게가 열리고 닫히는 속도

// 집게 상태 변수 (false = 닫힘 / true = 열림)
bool isOpen = false; 

// 버튼 디바운스 및 edge detection용 변수
int lastButtonState = HIGH;
int buttonState = HIGH;

void setup() {
  // 서보모터 핀 연결
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);
  servoGrip.attach(SERVO_GRIP_PIN);

  // PS2 조이스틱 버튼 설정
  pinMode(JOY_SW_PIN, INPUT_PULLUP);

  // 초기 위치 설정
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoGrip.write((int)angleGrip);

  Serial.begin(9600);
}

void loop() {
  // 조이스틱 아날로그 값 읽기
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);

 

  // 1. 좌우 서보모터 제어
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  }
  else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }

  // 2. 상하 서보모터 제어
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  }
  else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  // 각도 한계값 제한
  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);

  // 서보모터에 각도 전달
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  // =====================================
  // 3. 집게 서보모터 토글 제어 (수정됨)
  // =====================================
  // 집게 버튼 입력
buttonState = digitalRead(JOY_SW_PIN);

// 버튼을 누르는 순간 감지
if (buttonState == LOW && lastButtonState == HIGH) {
  isOpen = !isOpen;

  Serial.print("집게 상태: ");
  Serial.println(isOpen ? "열기" : "닫기");
}

lastButtonState = buttonState;
  

  // isOpen 상태에 따라 목표 각도로 부드럽게 이동
  if (isOpen) {
    // 열기 (MAX_GRIP 향해 각도 증가)
    if (angleGrip < MAX_GRIP) {
      angleGrip += GRIP_STEP_SIZE;
    }
  } else {
    // 닫기 (MIN_GRIP 향해 각도 감소)
    if (angleGrip > MIN_GRIP) {
      angleGrip -= GRIP_STEP_SIZE;
    }
  }

  // 집게 서보모터에 각도 전달
  angleGrip = constrain(angleGrip, MIN_GRIP, MAX_GRIP);
  servoGrip.write((int)angleGrip);

  delay(15);
}

// 서보모터 객체
Servo servoLR;
Servo servoUD;
Servo servoGrip;

// 서보모터 현재 각도 변수 (초기값: 중앙)
float angleLR = 90.0;
float angleUD = 90.0;
float angleGrip = 90.0; // 집게 초기 각도

// 각도 제한
const float MIN_LR = 60.0;
const float MAX_LR = 120.0;

const float MIN_UD = 0.0;
const float MAX_UD = 180.0;

// 집게 각도 제한 (0도: 닫힘 / 180도: 열림)
const float MIN_GRIP = 0.0;   // 닫혔을 때 각도
const float MAX_GRIP = 180.0; // 열렸을 때 각도

// 조이스틱 감도 및 집게 이동 속도
const float STEP_SIZE = 0.5;
const float GRIP_STEP_SIZE = 2.0; // 집게가 열리고 닫히는 속도

// 집게 상태 변수 (false = 닫힘 / true = 열림)
bool isOpen = false; 

// 버튼 디바운스 및 edge detection용 변수
int lastButtonState = HIGH;
int buttonState = HIGH;

void setup() {
  // 서보모터 핀 연결
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);
  servoGrip.attach(SERVO_GRIP_PIN);

  // PS2 조이스틱 버튼 설정
  pinMode(JOY_SW_PIN, INPUT_PULLUP);

  // 초기 위치 설정
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);
  servoGrip.write((int)angleGrip);

  Serial.begin(9600);
}

void loop() {
  // 조이스틱 아날로그 값 읽기
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);

  Serial.println(yVal);

  // 1. 좌우 서보모터 제어
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  }
  else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }

  // 2. 상하 서보모터 제어
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  }
  else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  // 각도 한계값 제한
  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);

  // 서보모터에 각도 전달
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  // =====================================
  // 3. 집게 서보모터 토글 제어 (수정됨)
  // =====================================
  buttonState = digitalRead(JOY_SW_PIN);

  // 버튼을 눌렀을 때 순간 감지 (HIGH -> LOW)
  if (buttonState == LOW && lastButtonState == HIGH) {
    isOpen = !isOpen; // 누를 때마다 열림/닫힘 상태 전환
  }
  lastButtonState = buttonState;

  // isOpen 상태에 따라 목표 각도로 부드럽게 이동
  if (isOpen) {
    // 열기 (MAX_GRIP 향해 각도 증가)
    if (angleGrip < MAX_GRIP) {
      angleGrip += GRIP_STEP_SIZE;
    }
  } else {
    // 닫기 (MIN_GRIP 향해 각도 감소)
    if (angleGrip > MIN_GRIP) {
      angleGrip -= GRIP_STEP_SIZE;
    }
  }

  // 집게 서보모터에 각도 전달
  angleGrip = constrain(angleGrip, MIN_GRIP, MAX_GRIP);
  servoGrip.write((int)angleGrip);

  delay(15);
}

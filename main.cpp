#include <Servo.h>

// 핀 설정
const int JOY_X_PIN = A1;   // 조이스틱 좌우 (X축)
const int JOY_Y_PIN = A0;   // 조이스틱 상하 (Y축)
const int SERVO_LR_PIN = 9;  // 좌우 서보모터
const int SERVO_UD_PIN = 10; // 상하 서보모터

Servo servoLR; // 좌우 서보모터 객체
Servo servoUD; // 상하 서보모터 객체

// 서보모터 현재 각도 변수 (초기값: 중앙)
float angleLR = 90.0;
float angleUD = 90.0;

// 각도 제한 (범위 설정)
// 1. 좌우 서보: 기준(90도)에서 ±30도 -> 60도 ~ 120도
const float MIN_LR = 60.0;  // 왼쪽 최대 (90 - 30)
const float MAX_LR = 120.0; // 오른쪽 최대 (90 + 30)

// 2. 상하 서보: 기준(90도)에서 ±90도 -> 0도 ~ 180도
const float MIN_UD = 0.0;   // 위쪽 최대 (90 - 90)
const float MAX_UD = 180.0; // 아래쪽 최대 (90 + 90)

// 조이스틱 감도 설정 (조이스틱을 밀 때 각도가 변하는 속도)
const float STEP_SIZE = 0.5; 

void setup() {
  // 서보모터 핀 연결
  servoLR.attach(SERVO_LR_PIN);
  servoUD.attach(SERVO_UD_PIN);

  // 초기 위치 설정 (중앙 90도)
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  Serial.begin(9600); // 통신 속도를 9600bps로 설정합니다.

}

void loop() {
  // 조이스틱 아날로그 값 읽기 (0 ~ 1023, 중립 약 512)
  int xVal = analogRead(JOY_X_PIN);
  int yVal = analogRead(JOY_Y_PIN);

  Serial.println(yVal);      // 값 출력 후 줄바꿈
  //Serial.println(yVal);      // 값 출력 후 줄바꿈



  // 1. 좌우 서보모터 제어
  // 조이스틱을 왼쪽으로 밀었을 때 (X값 감소)
  if (xVal < 400) {
    angleLR -= STEP_SIZE;
  } 
  // 조이스틱을 오른쪽으로 밀었을 때 (X값 증가)
  else if (xVal > 600) {
    angleLR += STEP_SIZE;
  }
  // (400 ~ 600 사이 중립 구간일 때는 angleLR 값이 유지되어 모터가 멈춤)

  // 2. 상하 서보모터 제어
  // 조이스틱을 위로 밀었을 때 (Y값 감소) -> 모터는 왼쪽 방향(각도 감소)으로 움직임
  if (yVal < 400) {
    angleUD -= STEP_SIZE;
  } 
  // 조이스틱을 아래로 밀었을 때 (Y값 증가) -> 모터는 오른쪽 방향(각도 증가)으로 움직임
  else if (yVal > 600) {
    angleUD += STEP_SIZE;
  }

  // 각도 한계값 제한 (최대 범위를 벗어나지 않도록 고정)
  angleLR = constrain(angleLR, MIN_LR, MAX_LR);
  angleUD = constrain(angleUD, MIN_UD, MAX_UD);

  // 서보모터에 계산된 각도 전달
  servoLR.write((int)angleLR);
  servoUD.write((int)angleUD);

  // 모터 동작 속도 제어용 딜레이 (ms)
  delay(15); 
}

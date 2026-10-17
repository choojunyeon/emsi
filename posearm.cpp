#include <Servo.h>

// ==========================================
// 1. 서보모터 설정
// ==========================================

Servo servoLR;    // 좌우 회전
Servo servoUD;    // 상하 이동
Servo servoGrip;  // 집게 개폐

const int PIN_LR = 9;
const int PIN_UD = 10;
const int PIN_GRIP = 11;

// 현재 각도
int angleLR = 90;
int angleUD = 90;
int angleGrip = 90;

// 파이썬에서 전달받을 문자열
String receivedData = "";

// ==========================================
// 2. 초기 설정
// ==========================================

void setup() {
  // 서보모터 연결
  servoLR.attach(PIN_LR);
  servoUD.attach(PIN_UD);
  servoGrip.attach(PIN_GRIP);

  // 시작 각도 설정
  servoLR.write(angleLR);
  servoUD.write(angleUD);
  servoGrip.write(angleGrip);

  // 파이썬과 USB 시리얼 통신 시작
  Serial.begin(9600);

  // 초기 각도로 이동할 시간
  delay(500);
}

// ==========================================
// 3. 반복 실행
// ==========================================

void loop() {
  // 파이썬에서 한 줄의 데이터가 도착했는지 확인
  while (Serial.available() > 0) {
    char receivedChar = Serial.read();

    // 줄바꿈 문자를 받으면 데이터 처리
    if (receivedChar == '\n') {
      processData(receivedData);
      receivedData = "";
    }
    // 줄바꿈 전까지 문자열에 추가
    else if (receivedChar != '\r') {
      receivedData += receivedChar;

      // 비정상적으로 긴 문자열 방지
      if (receivedData.length() > 50) {
        receivedData = "";
      }
    }
  }
}

// ==========================================
// 4. 파이썬 데이터 처리
// ==========================================

void processData(String data) {
  int firstComma = data.indexOf(',');
  int secondComma = data.indexOf(',', firstComma + 1);

  // 쉼표가 2개가 아니면 잘못된 데이터
  if (firstComma < 0 || secondComma < 0) {
    return;
  }

  // 좌우, 상하, 집게 각도 분리
  int newLR = data.substring(0, firstComma).toInt();

  int newUD = data.substring(
    firstComma + 1, secondComma
  ).toInt();

  int newGrip = data.substring(
    secondComma + 1
  ).toInt();

  // 서보모터 안전 범위로 제한
  newLR = constrain(newLR, 0, 180);
  newUD = constrain(newUD, 0, 180);
  newGrip = constrain(newGrip, 0, 180);

  // 목표 각도 적용
  angleLR = newLR;
  angleUD = newUD;
  angleGrip = newGrip;

  servoLR.write(angleLR);
  servoUD.write(angleUD);
  servoGrip.write(angleGrip);
}

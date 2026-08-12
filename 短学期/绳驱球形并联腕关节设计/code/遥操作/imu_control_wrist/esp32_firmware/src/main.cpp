#include <Arduino.h>

#include <cmath>

#include "config.h"
#include "imu_source.h"
#include "protocol.h"
#include "servo_bus.h"

namespace {

HardwareSerial servoUart(SERVO_UART_NUMBER);
ServoBus servoBus(servoUart);
ImuSource imu;
wrist_protocol::FrameParser hostParser;

uint16_t imuSequence = 0;
uint16_t statusSequence = 0;
uint32_t lastImuRetryMs = 0;

wrist_protocol::SensorState currentImuState() {
  if (imu.ready()) {
    return wrist_protocol::SENSOR_RESPONDING;
  }
  return imu.calibrationUnstable()
             ? wrist_protocol::SENSOR_CALIBRATION_MOVING
             : wrist_protocol::SENSOR_NO_RESPONSE;
}

void sendSensorStatus(wrist_protocol::SensorState state) {
  constexpr uint8_t SENSOR_ID_IMU = 1;
  const uint8_t payload[2] = {SENSOR_ID_IMU, static_cast<uint8_t>(state)};
  wrist_protocol::sendFrame(Serial, wrist_protocol::TYPE_SENSOR_STATUS,
                            ++statusSequence, payload, sizeof(payload));
}

void sendRpy(const RpyDegrees &rpy) {
  uint8_t payload[wrist_protocol::ANGLE_PAYLOAD_LENGTH] = {};
  wrist_protocol::writeI32Le(&payload[0], lroundf(rpy.yaw * 1000.0F));
  wrist_protocol::writeI32Le(&payload[4], lroundf(rpy.pitch * 1000.0F));
  wrist_protocol::writeI32Le(&payload[8], lroundf(rpy.roll * 1000.0F));
  wrist_protocol::sendFrame(Serial, wrist_protocol::TYPE_IMU_RPY,
                            ++imuSequence, payload, sizeof(payload));
}

void handleHostFrame(const wrist_protocol::Frame &frame) {
  if (frame.type != wrist_protocol::TYPE_SET_WRIST_TARGET) {
    wrist_protocol::sendAck(Serial, frame.sequence, frame.type,
                            wrist_protocol::ACK_UNSUPPORTED_TYPE);
    return;
  }
  if (frame.payloadLength != wrist_protocol::ANGLE_PAYLOAD_LENGTH) {
    wrist_protocol::sendAck(Serial, frame.sequence, frame.type,
                            wrist_protocol::ACK_BAD_LENGTH);
    return;
  }

  float theta[SERVO_COUNT] = {};
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    theta[i] = wrist_protocol::readI32Le(&frame.payload[i * 4]) / 1000.0F;
  }

  const ServoTargetStatus status = servoBus.setThetaDegrees(theta);
  wrist_protocol::AckStatus ackStatus = wrist_protocol::ACK_OK;
  if (status == ServoTargetStatus::OUT_OF_RANGE) {
    ackStatus = wrist_protocol::ACK_OUT_OF_RANGE;
  } else if (status == ServoTargetStatus::UNSAFE_AXIS_ORDER) {
    ackStatus = wrist_protocol::ACK_UNSAFE_AXIS_ORDER;
  }
  wrist_protocol::sendAck(Serial, frame.sequence, frame.type, ackStatus);
}

void receiveHostFrames() {
  wrist_protocol::Frame frame;
  while (Serial.available() > 0) {
    if (hostParser.feed(static_cast<uint8_t>(Serial.read()), frame)) {
      handleHostFrame(frame);
    }
  }
}

void serviceImu() {
  if (!imu.ready()) {
    const uint32_t now = millis();
    if (now - lastImuRetryMs >= IMU_RETRY_INTERVAL_MS) {
      lastImuRetryMs = now;
      imu.begin();
      sendSensorStatus(currentImuState());
    }
    return;
  }

  RpyDegrees rpy;
  if (imu.read(rpy)) {
    sendRpy(rpy);
  }
}

}  // namespace

void setup() {
  Serial.begin(HOST_BAUDRATE);
  servoBus.begin();
  delay(100);

  const bool imuReady = imu.begin();
  (void)imuReady;
  sendSensorStatus(currentImuState());
  lastImuRetryMs = millis();
}

void loop() {
  receiveHostFrames();
  serviceImu();
}

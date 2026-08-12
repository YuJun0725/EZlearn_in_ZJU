#pragma once

#include <Arduino.h>

namespace wrist_protocol {

constexpr uint8_t SOF_LOW = 0x55;
constexpr uint8_t SOF_HIGH = 0xAA;
constexpr uint8_t TYPE_ACK = 0x02;
constexpr uint8_t TYPE_SET_WRIST_TARGET = 0x20;
constexpr uint8_t TYPE_SENSOR_STATUS = 0x30;
constexpr uint8_t TYPE_IMU_RPY = 0x31;

constexpr uint16_t ANGLE_PAYLOAD_LENGTH = 12;
constexpr uint16_t MAX_PAYLOAD_LENGTH = 32;
constexpr uint8_t BODY_HEADER_LENGTH = 5;  // type, sequence, payload length

enum AckStatus : uint8_t {
  ACK_OK = 0,
  ACK_BAD_LENGTH = 1,
  ACK_UNSUPPORTED_TYPE = 2,
  ACK_OUT_OF_RANGE = 3,
  ACK_UNSAFE_AXIS_ORDER = 4,
};

enum SensorState : uint8_t {
  SENSOR_NO_RESPONSE = 0,
  SENSOR_RESPONDING = 1,
  SENSOR_BUS_ERROR = 2,
  SENSOR_CALIBRATION_MOVING = 3,
};

struct Frame {
  uint8_t type = 0;
  uint16_t sequence = 0;
  uint16_t payloadLength = 0;
  uint8_t payload[MAX_PAYLOAD_LENGTH] = {};
};

uint16_t crc16CcittFalse(const uint8_t *data, uint16_t length);
uint16_t readU16Le(const uint8_t *data);
int32_t readI32Le(const uint8_t *data);
void writeI32Le(uint8_t *data, int32_t value);

void sendFrame(HardwareSerial &serial, uint8_t type, uint16_t sequence,
               const uint8_t *payload, uint16_t payloadLength);
void sendAck(HardwareSerial &serial, uint16_t sequence, uint8_t originalType,
             AckStatus status);

class FrameParser {
 public:
  bool feed(uint8_t byte, Frame &frame);

 private:
  enum State : uint8_t {
    WAIT_SOF_LOW,
    WAIT_SOF_HIGH,
    READ_HEADER,
    READ_PAYLOAD,
    READ_CRC_LOW,
    READ_CRC_HIGH,
  };

  void reset();
  bool finish(Frame &frame);

  State state_ = WAIT_SOF_LOW;
  uint8_t body_[BODY_HEADER_LENGTH + MAX_PAYLOAD_LENGTH] = {};
  uint16_t bodyLength_ = 0;
  uint16_t expectedBodyLength_ = 0;
  uint16_t payloadLength_ = 0;
  uint16_t receivedCrc_ = 0;
};

}  // namespace wrist_protocol

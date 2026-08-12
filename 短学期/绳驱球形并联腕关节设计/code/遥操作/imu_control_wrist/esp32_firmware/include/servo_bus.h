#pragma once

#include <Arduino.h>

#include "config.h"

enum class ServoTargetStatus : uint8_t {
  ACCEPTED,
  OUT_OF_RANGE,
  UNSAFE_AXIS_ORDER,
};

class ServoBus {
 public:
  explicit ServoBus(HardwareSerial &serial) : serial_(serial) {}

  void begin();
  ServoTargetStatus setThetaDegrees(const float thetaDeg[SERVO_COUNT]);
  void setZero();

 private:
  void sendPacket(uint8_t id, uint8_t instruction, const uint8_t *params,
                  uint8_t paramLength);
  void writeByte(uint8_t id, uint8_t address, uint8_t value);
  void writeWord(uint8_t id, uint8_t address, uint16_t value);
  void syncWritePositions(const uint16_t position[SERVO_COUNT]);
  bool thetaToPosition(size_t index, float thetaDeg, uint16_t &position) const;
  bool axisOrderIsSafe(const float thetaDeg[SERVO_COUNT]) const;

  HardwareSerial &serial_;
};

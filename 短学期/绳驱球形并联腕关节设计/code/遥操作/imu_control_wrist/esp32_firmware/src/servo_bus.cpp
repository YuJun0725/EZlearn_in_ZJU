#include "servo_bus.h"

#include <cmath>

namespace {

constexpr uint8_t BROADCAST_ID = 0xFE;
constexpr uint8_t INSTRUCTION_WRITE = 0x03;
constexpr uint8_t INSTRUCTION_SYNC_WRITE = 0x83;
constexpr uint8_t ADDRESS_TORQUE_ENABLE = 40;
constexpr uint8_t ADDRESS_ACCELERATION = 41;
constexpr uint8_t ADDRESS_GOAL_POSITION = 42;
constexpr uint8_t ADDRESS_SPEED = 46;
constexpr float COUNTS_PER_DEGREE = 4096.0F / 360.0F;

float wrapTo360(float angle) {
  angle = fmodf(angle, 360.0F);
  return angle < 0.0F ? angle + 360.0F : angle;
}

}  // namespace

void ServoBus::sendPacket(uint8_t id, uint8_t instruction,
                          const uint8_t *params, uint8_t paramLength) {
  const uint8_t length = paramLength + 2;
  uint16_t sum = id + length + instruction;

  serial_.write(0xFF);
  serial_.write(0xFF);
  serial_.write(id);
  serial_.write(length);
  serial_.write(instruction);
  for (uint8_t i = 0; i < paramLength; ++i) {
    serial_.write(params[i]);
    sum += params[i];
  }
  serial_.write(static_cast<uint8_t>(~sum));
}

void ServoBus::writeByte(uint8_t id, uint8_t address, uint8_t value) {
  const uint8_t params[] = {address, value};
  sendPacket(id, INSTRUCTION_WRITE, params, sizeof(params));
}

void ServoBus::writeWord(uint8_t id, uint8_t address, uint16_t value) {
  const uint8_t params[] = {
      address,
      static_cast<uint8_t>(value & 0xFF),
      static_cast<uint8_t>((value >> 8) & 0xFF),
  };
  sendPacket(id, INSTRUCTION_WRITE, params, sizeof(params));
}

void ServoBus::begin() {
  serial_.begin(SERVO_BAUDRATE, SERIAL_8N1, SERVO_RX_PIN, SERVO_TX_PIN);
  delay(100);
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    writeByte(SERVO_IDS[i], ADDRESS_TORQUE_ENABLE, 1);
    delay(3);
    writeByte(SERVO_IDS[i], ADDRESS_ACCELERATION, SERVO_ACCELERATION);
    delay(3);
    writeWord(SERVO_IDS[i], ADDRESS_SPEED, SERVO_SPEED);
    delay(3);
  }
  if (MOVE_TO_ZERO_ON_BOOT) {
    setZero();
  }
}

bool ServoBus::thetaToPosition(size_t index, float thetaDeg,
                               uint16_t &position) const {
  if (!std::isfinite(thetaDeg) || thetaDeg < SERVO_MIN_THETA_DEG[index] ||
      thetaDeg > SERVO_MAX_THETA_DEG[index]) {
    return false;
  }

  const float calibratedTheta = thetaDeg + SERVO_ZERO_OFFSET_DEG[index];
  const long raw = lroundf(
      SERVO_CENTER[index] +
      SERVO_THETA_SIGN[index] * calibratedTheta *
          SERVO_GEAR_RATIO[index] * COUNTS_PER_DEGREE);
  if (raw < 0 || raw > 4095) {
    return false;
  }
  position = static_cast<uint16_t>(raw);
  return true;
}

void ServoBus::syncWritePositions(const uint16_t position[SERVO_COUNT]) {
  constexpr uint8_t DATA_LENGTH = 2;
  uint8_t params[2 + SERVO_COUNT * (1 + DATA_LENGTH)] = {};
  params[0] = ADDRESS_GOAL_POSITION;
  params[1] = DATA_LENGTH;
  uint8_t cursor = 2;
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    params[cursor++] = SERVO_IDS[i];
    params[cursor++] = static_cast<uint8_t>(position[i] & 0xFF);
    params[cursor++] = static_cast<uint8_t>((position[i] >> 8) & 0xFF);
  }
  sendPacket(BROADCAST_ID, INSTRUCTION_SYNC_WRITE, params, sizeof(params));
}

bool ServoBus::axisOrderIsSafe(const float thetaDeg[SERVO_COUNT]) const {
  // Initial cyclic order for azimuths [0, 120, -120] is leg 3 -> 1 -> 2.
  constexpr size_t ORDER[SERVO_COUNT] = {2, 0, 1};
  float azimuths[SERVO_COUNT] = {};
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    azimuths[i] = wrapTo360(SERVO_BASE_AZIMUTH_DEG[i] + thetaDeg[i]);
  }

  float gapSum = 0.0F;
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    const size_t current = ORDER[i];
    const size_t following = ORDER[(i + 1) % SERVO_COUNT];
    const float gap = wrapTo360(azimuths[following] - azimuths[current]);
    if (gap <= MIN_AXIS_CLEARANCE_DEG) {
      return false;
    }
    gapSum += gap;
  }

  // Correct cyclic order winds around the circle exactly once. A changed
  // order makes these three directed gaps wind around twice (720 degrees).
  return fabsf(gapSum - 360.0F) < 0.01F;
}

ServoTargetStatus ServoBus::setThetaDegrees(
    const float thetaDeg[SERVO_COUNT]) {
  uint16_t positions[SERVO_COUNT] = {};
  for (size_t i = 0; i < SERVO_COUNT; ++i) {
    if (!thetaToPosition(i, thetaDeg[i], positions[i])) {
      return ServoTargetStatus::OUT_OF_RANGE;
    }
  }
  if (!axisOrderIsSafe(thetaDeg)) {
    return ServoTargetStatus::UNSAFE_AXIS_ORDER;
  }
  syncWritePositions(positions);
  return ServoTargetStatus::ACCEPTED;
}

void ServoBus::setZero() {
  const float zero[SERVO_COUNT] = {0.0F, 0.0F, 0.0F};
  setThetaDegrees(zero);
}

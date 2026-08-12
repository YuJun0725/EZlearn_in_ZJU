#include "protocol.h"

#include <cstring>

namespace wrist_protocol {

uint16_t crc16CcittFalse(const uint8_t *data, uint16_t length) {
  uint16_t crc = 0xFFFF;
  for (uint16_t i = 0; i < length; ++i) {
    crc ^= static_cast<uint16_t>(data[i]) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc & 0x8000)
                ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

uint16_t readU16Le(const uint8_t *data) {
  return static_cast<uint16_t>(data[0]) |
         (static_cast<uint16_t>(data[1]) << 8);
}

int32_t readI32Le(const uint8_t *data) {
  const uint32_t value = static_cast<uint32_t>(data[0]) |
                         (static_cast<uint32_t>(data[1]) << 8) |
                         (static_cast<uint32_t>(data[2]) << 16) |
                         (static_cast<uint32_t>(data[3]) << 24);
  return static_cast<int32_t>(value);
}

void writeI32Le(uint8_t *data, int32_t value) {
  const uint32_t raw = static_cast<uint32_t>(value);
  data[0] = static_cast<uint8_t>(raw & 0xFF);
  data[1] = static_cast<uint8_t>((raw >> 8) & 0xFF);
  data[2] = static_cast<uint8_t>((raw >> 16) & 0xFF);
  data[3] = static_cast<uint8_t>((raw >> 24) & 0xFF);
}

void sendFrame(HardwareSerial &serial, uint8_t type, uint16_t sequence,
               const uint8_t *payload, uint16_t payloadLength) {
  if (payloadLength > MAX_PAYLOAD_LENGTH) {
    return;
  }

  uint8_t body[BODY_HEADER_LENGTH + MAX_PAYLOAD_LENGTH] = {};
  body[0] = type;
  body[1] = static_cast<uint8_t>(sequence & 0xFF);
  body[2] = static_cast<uint8_t>((sequence >> 8) & 0xFF);
  body[3] = static_cast<uint8_t>(payloadLength & 0xFF);
  body[4] = static_cast<uint8_t>((payloadLength >> 8) & 0xFF);
  if (payloadLength > 0 && payload != nullptr) {
    memcpy(&body[BODY_HEADER_LENGTH], payload, payloadLength);
  }

  const uint16_t bodyLength = BODY_HEADER_LENGTH + payloadLength;
  const uint16_t crc = crc16CcittFalse(body, bodyLength);
  serial.write(SOF_LOW);
  serial.write(SOF_HIGH);
  serial.write(body, bodyLength);
  serial.write(static_cast<uint8_t>(crc & 0xFF));
  serial.write(static_cast<uint8_t>((crc >> 8) & 0xFF));
}

void sendAck(HardwareSerial &serial, uint16_t sequence, uint8_t originalType,
             AckStatus status) {
  const uint8_t payload[2] = {originalType, static_cast<uint8_t>(status)};
  sendFrame(serial, TYPE_ACK, sequence, payload, sizeof(payload));
}

void FrameParser::reset() {
  state_ = WAIT_SOF_LOW;
  bodyLength_ = 0;
  expectedBodyLength_ = 0;
  payloadLength_ = 0;
  receivedCrc_ = 0;
}

bool FrameParser::finish(Frame &frame) {
  if (crc16CcittFalse(body_, bodyLength_) != receivedCrc_) {
    return false;
  }

  frame.type = body_[0];
  frame.sequence = readU16Le(&body_[1]);
  frame.payloadLength = payloadLength_;
  if (payloadLength_ > 0) {
    memcpy(frame.payload, &body_[BODY_HEADER_LENGTH], payloadLength_);
  }
  return true;
}

bool FrameParser::feed(uint8_t byte, Frame &frame) {
  switch (state_) {
    case WAIT_SOF_LOW:
      if (byte == SOF_LOW) {
        state_ = WAIT_SOF_HIGH;
      }
      break;

    case WAIT_SOF_HIGH:
      if (byte == SOF_HIGH) {
        bodyLength_ = 0;
        state_ = READ_HEADER;
      } else if (byte != SOF_LOW) {
        state_ = WAIT_SOF_LOW;
      }
      break;

    case READ_HEADER:
      body_[bodyLength_++] = byte;
      if (bodyLength_ == BODY_HEADER_LENGTH) {
        payloadLength_ = readU16Le(&body_[3]);
        if (payloadLength_ > MAX_PAYLOAD_LENGTH) {
          reset();
        } else {
          expectedBodyLength_ = BODY_HEADER_LENGTH + payloadLength_;
          state_ = payloadLength_ == 0 ? READ_CRC_LOW : READ_PAYLOAD;
        }
      }
      break;

    case READ_PAYLOAD:
      body_[bodyLength_++] = byte;
      if (bodyLength_ == expectedBodyLength_) {
        state_ = READ_CRC_LOW;
      }
      break;

    case READ_CRC_LOW:
      receivedCrc_ = byte;
      state_ = READ_CRC_HIGH;
      break;

    case READ_CRC_HIGH: {
      receivedCrc_ |= static_cast<uint16_t>(byte) << 8;
      const bool valid = finish(frame);
      reset();
      return valid;
    }
  }
  return false;
}

}  // namespace wrist_protocol


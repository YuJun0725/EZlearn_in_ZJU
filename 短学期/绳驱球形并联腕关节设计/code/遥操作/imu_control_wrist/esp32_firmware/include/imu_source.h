#pragma once

#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <Arduino.h>

struct RpyDegrees {
  float yaw = 0.0F;
  float pitch = 0.0F;
  float roll = 0.0F;
};

class ImuSource {
 public:
  bool begin();
  bool read(RpyDegrees &rpy);
  bool ready() const { return ready_; }
  bool calibrationUnstable() const { return calibrationUnstable_; }

 private:
  bool calibrateGyro();
  static void mapSensorAxes(float x, float y, float z, float output[3]);
  void expectedGravityInBody(float output[3]) const;
  void updateQuaternion(const float bodyRate[3], float dt);
  RpyDegrees relativeQuaternionToRpy() const;

  Adafruit_MPU6050 mpu_;
  bool ready_ = false;
  bool calibrationUnstable_ = false;
  uint32_t lastSampleMicros_ = 0;
  float gyroBiasRadS_[3] = {};
  float referenceGravity_[3] = {0.0F, 0.0F, 1.0F};
  float referenceAccelMagnitude_ = 9.81F;
  float quaternion_[4] = {1.0F, 0.0F, 0.0F, 0.0F};  // w, x, y, z
};

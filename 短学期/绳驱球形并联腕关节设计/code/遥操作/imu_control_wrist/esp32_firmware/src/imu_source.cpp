#include "imu_source.h"

#include <Wire.h>

#include <algorithm>
#include <cmath>

#include "config.h"

namespace {

constexpr float RAD_TO_DEG_F = 180.0F / PI;

float wrapDegrees(float angle) {
  while (angle >= 180.0F) {
    angle -= 360.0F;
  }
  while (angle < -180.0F) {
    angle += 360.0F;
  }
  return angle;
}

float clampValue(float value, float lower, float upper) {
  return std::max(lower, std::min(upper, value));
}

}  // namespace

void ImuSource::mapSensorAxes(float x, float y, float z, float output[3]) {
  const float sensor[3] = {x, y, z};
  for (size_t i = 0; i < 3; ++i) {
    output[i] = IMU_AXIS_SIGN[i] * sensor[IMU_AXIS_MAP[i]];
  }
}

bool ImuSource::calibrateGyro() {
  float gyroSum[3] = {};
  float gyroSquareSum[3] = {};
  float accelSum[3] = {};
  float accelMagnitudeSum = 0.0F;
  float accelMagnitudeSquareSum = 0.0F;
  sensors_event_t acceleration;
  sensors_event_t gyro;
  sensors_event_t temperature;

  for (uint16_t sample = 0; sample < IMU_GYRO_CALIBRATION_SAMPLES; ++sample) {
    if (!mpu_.getEvent(&acceleration, &gyro, &temperature)) {
      return false;
    }

    float bodyGyro[3] = {};
    float bodyAccel[3] = {};
    mapSensorAxes(gyro.gyro.x, gyro.gyro.y, gyro.gyro.z, bodyGyro);
    mapSensorAxes(acceleration.acceleration.x, acceleration.acceleration.y,
                  acceleration.acceleration.z, bodyAccel);
    for (size_t axis = 0; axis < 3; ++axis) {
      gyroSum[axis] += bodyGyro[axis];
      gyroSquareSum[axis] += bodyGyro[axis] * bodyGyro[axis];
      accelSum[axis] += bodyAccel[axis];
    }
    const float accelMagnitude =
        sqrtf(bodyAccel[0] * bodyAccel[0] + bodyAccel[1] * bodyAccel[1] +
              bodyAccel[2] * bodyAccel[2]);
    accelMagnitudeSum += accelMagnitude;
    accelMagnitudeSquareSum += accelMagnitude * accelMagnitude;
    delay(2);
  }

  calibrationUnstable_ = false;
  float gyroMeanMagnitudeSquared = 0.0F;
  for (size_t axis = 0; axis < 3; ++axis) {
    gyroBiasRadS_[axis] = gyroSum[axis] / IMU_GYRO_CALIBRATION_SAMPLES;
    referenceGravity_[axis] = accelSum[axis] / IMU_GYRO_CALIBRATION_SAMPLES;
    gyroMeanMagnitudeSquared += gyroBiasRadS_[axis] * gyroBiasRadS_[axis];
    const float variance = std::max(
        0.0F,
        gyroSquareSum[axis] / IMU_GYRO_CALIBRATION_SAMPLES -
            gyroBiasRadS_[axis] * gyroBiasRadS_[axis]);
    if (sqrtf(variance) > IMU_CALIBRATION_MAX_GYRO_STDDEV_RAD_S) {
      calibrationUnstable_ = true;
    }
  }

  const float accelMean =
      accelMagnitudeSum / IMU_GYRO_CALIBRATION_SAMPLES;
  const float accelVariance = std::max(
      0.0F,
      accelMagnitudeSquareSum / IMU_GYRO_CALIBRATION_SAMPLES -
          accelMean * accelMean);
  if (sqrtf(gyroMeanMagnitudeSquared) >
          IMU_CALIBRATION_MAX_GYRO_MEAN_RAD_S ||
      sqrtf(accelVariance) > IMU_CALIBRATION_MAX_ACCEL_STDDEV_M_S2) {
    calibrationUnstable_ = true;
  }
  if (calibrationUnstable_) {
    return false;
  }

  referenceAccelMagnitude_ =
      sqrtf(referenceGravity_[0] * referenceGravity_[0] +
            referenceGravity_[1] * referenceGravity_[1] +
            referenceGravity_[2] * referenceGravity_[2]);
  if (referenceAccelMagnitude_ < 4.0F) {
    return false;
  }
  for (float &axis : referenceGravity_) {
    axis /= referenceAccelMagnitude_;
  }
  return true;
}

bool ImuSource::begin() {
  Wire.begin(IMU_SDA_PIN, IMU_SCL_PIN);
  calibrationUnstable_ = false;
  ready_ = mpu_.begin(IMU_I2C_ADDRESS, &Wire);
  if (!ready_) {
    return false;
  }

  mpu_.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu_.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu_.setFilterBandwidth(MPU6050_BAND_21_HZ);
  delay(100);

  ready_ = calibrateGyro();
  quaternion_[0] = 1.0F;
  quaternion_[1] = 0.0F;
  quaternion_[2] = 0.0F;
  quaternion_[3] = 0.0F;
  lastSampleMicros_ = micros();
  return ready_;
}

void ImuSource::expectedGravityInBody(float output[3]) const {
  const float w = quaternion_[0];
  const float x = quaternion_[1];
  const float y = quaternion_[2];
  const float z = quaternion_[3];
  const float gx = referenceGravity_[0];
  const float gy = referenceGravity_[1];
  const float gz = referenceGravity_[2];

  // quaternion_ rotates the current body frame into the startup frame.
  // R(q)^T rotates the startup gravity vector into the current body frame.
  output[0] = (1.0F - 2.0F * (y * y + z * z)) * gx +
              2.0F * (x * y + w * z) * gy +
              2.0F * (x * z - w * y) * gz;
  output[1] = 2.0F * (x * y - w * z) * gx +
              (1.0F - 2.0F * (x * x + z * z)) * gy +
              2.0F * (y * z + w * x) * gz;
  output[2] = 2.0F * (x * z + w * y) * gx +
              2.0F * (y * z - w * x) * gy +
              (1.0F - 2.0F * (x * x + y * y)) * gz;
}

void ImuSource::updateQuaternion(const float bodyRate[3], float dt) {
  const float w = quaternion_[0];
  const float x = quaternion_[1];
  const float y = quaternion_[2];
  const float z = quaternion_[3];
  const float halfDt = 0.5F * dt;

  quaternion_[0] += (-x * bodyRate[0] - y * bodyRate[1] - z * bodyRate[2]) * halfDt;
  quaternion_[1] += (w * bodyRate[0] + y * bodyRate[2] - z * bodyRate[1]) * halfDt;
  quaternion_[2] += (w * bodyRate[1] - x * bodyRate[2] + z * bodyRate[0]) * halfDt;
  quaternion_[3] += (w * bodyRate[2] + x * bodyRate[1] - y * bodyRate[0]) * halfDt;

  const float magnitude =
      sqrtf(quaternion_[0] * quaternion_[0] + quaternion_[1] * quaternion_[1] +
            quaternion_[2] * quaternion_[2] + quaternion_[3] * quaternion_[3]);
  if (magnitude < 1.0e-8F) {
    quaternion_[0] = 1.0F;
    quaternion_[1] = quaternion_[2] = quaternion_[3] = 0.0F;
    return;
  }
  for (float &value : quaternion_) {
    value /= magnitude;
  }
}

RpyDegrees ImuSource::relativeQuaternionToRpy() const {
  const float w = quaternion_[0];
  const float x = quaternion_[1];
  const float y = quaternion_[2];
  const float z = quaternion_[3];

  const float roll =
      atan2f(2.0F * (w * x + y * z), 1.0F - 2.0F * (x * x + y * y));
  const float sinPitch =
      clampValue(2.0F * (w * y - z * x), -1.0F, 1.0F);
  const float pitch = asinf(sinPitch);
  const float yaw =
      atan2f(2.0F * (w * z + x * y), 1.0F - 2.0F * (y * y + z * z));

  RpyDegrees result;
  result.yaw = wrapDegrees(
      IMU_YAW_SIGN * yaw * RAD_TO_DEG_F + IMU_YAW_OFFSET_DEG);
  result.pitch = wrapDegrees(
      IMU_PITCH_SIGN * pitch * RAD_TO_DEG_F + IMU_PITCH_OFFSET_DEG);
  result.roll = wrapDegrees(
      IMU_ROLL_SIGN * roll * RAD_TO_DEG_F + IMU_ROLL_OFFSET_DEG);
  return result;
}

bool ImuSource::read(RpyDegrees &rpy) {
  if (!ready_) {
    return false;
  }

  const uint32_t nowMicros = micros();
  const uint32_t elapsedMicros = nowMicros - lastSampleMicros_;
  if (elapsedMicros < IMU_REPORT_INTERVAL_US) {
    return false;
  }
  lastSampleMicros_ = nowMicros;
  const float dt = std::min(elapsedMicros * 1.0e-6F, 0.05F);

  sensors_event_t acceleration;
  sensors_event_t gyro;
  sensors_event_t temperature;
  if (!mpu_.getEvent(&acceleration, &gyro, &temperature)) {
    ready_ = false;
    return false;
  }

  float accel[3] = {};
  float rawBodyRate[3] = {};
  float bodyRate[3] = {};
  mapSensorAxes(acceleration.acceleration.x, acceleration.acceleration.y,
                acceleration.acceleration.z, accel);
  mapSensorAxes(gyro.gyro.x, gyro.gyro.y, gyro.gyro.z, rawBodyRate);
  for (size_t axis = 0; axis < 3; ++axis) {
    bodyRate[axis] = rawBodyRate[axis] - gyroBiasRadS_[axis];
  }

  const float accelMagnitude =
      sqrtf(accel[0] * accel[0] + accel[1] * accel[1] + accel[2] * accel[2]);
  const float magnitudeRatio = accelMagnitude / referenceAccelMagnitude_;
  const float correctedRateMagnitude =
      sqrtf(bodyRate[0] * bodyRate[0] + bodyRate[1] * bodyRate[1] +
            bodyRate[2] * bodyRate[2]);
  if (magnitudeRatio >= 0.95F && magnitudeRatio <= 1.05F &&
      correctedRateMagnitude <= IMU_BIAS_TRACKING_MAX_RATE_RAD_S) {
    const float biasAlpha = dt / (IMU_BIAS_TRACKING_TAU_S + dt);
    for (size_t axis = 0; axis < 3; ++axis) {
      gyroBiasRadS_[axis] +=
          biasAlpha * (rawBodyRate[axis] - gyroBiasRadS_[axis]);
      bodyRate[axis] = rawBodyRate[axis] - gyroBiasRadS_[axis];
    }
  }
  if (accelMagnitude > 1.0e-6F &&
      magnitudeRatio >= IMU_ACCEL_CORRECTION_MIN_RATIO &&
      magnitudeRatio <= IMU_ACCEL_CORRECTION_MAX_RATIO) {
    float measuredGravity[3] = {
        accel[0] / accelMagnitude,
        accel[1] / accelMagnitude,
        accel[2] / accelMagnitude,
    };
    float expectedGravity[3] = {};
    expectedGravityInBody(expectedGravity);

    const float error[3] = {
        measuredGravity[1] * expectedGravity[2] -
            measuredGravity[2] * expectedGravity[1],
        measuredGravity[2] * expectedGravity[0] -
            measuredGravity[0] * expectedGravity[2],
        measuredGravity[0] * expectedGravity[1] -
            measuredGravity[1] * expectedGravity[0],
    };
    for (size_t axis = 0; axis < 3; ++axis) {
      bodyRate[axis] += IMU_ATTITUDE_KP * error[axis];
    }
  }

  updateQuaternion(bodyRate, dt);
  rpy = relativeQuaternionToRpy();
  return true;
}

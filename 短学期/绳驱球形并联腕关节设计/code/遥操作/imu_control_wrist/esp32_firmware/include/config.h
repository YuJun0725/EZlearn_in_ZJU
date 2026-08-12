#pragma once

#include <Arduino.h>

// USB serial link between the ESP32 and the computer.
constexpr uint32_t HOST_BAUDRATE = 115200;

// Feetech STS/HLS/SMS bus servo UART.
constexpr int SERVO_UART_NUMBER = 2;
constexpr int SERVO_RX_PIN = 16;
constexpr int SERVO_TX_PIN = 17;
constexpr uint32_t SERVO_BAUDRATE = 1000000;

constexpr size_t SERVO_COUNT = 3;
constexpr uint8_t SERVO_IDS[SERVO_COUNT] = {0, 1, 2};
constexpr int32_t SERVO_CENTER[SERVO_COUNT] = {2048, 2048, 2048};
// Motor output angle / mechanism theta. A 3:1 reduction means 3.0 here.
constexpr float SERVO_GEAR_RATIO[SERVO_COUNT] = {3.0F, 3.0F, 3.0F};

// Physical convention from the original test:
// CENTER - 1024 is a physical counter-clockwise 90 degree turn, and theta
// increases counter-clockwise. Therefore every theta-to-position sign is -1.
constexpr int8_t SERVO_THETA_SIGN[SERVO_COUNT] = {-1, -1, -1};
constexpr float SERVO_ZERO_OFFSET_DEG[SERVO_COUNT] = {0.0F, 0.0F, 0.0F};
// A single-turn servo centered at 2048 provides almost +/-60 degrees theta.
constexpr float SERVO_MIN_THETA_DEG[SERVO_COUNT] = {-59.0F, -59.0F, -59.0F};
constexpr float SERVO_MAX_THETA_DEG[SERVO_COUNT] = {59.0F, 59.0F, 59.0F};
constexpr float SERVO_BASE_AZIMUTH_DEG[SERVO_COUNT] = {0.0F, 120.0F, -120.0F};
constexpr float MIN_AXIS_CLEARANCE_DEG = 5.0F;

constexpr uint8_t SERVO_ACCELERATION = 60;
constexpr uint16_t SERVO_SPEED = 1000;
constexpr bool MOVE_TO_ZERO_ON_BOOT = false;

// MPU6050 I2C connection. Use 0x69 when AD0 is pulled high.
constexpr int IMU_SDA_PIN = 21;
constexpr int IMU_SCL_PIN = 22;
constexpr uint8_t IMU_I2C_ADDRESS = 0x68;
constexpr uint32_t IMU_REPORT_INTERVAL_US = 10000;  // 100 Hz
constexpr uint32_t IMU_RETRY_INTERVAL_MS = 2000;
constexpr uint16_t IMU_GYRO_CALIBRATION_SAMPLES = 500;
constexpr float IMU_ATTITUDE_KP = 2.0F;
constexpr float IMU_ACCEL_CORRECTION_MIN_RATIO = 0.75F;
constexpr float IMU_ACCEL_CORRECTION_MAX_RATIO = 1.25F;
constexpr float IMU_CALIBRATION_MAX_GYRO_STDDEV_RAD_S = 0.03F;
constexpr float IMU_CALIBRATION_MAX_GYRO_MEAN_RAD_S = 0.15F;
constexpr float IMU_CALIBRATION_MAX_ACCEL_STDDEV_M_S2 = 0.35F;
constexpr float IMU_BIAS_TRACKING_MAX_RATE_RAD_S = 0.02F;
constexpr float IMU_BIAS_TRACKING_TAU_S = 10.0F;

// Map MPU axes to mechanism axes before attitude estimation.
// 0 = sensor X, 1 = sensor Y, 2 = sensor Z.
constexpr uint8_t IMU_AXIS_MAP[3] = {0, 1, 2};
constexpr float IMU_AXIS_SIGN[3] = {1.0F, 1.0F, 1.0F};

// Final RPY signs and fixed offsets after attitude estimation.
constexpr float IMU_YAW_SIGN = 1.0F;
constexpr float IMU_PITCH_SIGN = 1.0F;
constexpr float IMU_ROLL_SIGN = 1.0F;
constexpr float IMU_YAW_OFFSET_DEG = 0.0F;
constexpr float IMU_PITCH_OFFSET_DEG = 0.0F;
constexpr float IMU_ROLL_OFFSET_DEG = 0.0F;

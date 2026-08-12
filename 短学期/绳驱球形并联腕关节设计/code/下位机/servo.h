/**
 * @file servo.h
 * @brief STM32 HAL driver for the FEETECH serial bus-servo protocol.
 *
 * Protocol source:
 *   "Communication Protocol Manual - Magnetic Encoder Version" (2022-04-03)
 *
 * UART requirements:
 *   - Asynchronous serial, 8 data bits, no parity, 1 stop bit (8-N-1).
 *   - Configure the baud rate according to the concrete servo model.
 *   - TTL half-duplex and RS485 transceivers can be supported through the
 *     optional direction callback.
 *
 * The driver is blocking, performs no dynamic allocation, and is not
 * re-entrant. If several RTOS tasks share one bus, protect each complete API
 * call with the same mutex.
 */

#ifndef SERVO_H
#define SERVO_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/*
 * CubeMX projects normally expose the selected STM32 HAL through main.h.
 * A project may override this before including servo.h, for example:
 *
 *   #define SERVO_HAL_HEADER "stm32f4xx_hal.h"
 *   #include "servo.h"
 */
#ifndef SERVO_HAL_HEADER
#define SERVO_HAL_HEADER "main.h"
#endif
#include SERVO_HAL_HEADER

/* Protocol constants. */
#define SERVO_HEADER_BYTE                 0xFFU
#define SERVO_BROADCAST_ID                0xFEU
#define SERVO_MAX_UNICAST_ID              0xFDU

#define SERVO_INST_PING                   0x01U
#define SERVO_INST_READ_DATA              0x02U
#define SERVO_INST_WRITE_DATA             0x03U
#define SERVO_INST_REG_WRITE              0x04U
#define SERVO_INST_ACTION                 0x05U
#define SERVO_INST_RECOVERY               0x06U
#define SERVO_INST_RESET                  0x0AU
#define SERVO_INST_SYNC_READ              0x82U
#define SERVO_INST_SYNC_WRITE             0x83U

/*
 * The one-byte protocol length field permits at most 253 instruction
 * parameters and a 259-byte complete packet. Reducing this macro saves RAM,
 * but also reduces the largest supported SYNC READ/WRITE packet.
 */
#ifndef SERVO_MAX_PACKET_SIZE
#define SERVO_MAX_PACKET_SIZE             259U
#endif

#if (SERVO_MAX_PACKET_SIZE < 6U) || (SERVO_MAX_PACKET_SIZE > 259U)
#error "SERVO_MAX_PACKET_SIZE must be in the range 6..259"
#endif

#define SERVO_MAX_PARAMETERS              (SERVO_MAX_PACKET_SIZE - 6U)
#define SERVO_DEFAULT_TIMEOUT_MS          20U

/*
 * These two addresses are present in the examples in the supplied protocol
 * manual. They are not guaranteed to be identical on every servo model.
 * Override them at compile time after checking the model-specific control
 * table.
 */
#ifndef SERVO_ADDR_GOAL_POSITION
#define SERVO_ADDR_GOAL_POSITION          0x2AU
#endif

#ifndef SERVO_ADDR_PRESENT_POSITION
#define SERVO_ADDR_PRESENT_POSITION       0x38U
#endif

#define SERVO_GOAL_BLOCK_LENGTH           6U

typedef enum
{
    SERVO_RESULT_OK = 0,
    SERVO_RESULT_INVALID_ARGUMENT,
    SERVO_RESULT_INVALID_ID,
    SERVO_RESULT_PACKET_TOO_LARGE,
    SERVO_RESULT_BUFFER_TOO_SMALL,
    SERVO_RESULT_HAL_ERROR,
    SERVO_RESULT_HAL_BUSY,
    SERVO_RESULT_TIMEOUT,
    SERVO_RESULT_BAD_LENGTH,
    SERVO_RESULT_CHECKSUM_ERROR,
    SERVO_RESULT_ID_MISMATCH
} Servo_Result;

/**
 * @brief Optional half-duplex/RS485 direction callback.
 *
 * @param user      User context supplied to ServoBus_Init().
 * @param transmit  true before transmission, false before reception.
 *
 * Typical RS485 implementation:
 *   HAL_GPIO_WritePin(DE_GPIO_Port, DE_Pin,
 *                     transmit ? GPIO_PIN_SET : GPIO_PIN_RESET);
 *
 * For a transceiver with separate DE and /RE pins, drive both pins as required
 * by its data sheet.
 */
typedef void (*Servo_DirectionCallback)(void *user, bool transmit);

typedef struct
{
    UART_HandleTypeDef *huart;
    Servo_DirectionCallback set_direction;
    void *direction_user;
    uint32_t timeout_ms;
    uint8_t tx_buffer[SERVO_MAX_PACKET_SIZE];
} ServoBus_HandleTypeDef;

/**
 * @brief One item in a generic synchronous write operation.
 *
 * data must point to exactly data_length bytes passed to Servo_SyncWrite().
 */
typedef struct
{
    uint8_t id;
    const uint8_t *data;
} ServoSyncWriteItem;

/**
 * @brief One target for the model-example goal block at address 0x2A.
 *
 * position, time and speed are serialized little-endian, as required by the
 * supplied magnetic-encoder protocol manual. Their engineering units remain
 * model-specific.
 */
typedef struct
{
    uint8_t id;
    uint16_t position;
    uint16_t time;
    uint16_t speed;
} ServoMoveItem;

/* Bus setup. */
Servo_Result ServoBus_Init(ServoBus_HandleTypeDef *bus,
                           UART_HandleTypeDef *huart,
                           uint32_t timeout_ms,
                           Servo_DirectionCallback direction_callback,
                           void *direction_user);

void ServoBus_SetTimeout(ServoBus_HandleTypeDef *bus, uint32_t timeout_ms);

/*
 * Low-level packet APIs. Servo_ReceiveStatus() returns the raw device ERROR
 * byte through device_error. A non-zero device_error does not make the
 * transport result fail; callers should evaluate it separately.
 */
Servo_Result Servo_SendInstruction(ServoBus_HandleTypeDef *bus,
                                   uint8_t id,
                                   uint8_t instruction,
                                   const uint8_t *parameters,
                                   uint8_t parameter_count);

Servo_Result Servo_ReceiveStatus(ServoBus_HandleTypeDef *bus,
                                uint8_t expected_id,
                                uint8_t *device_error,
                                uint8_t *parameters,
                                uint8_t parameter_capacity,
                                uint8_t *parameter_count);

Servo_Result Servo_Transact(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t instruction,
                            const uint8_t *tx_parameters,
                            uint8_t tx_parameter_count,
                            bool expect_status,
                            uint8_t *device_error,
                            uint8_t *rx_parameters,
                            uint8_t rx_parameter_capacity,
                            uint8_t *rx_parameter_count);

/* Protocol instruction APIs. */
Servo_Result Servo_Ping(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint8_t *device_error);

Servo_Result Servo_Read(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint8_t start_address,
                        uint8_t data_length,
                        uint8_t *data,
                        uint8_t *device_error);

Servo_Result Servo_Write(ServoBus_HandleTypeDef *bus,
                         uint8_t id,
                         uint8_t start_address,
                         const uint8_t *data,
                         uint8_t data_length,
                         bool wait_for_status,
                         uint8_t *device_error);

Servo_Result Servo_RegWrite(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t start_address,
                            const uint8_t *data,
                            uint8_t data_length,
                            bool wait_for_status,
                            uint8_t *device_error);

/**
 * @brief Broadcast ACTION; no status packet is expected.
 */
Servo_Result Servo_Action(ServoBus_HandleTypeDef *bus);

/**
 * @brief Broadcast one write packet to several servos.
 *
 * Every item writes the same start address and byte count. No status packet is
 * returned because the packet uses broadcast ID 0xFE.
 */
Servo_Result Servo_SyncWrite(ServoBus_HandleTypeDef *bus,
                             uint8_t start_address,
                             uint8_t data_length,
                             const ServoSyncWriteItem *items,
                             uint8_t item_count);

/**
 * @brief Broadcast a synchronous read and receive replies in requested ID order.
 *
 * out_data contains item_count rows separated by out_stride bytes. out_stride
 * must be at least data_length. device_errors may be NULL; otherwise it must
 * contain item_count bytes.
 *
 * The protocol manual notes that SYNC READ is implemented only by some servo
 * models.
 */
Servo_Result Servo_SyncRead(ServoBus_HandleTypeDef *bus,
                            uint8_t start_address,
                            uint8_t data_length,
                            const uint8_t *ids,
                            uint8_t item_count,
                            uint8_t *out_data,
                            size_t out_stride,
                            uint8_t *device_errors);

Servo_Result Servo_Recovery(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t *device_error);

Servo_Result Servo_Reset(ServoBus_HandleTypeDef *bus,
                         uint8_t id,
                         uint8_t *device_error);

/* Little-endian control-table convenience APIs. */
Servo_Result Servo_ReadU8(ServoBus_HandleTypeDef *bus,
                          uint8_t id,
                          uint8_t address,
                          uint8_t *value,
                          uint8_t *device_error);

Servo_Result Servo_ReadU16(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint8_t address,
                           uint16_t *value,
                           uint8_t *device_error);

Servo_Result Servo_WriteU8(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint8_t address,
                           uint8_t value,
                           bool wait_for_status,
                           uint8_t *device_error);

Servo_Result Servo_WriteU16(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t address,
                            uint16_t value,
                            bool wait_for_status,
                            uint8_t *device_error);

/*
 * Convenience APIs derived from the two example addresses in the supplied
 * manual. Check the concrete servo's control table before use.
 */
Servo_Result Servo_Move(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint16_t position,
                        uint16_t time,
                        uint16_t speed,
                        uint8_t *device_error);

Servo_Result Servo_RegMove(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint16_t position,
                           uint16_t time,
                           uint16_t speed,
                           uint8_t *device_error);

Servo_Result Servo_SyncMove(ServoBus_HandleTypeDef *bus,
                            const ServoMoveItem *items,
                            uint8_t item_count);

Servo_Result Servo_ReadPosition(ServoBus_HandleTypeDef *bus,
                                uint8_t id,
                                uint16_t *position,
                                uint8_t *device_error);

const char *Servo_ResultString(Servo_Result result);

#ifdef __cplusplus
}
#endif

#endif /* SERVO_H */

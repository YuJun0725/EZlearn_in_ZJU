/**
 * @file servo.c
 * @brief STM32 HAL implementation of the FEETECH serial bus-servo protocol.
 */

#include "servo.h"

#include <string.h>

static bool Servo_IsValidAnyId(uint8_t id)
{
    return id <= SERVO_BROADCAST_ID;
}

static bool Servo_IsValidUnicastId(uint8_t id)
{
    return id <= SERVO_MAX_UNICAST_ID;
}

static Servo_Result Servo_MapHalStatus(HAL_StatusTypeDef status)
{
    switch (status)
    {
        case HAL_OK:
            return SERVO_RESULT_OK;

        case HAL_BUSY:
            return SERVO_RESULT_HAL_BUSY;

        case HAL_TIMEOUT:
            return SERVO_RESULT_TIMEOUT;

        case HAL_ERROR:
        default:
            return SERVO_RESULT_HAL_ERROR;
    }
}

static uint32_t Servo_RemainingTimeout(uint32_t start_tick, uint32_t timeout_ms)
{
    uint32_t elapsed;

    if (timeout_ms == HAL_MAX_DELAY)
    {
        return HAL_MAX_DELAY;
    }

    elapsed = HAL_GetTick() - start_tick;
    if (elapsed >= timeout_ms)
    {
        return 0U;
    }

    return timeout_ms - elapsed;
}

static Servo_Result Servo_ReceiveByte(ServoBus_HandleTypeDef *bus,
                                      uint32_t start_tick,
                                      uint8_t *value)
{
    uint32_t remaining;
    HAL_StatusTypeDef hal_status;

    remaining = Servo_RemainingTimeout(start_tick, bus->timeout_ms);
    if (remaining == 0U)
    {
        return SERVO_RESULT_TIMEOUT;
    }

    hal_status = HAL_UART_Receive(bus->huart, value, 1U, remaining);
    return Servo_MapHalStatus(hal_status);
}

static uint8_t Servo_Checksum(const uint8_t *packet_without_header,
                              size_t byte_count)
{
    uint8_t sum = 0U;
    size_t index;

    for (index = 0U; index < byte_count; ++index)
    {
        sum = (uint8_t)(sum + packet_without_header[index]);
    }

    return (uint8_t)(~sum);
}

static void Servo_EncodeU16LE(uint16_t value, uint8_t bytes[2])
{
    bytes[0] = (uint8_t)(value & 0xFFU);
    bytes[1] = (uint8_t)((value >> 8U) & 0xFFU);
}

static uint16_t Servo_DecodeU16LE(const uint8_t bytes[2])
{
    return (uint16_t)((uint16_t)bytes[0] |
                      ((uint16_t)bytes[1] << 8U));
}

static Servo_Result Servo_TransmitPrepared(ServoBus_HandleTypeDef *bus,
                                           size_t packet_size)
{
    HAL_StatusTypeDef hal_status;

    if ((bus == NULL) || (bus->huart == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if ((packet_size < 6U) || (packet_size > SERVO_MAX_PACKET_SIZE) ||
        (packet_size > UINT16_MAX))
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    if (bus->set_direction != NULL)
    {
        bus->set_direction(bus->direction_user, true);
    }

    hal_status = HAL_UART_Transmit(bus->huart,
                                  bus->tx_buffer,
                                  (uint16_t)packet_size,
                                  bus->timeout_ms);

    /*
     * Blocking HAL_UART_Transmit() waits for the final transmission-complete
     * condition on supported STM32 HAL families. Direction is switched only
     * after it returns so the stop bit is not truncated.
     */
    if (bus->set_direction != NULL)
    {
        bus->set_direction(bus->direction_user, false);
    }

    return Servo_MapHalStatus(hal_status);
}

/*
 * Send a packet whose parameters already occupy tx_buffer[5..].
 */
static Servo_Result Servo_SendPreparedParameters(ServoBus_HandleTypeDef *bus,
                                                 uint8_t id,
                                                 uint8_t instruction,
                                                 uint8_t parameter_count)
{
    size_t packet_size;

    if ((bus == NULL) || (bus->huart == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if (!Servo_IsValidAnyId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    packet_size = (size_t)parameter_count + 6U;
    if (packet_size > SERVO_MAX_PACKET_SIZE)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    bus->tx_buffer[0] = SERVO_HEADER_BYTE;
    bus->tx_buffer[1] = SERVO_HEADER_BYTE;
    bus->tx_buffer[2] = id;
    bus->tx_buffer[3] = (uint8_t)(parameter_count + 2U);
    bus->tx_buffer[4] = instruction;
    bus->tx_buffer[packet_size - 1U] =
        Servo_Checksum(&bus->tx_buffer[2], packet_size - 3U);

    return Servo_TransmitPrepared(bus, packet_size);
}

static Servo_Result Servo_WriteInstruction(ServoBus_HandleTypeDef *bus,
                                           uint8_t instruction,
                                           uint8_t id,
                                           uint8_t start_address,
                                           const uint8_t *data,
                                           uint8_t data_length,
                                           bool wait_for_status,
                                           uint8_t *device_error)
{
    uint8_t rx_count = 0U;
    uint8_t parameter_count;
    Servo_Result result;

    if ((bus == NULL) || (bus->huart == NULL) ||
        (data == NULL) || (data_length == 0U))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if ((size_t)data_length + 1U > SERVO_MAX_PARAMETERS)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    parameter_count = (uint8_t)(data_length + 1U);
    (void)memmove(&bus->tx_buffer[6], data, data_length);
    bus->tx_buffer[5] = start_address;

    result = Servo_SendPreparedParameters(bus, id, instruction, parameter_count);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    if (!wait_for_status || (id == SERVO_BROADCAST_ID))
    {
        return SERVO_RESULT_OK;
    }

    result = Servo_ReceiveStatus(bus,
                                 id,
                                 device_error,
                                 NULL,
                                 0U,
                                 &rx_count);
    if ((result == SERVO_RESULT_OK) && (rx_count != 0U))
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    return result;
}

Servo_Result ServoBus_Init(ServoBus_HandleTypeDef *bus,
                           UART_HandleTypeDef *huart,
                           uint32_t timeout_ms,
                           Servo_DirectionCallback direction_callback,
                           void *direction_user)
{
    if ((bus == NULL) || (huart == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    bus->huart = huart;
    bus->set_direction = direction_callback;
    bus->direction_user = direction_user;
    bus->timeout_ms =
        (timeout_ms == 0U) ? SERVO_DEFAULT_TIMEOUT_MS : timeout_ms;
    (void)memset(bus->tx_buffer, 0, sizeof(bus->tx_buffer));

    if (bus->set_direction != NULL)
    {
        bus->set_direction(bus->direction_user, false);
    }

    return SERVO_RESULT_OK;
}

void ServoBus_SetTimeout(ServoBus_HandleTypeDef *bus, uint32_t timeout_ms)
{
    if (bus != NULL)
    {
        bus->timeout_ms =
            (timeout_ms == 0U) ? SERVO_DEFAULT_TIMEOUT_MS : timeout_ms;
    }
}

Servo_Result Servo_SendInstruction(ServoBus_HandleTypeDef *bus,
                                   uint8_t id,
                                   uint8_t instruction,
                                   const uint8_t *parameters,
                                   uint8_t parameter_count)
{
    if ((bus == NULL) || (bus->huart == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if (!Servo_IsValidAnyId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    if ((parameter_count > 0U) && (parameters == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if ((size_t)parameter_count > SERVO_MAX_PARAMETERS)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    if (parameter_count > 0U)
    {
        (void)memmove(&bus->tx_buffer[5], parameters, parameter_count);
    }

    return Servo_SendPreparedParameters(bus, id, instruction, parameter_count);
}

Servo_Result Servo_ReceiveStatus(ServoBus_HandleTypeDef *bus,
                                uint8_t expected_id,
                                uint8_t *device_error,
                                uint8_t *parameters,
                                uint8_t parameter_capacity,
                                uint8_t *parameter_count)
{
    uint32_t start_tick;
    uint8_t byte = 0U;
    uint8_t id;
    uint8_t length;
    uint8_t error;
    uint8_t received_checksum;
    uint8_t calculated_checksum;
    uint8_t sum;
    uint8_t count;
    uint8_t index;
    uint8_t header_count = 0U;
    bool buffer_too_small = false;
    Servo_Result result;

    if ((bus == NULL) || (bus->huart == NULL) || (parameter_count == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    if (!Servo_IsValidUnicastId(expected_id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    if ((parameter_capacity > 0U) && (parameters == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    *parameter_count = 0U;
    start_tick = HAL_GetTick();

    if (bus->set_direction != NULL)
    {
        bus->set_direction(bus->direction_user, false);
    }

    /*
     * Seek two consecutive 0xFF bytes. A third 0xFF is treated as a possible
     * overlapping header because 0xFF is not a legal status-packet ID.
     */
    while (header_count < 2U)
    {
        result = Servo_ReceiveByte(bus, start_tick, &byte);
        if (result != SERVO_RESULT_OK)
        {
            return result;
        }

        if (byte == SERVO_HEADER_BYTE)
        {
            ++header_count;
        }
        else
        {
            header_count = 0U;
        }
    }

    do
    {
        result = Servo_ReceiveByte(bus, start_tick, &id);
        if (result != SERVO_RESULT_OK)
        {
            return result;
        }
    } while (id == SERVO_HEADER_BYTE);

    if (!Servo_IsValidUnicastId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    result = Servo_ReceiveByte(bus, start_tick, &length);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    if (length < 2U)
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    count = (uint8_t)(length - 2U);
    *parameter_count = count;
    if (count > parameter_capacity)
    {
        buffer_too_small = true;
    }

    result = Servo_ReceiveByte(bus, start_tick, &error);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    sum = (uint8_t)(id + length + error);

    for (index = 0U; index < count; ++index)
    {
        result = Servo_ReceiveByte(bus, start_tick, &byte);
        if (result != SERVO_RESULT_OK)
        {
            return result;
        }

        sum = (uint8_t)(sum + byte);
        if (index < parameter_capacity)
        {
            parameters[index] = byte;
        }
    }

    result = Servo_ReceiveByte(bus, start_tick, &received_checksum);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    calculated_checksum = (uint8_t)(~sum);
    if (received_checksum != calculated_checksum)
    {
        return SERVO_RESULT_CHECKSUM_ERROR;
    }

    if (id != expected_id)
    {
        return SERVO_RESULT_ID_MISMATCH;
    }

    if (device_error != NULL)
    {
        *device_error = error;
    }

    if (buffer_too_small)
    {
        return SERVO_RESULT_BUFFER_TOO_SMALL;
    }

    return SERVO_RESULT_OK;
}

Servo_Result Servo_Transact(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t instruction,
                            const uint8_t *tx_parameters,
                            uint8_t tx_parameter_count,
                            bool expect_status,
                            uint8_t *device_error,
                            uint8_t *rx_parameters,
                            uint8_t rx_parameter_capacity,
                            uint8_t *rx_parameter_count)
{
    Servo_Result result;

    if (rx_parameter_count == NULL)
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    *rx_parameter_count = 0U;

    result = Servo_SendInstruction(bus,
                                   id,
                                   instruction,
                                   tx_parameters,
                                   tx_parameter_count);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    if (!expect_status || (id == SERVO_BROADCAST_ID))
    {
        return SERVO_RESULT_OK;
    }

    return Servo_ReceiveStatus(bus,
                               id,
                               device_error,
                               rx_parameters,
                               rx_parameter_capacity,
                               rx_parameter_count);
}

Servo_Result Servo_Ping(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint8_t *device_error)
{
    uint8_t rx_count = 0U;
    Servo_Result result;

    /*
     * Although the manual mentions broadcast PING, several servos replying at
     * once would collide on one bus. Require a unicast ID here.
     */
    if (!Servo_IsValidUnicastId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    result = Servo_Transact(bus,
                            id,
                            SERVO_INST_PING,
                            NULL,
                            0U,
                            true,
                            device_error,
                            NULL,
                            0U,
                            &rx_count);
    if ((result == SERVO_RESULT_OK) && (rx_count != 0U))
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    return result;
}

Servo_Result Servo_Read(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint8_t start_address,
                        uint8_t data_length,
                        uint8_t *data,
                        uint8_t *device_error)
{
    uint8_t tx_parameters[2];
    uint8_t rx_count = 0U;
    Servo_Result result;

    if (!Servo_IsValidUnicastId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    if ((data_length == 0U) || (data == NULL))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    tx_parameters[0] = start_address;
    tx_parameters[1] = data_length;

    result = Servo_Transact(bus,
                            id,
                            SERVO_INST_READ_DATA,
                            tx_parameters,
                            2U,
                            true,
                            device_error,
                            data,
                            data_length,
                            &rx_count);
    if ((result == SERVO_RESULT_OK) && (rx_count != data_length))
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    return result;
}

Servo_Result Servo_Write(ServoBus_HandleTypeDef *bus,
                         uint8_t id,
                         uint8_t start_address,
                         const uint8_t *data,
                         uint8_t data_length,
                         bool wait_for_status,
                         uint8_t *device_error)
{
    return Servo_WriteInstruction(bus,
                                  SERVO_INST_WRITE_DATA,
                                  id,
                                  start_address,
                                  data,
                                  data_length,
                                  wait_for_status,
                                  device_error);
}

Servo_Result Servo_RegWrite(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t start_address,
                            const uint8_t *data,
                            uint8_t data_length,
                            bool wait_for_status,
                            uint8_t *device_error)
{
    return Servo_WriteInstruction(bus,
                                  SERVO_INST_REG_WRITE,
                                  id,
                                  start_address,
                                  data,
                                  data_length,
                                  wait_for_status,
                                  device_error);
}

Servo_Result Servo_Action(ServoBus_HandleTypeDef *bus)
{
    return Servo_SendInstruction(bus,
                                 SERVO_BROADCAST_ID,
                                 SERVO_INST_ACTION,
                                 NULL,
                                 0U);
}

Servo_Result Servo_SyncWrite(ServoBus_HandleTypeDef *bus,
                             uint8_t start_address,
                             uint8_t data_length,
                             const ServoSyncWriteItem *items,
                             uint8_t item_count)
{
    size_t parameter_count;
    size_t offset;
    uint8_t index;

    if ((bus == NULL) || (bus->huart == NULL) || (items == NULL) ||
        (item_count == 0U) || (data_length == 0U))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    parameter_count = 2U + ((size_t)data_length + 1U) * item_count;
    if (parameter_count > SERVO_MAX_PARAMETERS)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    bus->tx_buffer[5] = start_address;
    bus->tx_buffer[6] = data_length;
    offset = 7U;

    for (index = 0U; index < item_count; ++index)
    {
        if (!Servo_IsValidUnicastId(items[index].id))
        {
            return SERVO_RESULT_INVALID_ID;
        }

        if (items[index].data == NULL)
        {
            return SERVO_RESULT_INVALID_ARGUMENT;
        }

        bus->tx_buffer[offset++] = items[index].id;
        (void)memmove(&bus->tx_buffer[offset],
                      items[index].data,
                      data_length);
        offset += data_length;
    }

    return Servo_SendPreparedParameters(bus,
                                        SERVO_BROADCAST_ID,
                                        SERVO_INST_SYNC_WRITE,
                                        (uint8_t)parameter_count);
}

Servo_Result Servo_SyncRead(ServoBus_HandleTypeDef *bus,
                            uint8_t start_address,
                            uint8_t data_length,
                            const uint8_t *ids,
                            uint8_t item_count,
                            uint8_t *out_data,
                            size_t out_stride,
                            uint8_t *device_errors)
{
    size_t parameter_count;
    uint8_t index;
    uint8_t rx_count;
    uint8_t ignored_error;
    Servo_Result result;

    if ((bus == NULL) || (bus->huart == NULL) || (ids == NULL) ||
        (out_data == NULL) || (item_count == 0U) || (data_length == 0U) ||
        (out_stride < data_length))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    parameter_count = (size_t)item_count + 2U;
    if (parameter_count > SERVO_MAX_PARAMETERS)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    bus->tx_buffer[5] = start_address;
    bus->tx_buffer[6] = data_length;
    for (index = 0U; index < item_count; ++index)
    {
        if (!Servo_IsValidUnicastId(ids[index]))
        {
            return SERVO_RESULT_INVALID_ID;
        }
        bus->tx_buffer[7U + index] = ids[index];
    }

    result = Servo_SendPreparedParameters(bus,
                                          SERVO_BROADCAST_ID,
                                          SERVO_INST_SYNC_READ,
                                          (uint8_t)parameter_count);
    if (result != SERVO_RESULT_OK)
    {
        return result;
    }

    for (index = 0U; index < item_count; ++index)
    {
        rx_count = 0U;
        result = Servo_ReceiveStatus(bus,
                                     ids[index],
                                     (device_errors != NULL)
                                         ? &device_errors[index]
                                         : &ignored_error,
                                     &out_data[(size_t)index * out_stride],
                                     data_length,
                                     &rx_count);
        if (result != SERVO_RESULT_OK)
        {
            return result;
        }

        if (rx_count != data_length)
        {
            return SERVO_RESULT_BAD_LENGTH;
        }
    }

    return SERVO_RESULT_OK;
}

Servo_Result Servo_Recovery(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t *device_error)
{
    uint8_t rx_count = 0U;
    Servo_Result result;

    if (!Servo_IsValidAnyId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    result = Servo_Transact(bus,
                            id,
                            SERVO_INST_RECOVERY,
                            NULL,
                            0U,
                            id != SERVO_BROADCAST_ID,
                            device_error,
                            NULL,
                            0U,
                            &rx_count);
    if ((result == SERVO_RESULT_OK) && (rx_count != 0U))
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    return result;
}

Servo_Result Servo_Reset(ServoBus_HandleTypeDef *bus,
                         uint8_t id,
                         uint8_t *device_error)
{
    uint8_t rx_count = 0U;
    Servo_Result result;

    if (!Servo_IsValidAnyId(id))
    {
        return SERVO_RESULT_INVALID_ID;
    }

    result = Servo_Transact(bus,
                            id,
                            SERVO_INST_RESET,
                            NULL,
                            0U,
                            id != SERVO_BROADCAST_ID,
                            device_error,
                            NULL,
                            0U,
                            &rx_count);
    if ((result == SERVO_RESULT_OK) && (rx_count != 0U))
    {
        return SERVO_RESULT_BAD_LENGTH;
    }

    return result;
}

Servo_Result Servo_ReadU8(ServoBus_HandleTypeDef *bus,
                          uint8_t id,
                          uint8_t address,
                          uint8_t *value,
                          uint8_t *device_error)
{
    return Servo_Read(bus, id, address, 1U, value, device_error);
}

Servo_Result Servo_ReadU16(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint8_t address,
                           uint16_t *value,
                           uint8_t *device_error)
{
    uint8_t data[2];
    Servo_Result result;

    if (value == NULL)
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    result = Servo_Read(bus, id, address, 2U, data, device_error);
    if (result == SERVO_RESULT_OK)
    {
        *value = Servo_DecodeU16LE(data);
    }

    return result;
}

Servo_Result Servo_WriteU8(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint8_t address,
                           uint8_t value,
                           bool wait_for_status,
                           uint8_t *device_error)
{
    return Servo_Write(bus,
                       id,
                       address,
                       &value,
                       1U,
                       wait_for_status,
                       device_error);
}

Servo_Result Servo_WriteU16(ServoBus_HandleTypeDef *bus,
                            uint8_t id,
                            uint8_t address,
                            uint16_t value,
                            bool wait_for_status,
                            uint8_t *device_error)
{
    uint8_t data[2];

    Servo_EncodeU16LE(value, data);
    return Servo_Write(bus,
                       id,
                       address,
                       data,
                       2U,
                       wait_for_status,
                       device_error);
}

Servo_Result Servo_Move(ServoBus_HandleTypeDef *bus,
                        uint8_t id,
                        uint16_t position,
                        uint16_t time,
                        uint16_t speed,
                        uint8_t *device_error)
{
    uint8_t data[SERVO_GOAL_BLOCK_LENGTH];

    Servo_EncodeU16LE(position, &data[0]);
    Servo_EncodeU16LE(time, &data[2]);
    Servo_EncodeU16LE(speed, &data[4]);

    return Servo_Write(bus,
                       id,
                       SERVO_ADDR_GOAL_POSITION,
                       data,
                       SERVO_GOAL_BLOCK_LENGTH,
                       true,
                       device_error);
}

Servo_Result Servo_RegMove(ServoBus_HandleTypeDef *bus,
                           uint8_t id,
                           uint16_t position,
                           uint16_t time,
                           uint16_t speed,
                           uint8_t *device_error)
{
    uint8_t data[SERVO_GOAL_BLOCK_LENGTH];

    Servo_EncodeU16LE(position, &data[0]);
    Servo_EncodeU16LE(time, &data[2]);
    Servo_EncodeU16LE(speed, &data[4]);

    return Servo_RegWrite(bus,
                          id,
                          SERVO_ADDR_GOAL_POSITION,
                          data,
                          SERVO_GOAL_BLOCK_LENGTH,
                          true,
                          device_error);
}

Servo_Result Servo_SyncMove(ServoBus_HandleTypeDef *bus,
                            const ServoMoveItem *items,
                            uint8_t item_count)
{
    size_t parameter_count;
    size_t offset;
    uint8_t index;

    if ((bus == NULL) || (bus->huart == NULL) || (items == NULL) ||
        (item_count == 0U))
    {
        return SERVO_RESULT_INVALID_ARGUMENT;
    }

    parameter_count =
        2U + ((size_t)SERVO_GOAL_BLOCK_LENGTH + 1U) * item_count;
    if (parameter_count > SERVO_MAX_PARAMETERS)
    {
        return SERVO_RESULT_PACKET_TOO_LARGE;
    }

    bus->tx_buffer[5] = SERVO_ADDR_GOAL_POSITION;
    bus->tx_buffer[6] = SERVO_GOAL_BLOCK_LENGTH;
    offset = 7U;

    for (index = 0U; index < item_count; ++index)
    {
        if (!Servo_IsValidUnicastId(items[index].id))
        {
            return SERVO_RESULT_INVALID_ID;
        }

        bus->tx_buffer[offset++] = items[index].id;
        Servo_EncodeU16LE(items[index].position,
                          &bus->tx_buffer[offset]);
        offset += 2U;
        Servo_EncodeU16LE(items[index].time,
                          &bus->tx_buffer[offset]);
        offset += 2U;
        Servo_EncodeU16LE(items[index].speed,
                          &bus->tx_buffer[offset]);
        offset += 2U;
    }

    return Servo_SendPreparedParameters(bus,
                                        SERVO_BROADCAST_ID,
                                        SERVO_INST_SYNC_WRITE,
                                        (uint8_t)parameter_count);
}

Servo_Result Servo_ReadPosition(ServoBus_HandleTypeDef *bus,
                                uint8_t id,
                                uint16_t *position,
                                uint8_t *device_error)
{
    return Servo_ReadU16(bus,
                         id,
                         SERVO_ADDR_PRESENT_POSITION,
                         position,
                         device_error);
}

const char *Servo_ResultString(Servo_Result result)
{
    switch (result)
    {
        case SERVO_RESULT_OK:
            return "OK";

        case SERVO_RESULT_INVALID_ARGUMENT:
            return "invalid argument";

        case SERVO_RESULT_INVALID_ID:
            return "invalid servo ID";

        case SERVO_RESULT_PACKET_TOO_LARGE:
            return "packet too large";

        case SERVO_RESULT_BUFFER_TOO_SMALL:
            return "receive buffer too small";

        case SERVO_RESULT_HAL_ERROR:
            return "STM32 HAL UART error";

        case SERVO_RESULT_HAL_BUSY:
            return "STM32 HAL UART busy";

        case SERVO_RESULT_TIMEOUT:
            return "communication timeout";

        case SERVO_RESULT_BAD_LENGTH:
            return "invalid packet length";

        case SERVO_RESULT_CHECKSUM_ERROR:
            return "checksum mismatch";

        case SERVO_RESULT_ID_MISMATCH:
            return "unexpected servo ID";

        default:
            return "unknown result";
    }
}

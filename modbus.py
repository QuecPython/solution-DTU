
def modbus_crc(string_byte):
    crc = 0xFFFF
    for pos in string_byte:
        crc ^= pos
        for i in range(8):
            if ((crc & 1) != 0):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    gen_crc = hex(((crc & 0xff) << 8) + (crc >> 8))
    int_crc = int(gen_crc, 16)
    high, low = divmod(int_crc, 0x100)
    string_byte.append(high)
    string_byte.append(low)
    return string_byte
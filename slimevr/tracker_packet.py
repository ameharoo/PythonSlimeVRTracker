import struct
from slimevr.tracker_types import BoardType, HardwareMcuType, ImuType, PacketType, SensorData


class DatagramPacket:
    buf: bytearray
    offset: int

    def __init__(self, buf=None):
        if buf is None:
            buf = bytearray()
        self.buf = buf
        self.offset = 0

    def send_byte(self, value: int):
        self.buf.extend(value.to_bytes(1))

    def send_bytes(self, values: list[int]):
        self.buf.extend(bytes(values)) 

    def send_short(self, value: int):
        self.buf.extend(value.to_bytes(2)) 

    def send_int(self, value: int):
        self.buf.extend(value.to_bytes(4)) 

    def send_long(self, value: int):
        self.buf.extend(value.to_bytes(8)) 

    def send_float(self, value: float):
        self.buf.extend(struct.pack("!f", value)) 

    def send_short_string(self, value: str):
        self.send_byte(len(value))
        self.send_bytes(value.encode("ascii")+ b"\00")

    def send_packet_type(self, packet_type: int):
        self.send_byte(0)
        self.send_byte(0)
        self.send_byte(0)
        self.send_byte(packet_type)

    def receive_byte(self) -> int:
        result = int.from_bytes(bytes(self.buf[self.offset]))
        self.offset += 1
        return result

    def receive_short(self) -> int:
        result = int.from_bytes(bytes(self.buf[self.offset:self.offset+2]))
        self.offset += 2
        return result

    def receive_int(self) -> int:
        result = int.from_bytes(bytes(self.buf[self.offset:self.offset+4]))
        self.offset += 4
        return result

    def receive_long(self) -> int:
        result = int.from_bytes(bytes(self.buf[self.offset:self.offset+8]))
        self.offset += 8
        return result

    def receive_packet_type(self) -> PacketType:
        return self.receive_int()

    def send_tracker_discovery(self):
        FIRMWARE_BUILD_NUMBER = 17
        FIRMWARE_VERSION = "0.4.0"
        MAC = bytes([120] * 6)
        
        self.send_packet_type(PacketType.PACKET_HANDSHAKE)
        self.send_long(0)
        self.send_int(BoardType.BOARD_SLIMEVR_DEV)
        self.send_int(ImuType.IMU_DEV_RESERVED)
        self.send_int(HardwareMcuType.MCU_DEV_RESERVED)
        self.send_int(0)
        self.send_int(0)
        self.send_int(0)
        self.send_int(FIRMWARE_BUILD_NUMBER)
        self.send_short_string(FIRMWARE_VERSION)
        self.send_bytes(MAC)

    def send_heartbeat(self, packet_number: int):
        self.send_packet_type(PacketType.PACKET_HEARTBEAT)
        self.send_long(packet_number)

    def send_feature_flags(self, packet_number: int):
        self.send_packet_type(PacketType.PACKET_FEATURE_FLAGS)
        self.send_long(packet_number)
        self.send_byte(0)

    def send_sensor_info(self, packet_number: int, sensor: SensorData):
        self.send_packet_type(PacketType.PACKET_SENSOR_INFO)
        self.send_long(packet_number)
        self.send_byte(sensor.id)
        self.send_byte(sensor.state)
        self.send_byte(sensor.type)

    def send_sensor_acceleration(self, packet_number: int, sensor_id: int, x: float, y: float, z: float):
        self.send_packet_type(PacketType.PACKET_ACCEL)
        self.send_long(packet_number)
        self.send_float(x)
        self.send_float(y)
        self.send_float(z)
        self.send_byte(sensor_id)

    def send_sensor_rotation_and_acceleration(self, packet_number: int, sensor_id: int, qx: float, qy: float, qz: float, qw: float, x: float, y: float, z: float):
        self.send_packet_type(PacketType.PACKET_ROTATION_AND_ACCELERATION)
        self.send_long(packet_number)
        self.send_byte(sensor_id)
        self.send_short(int(qy * (1 << 15)))
        self.send_short(int(qx * (1 << 15)))
        self.send_short(int(qz * (1 << 15)))
        self.send_short(int(qw * (1 << 15)))
        self.send_short(int(y * (1 << 7)))
        self.send_short(int(x * (1 << 7)))
        self.send_float(int(z * (1 << 7)))

    def send_sensor_rotation(self, packet_number: int, sensor_id: int, x: float, y: float, z: float, w: float):
        self.send_packet_type(PacketType.PACKET_ROTATION_DATA)
        self.send_long(packet_number)
        self.send_byte(sensor_id)
        self.send_byte(1)
        self.send_float(x)
        self.send_float(y)
        self.send_float(z)
        self.send_float(w)
        self.send_byte(0)
    
    def clear(self):
        self.buf.clear()
    
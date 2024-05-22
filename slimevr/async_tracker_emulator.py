
import asyncio
import math
from socket import AF_INET, SOCK_DGRAM, socket
import time

from slimevr.tracker_packet import DatagramPacket
from slimevr.types import ImuType, PacketType, SensorAcceleration, SensorData, SensorRotationQuat, SensorState


class SlimeVRTrackerEmulator():

    _packet_number: int
    _packet_number_lock: asyncio.Lock

    _sensors: dict[int, SensorData]
    _sensors_lock: asyncio.Lock

    sock: socket

    def __init__(self) -> None:
        self._packet_number = 0
        self._packet_number_lock = asyncio.Lock()

        self._sensors = {}
        self._sensors_lock = asyncio.Lock()

        self.sock = None

    async def set_tracker(self, tracker: SensorData):
        async with self._sensors_lock:
            self._sensors[tracker.id] = tracker

    async def set_tracker_acceleration(self, id: int, acceleration: SensorAcceleration):
        async with self._sensors_lock:
            self._sensors[id].acceleration = acceleration

    async def set_tracker_rotation(self, id: int, rotation: SensorRotationQuat):
        async with self._sensors_lock:
            self._sensors[id].rotation = rotation


    async def get_packet_number(self) -> int:
        async with self._packet_number_lock:
            self._packet_number += 1
            return self._packet_number

    async def send_sensor_info_packet(self, sock: socket, remote_addr, sensor: SensorData):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_sensor_info(await self.get_packet_number(), sensor)
        # print(pn)

        # await asyncio.sleep(0.01)
        await loop.sock_sendto(sock, pb.buf, remote_addr)
        # sock.sendto(pb.buf, remote_addr)

    async def send_sensor_rotation(self, sock: socket, remote_addr, sensor: SensorData):
        loop = asyncio.get_event_loop()

        # sensor.rotation = SensorRotationQuat.from_euler(-math.pi/2, 0, 0)

        pb = DatagramPacket()
        pb.send_sensor_rotation(await self.get_packet_number(), 
                                sensor.id, 
                                sensor.rotation.x , 
                                sensor.rotation.y, 
                                sensor.rotation.z, 
                                sensor.rotation.w)

        # await asyncio.sleep(0.01)
        await loop.sock_sendto(sock, pb.buf, remote_addr)
        # sock.sendto(pb.buf, remote_addr)

    async def send_sensor_acceleration(self, sock: socket, remote_addr, sensor: SensorData):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_sensor_acceleration(await self.get_packet_number(), 
                                    sensor.id, 
                                    sensor.acceleration.x * 100, 
                                    sensor.acceleration.y * 100,
                                    sensor.acceleration.z * 100)
        
        # await asyncio.sleep(0.01)
        await loop.sock_sendto(sock, pb.buf, remote_addr)
        # sock.sendto(pb.buf, remote_addr)

    async def send_sensor_rotation_and_acceleration(self, sock: socket, remote_addr, sensor: SensorData):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_sensor_rotation_and_acceleration(await self.get_packet_number(), 
                                                sensor.id, 
                                                sensor.rotation.x, 
                                                sensor.rotation.y, 
                                                sensor.rotation.z, 
                                                sensor.rotation.w,
                                                sensor.acceleration.x, 
                                                sensor.acceleration.y, 
                                                sensor.acceleration.z)
        

        # await asyncio.sleep(0.01)
        await loop.sock_sendto(sock, pb.buf, remote_addr)
        # sock.sendto(pb.buf, remote_addr)
        
    async def send_heartbeat_packet(self, sock: socket, remote_addr):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_heartbeat(await self.get_packet_number())

        await loop.sock_sendto(sock, pb.buf, remote_addr)

    async def send_tracker_discovery_packet(self, sock: socket, remote_addr):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_tracker_discovery()

        await loop.sock_sendto(sock, pb.buf, remote_addr)

    async def send_feature_flags(self, sock: socket, remote_addr):
        loop = asyncio.get_event_loop()

        pb = DatagramPacket()
        pb.send_feature_flags(await self.get_packet_number())

        await loop.sock_sendto(sock, pb.buf, remote_addr)

    async def send_trackers_data(self, sock: socket, addr):
        # Send sensor info's
        async with self._sensors_lock:
            for sensor in self._sensors.values():
                await self.send_sensor_info_packet(sock, addr, sensor)

            for sensor in self._sensors.values():
                if not sensor.rotation.need_update:
                    continue
                await self.send_sensor_rotation(sock, addr, sensor)
                self._sensors[sensor.id].rotation.need_update = False

            for sensor in self._sensors.values():
                if not sensor.acceleration.need_update:
                    continue
                await self.send_sensor_acceleration(sock, addr, sensor)
                self._sensors[sensor.id].acceleration.need_update = False

        await asyncio.sleep(0.1)

    async def handle_packet(self, sock: socket, remote_addr, recv_buf):
        loop = asyncio.get_event_loop()

        new_packet = DatagramPacket(recv_buf)
        packet_type = new_packet.receive_packet_type()

        if packet_type == PacketType.PACKET_RECEIVE_HEARTBEAT:
            await self.send_heartbeat_packet(sock, remote_addr)
            print("heartbeat")
        elif packet_type == PacketType.PACKET_PING_PONG:
            # Send packet back
            await loop.sock_sendto(sock, recv_buf, remote_addr)
        elif packet_type == PacketType.PACKET_SENSOR_INFO:
            pass
        elif packet_type == PacketType.PACKET_FEATURE_FLAGS:
            pass
        else:
            print("Packet type is: ", packet_type)
            print(recv_buf)

        await self.send_trackers_data(sock, remote_addr)
        await self.send_feature_flags(sock, remote_addr)
    
    # async def do(self, addr):
    #     loop = asyncio.get_event_loop()

    #     await self.send_trackers_data(self.sock, addr)

    #     recv_buf, remote_addr = await loop.sock_recvfrom(self.sock, 1024)
    #     await self.handle_packet(self.sock, remote_addr, recv_buf)


    async def run(self, addr):
        loop = asyncio.get_event_loop()

        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setblocking(False)

        await self.send_tracker_discovery_packet(self.sock, addr)

        while True:
            self.send_trackers_data(self.sock, addr)

            recv_buf, remote_addr = await loop.sock_recvfrom(self.sock, 1024)
            await self.handle_packet(self.sock, remote_addr, recv_buf)


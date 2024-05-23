from dataclasses import dataclass
import math

import numpy as np


class HardwareMcuType:
    MCU_UKNOWN = 0
    MCU_DEV_RESERVED = 250

class ImuType:
    IMU_UNKNOWN = 0
    BNO080 = 3
    IMU_DEV_RESERVED = 250

class BoardType:
    BOARD_UNKNOWN = 0
    BOARD_SLIMEVR_DEV = 2

class PacketType:
    PACKET_HEARTBEAT = 0
    PACKET_RECEIVE_HEARTBEAT = 1
    PACKET_HANDSHAKE = 3
    PACKET_ACCEL = 4
    PACKET_PING_PONG = 10
    PACKET_SENSOR_INFO = 15
    PACKET_ROTATION_DATA = 17
    PACKET_FEATURE_FLAGS = 22
    PACKET_ROTATION_AND_ACCELERATION = 23


class SensorState:
    SENSOR_OFFLINE = 0
    SENSOR_OK = 1
    SENSOR_ERROR = 2

@dataclass
class SensorRotationQuat:
    x: float
    y: float
    z: float
    w: float
    need_update: bool = True

    @classmethod
    def from_euler(cls, angleX, angleY, angleZ):
        a1 = angleX / 2
        a2 = angleY / 2
        a3 = angleZ / 2

        sx = math.sin(a1)
        cx = math.cos(a1)
        sy = math.sin(a2)
        cy = math.cos(a2)
        sz = math.sin(a3)
        cz = math.cos(a3)

        return cls(cx * cy * cz + sx * sy * sz, 
                   cy * cz * sx - cx * sy * sz,
                   cx * cz * sy + cy * sx * sz,
                   -cz * sx * sy + cx * cy * sz)


@dataclass
class SensorAcceleration:
    x: float
    y: float
    z: float
    
    need_update: bool = True

@dataclass
class SensorPosition:
    x: float
    y: float
    z: float
    
    need_update: bool = True

@dataclass
class SensorData:
    id: int
    state: SensorState
    type: ImuType
    rotation: SensorRotationQuat
    acceleration: SensorAcceleration
    position: SensorPosition


class Helper:
    @staticmethod
    def normalize(vector: np.ndarray):
        if (np.all(vector == 0)):
            return vector
        
        return vector / np.linalg.norm(vector)

    # Find quaternoin of rotation A to B
    @classmethod
    def find_quaternion_of_rotation(cls, A, B):

        A_norm = cls.normalize(A)
        B_norm = cls.normalize(B)
        
        dot_product = np.dot(A_norm, B_norm)
        if dot_product > 0.999999:  # Vectors are almost the same
            return np.array([1.0, 0.0, 0.0, 0.0])
        elif dot_product < -0.999999:  # Vectors are opposite
            # Find orthogonal vector to A_norm for axis of rotation
            orthogonal = np.cross(A_norm, [1, 0, 0])
            if np.linalg.norm(orthogonal) < 0.01:
                orthogonal = np.cross(A_norm, [0, 1, 0])
            orthogonal = cls.normalize(orthogonal)
            return np.array([0.0] + list(orthogonal))
        
        cross_product = np.cross(A_norm, B_norm)
        s = np.sqrt((1 + dot_product) * 2)
        inv_s = 1 / s
        
        q = np.zeros(4)
        q[0] = s * 0.5
        q[1:] = cross_product * inv_s
        
        return q
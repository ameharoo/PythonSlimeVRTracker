import asyncio

from slimevr_tracker_emulator.async_tracker_emulator import SlimeVRTrackerEmulatorAsync

UDP_IP = "127.0.0.1"
UDP_PORT = 6969

tracker_emulator = SlimeVRTrackerEmulatorAsync()
asyncio.run(tracker_emulator.run((UDP_IP, UDP_PORT)))
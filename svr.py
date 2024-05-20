import asyncio

from slimevr.async_tracker_emulator import SlimeVRTrackerEmulator

UDP_IP = "127.0.0.1"
UDP_PORT = 6969

tracker_emulator = SlimeVRTrackerEmulator()
asyncio.run(tracker_emulator.run((UDP_IP, UDP_PORT)))
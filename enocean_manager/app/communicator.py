# communicator.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import threading
import time
import os
from typing import Callable, Iterable, Optional, List, Any

try:
    from enocean.protocol.packet import Packet  # type: ignore
    from enocean.communicators.serial import SerialCommunicator  # type: ignore
except Exception:
    Packet = Any  # type: ignore
    class SerialCommunicator:  # type: ignore
        def __init__(self, *a, **kw): pass
        def start(self): pass
        def stop(self): pass
        def receive(self): 
            while False:
                yield None
        def send(self, *_a, **_k): pass

FrameCallback = Callable[[Any], None]

class Communicator:
    def __init__(self, port: Optional[str] = None, baudrate: int = 57600) -> None:
        self.sender_id = None
        self.port = port
        self.baudrate = baudrate
        self._comm = SerialCommunicator(port=self.port, baudrate=self.baudrate)
        self._callbacks: List[FrameCallback] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._running:
            return
        self._comm.start()
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        try:
            self._comm.stop()
        finally:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._thread = None

    def send(self, packet: Any) -> None:
        self._comm.send(packet)

    def add_listener(self, callback: FrameCallback) -> None:
        self._callbacks.append(callback)

    def remove_listener(self, callback: FrameCallback) -> None:
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit(self, frame: Any) -> None:
        for cb in list(self._callbacks):
            try:
                cb(frame)
            except Exception:
                pass

    def _listen_loop(self) -> None:
        while self._running:
            try:
                for p in self._comm.receive():
                    self._emit(p)
                time.sleep(0.01)
            except Exception:
                time.sleep(0.1)

    def receive_frames(self) -> Iterable[Any]:
        queue: List[Any] = []
        def _collector(frame: Any) -> None:
            queue.append(frame)
        self.add_listener(_collector)
        try:
            while self._running:
                while queue:
                    yield queue.pop(0)
                time.sleep(0.01)
        finally:
            self.remove_listener(_collector)

communicator = Communicator(
    port=os.environ.get("SERIAL_PORT", "/dev/ttyUSB0"),
    baudrate=57600,
)

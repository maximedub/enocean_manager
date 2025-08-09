# enocean_manager/communicator.py
# -*- coding: utf-8 -*-
"""
Couche de communication bas-niveau (ex: série USB300/TCM).
Ajouts :
- registre de callbacks pour écouter toutes les trames entrantes (sniffer léger)
- générateur receive_frames() pour itérer facilement dans pairing.py
"""

from __future__ import annotations  # Annotations futures
import threading  # Thread d'écoute asynchrone
import time  # Temporisation simple
import os
from typing import Callable, Iterable, Optional, List, Any  # Types

# NOTE : Les imports réels de ta pile EnOcean restent inchangés.
# Exemple (à adapter selon ta lib) :
# from enocean.protocol.packet import Packet
# from enocean.consolelogger import init_logger
# from enocean.communicators.serial import SerialCommunicator

try:
    from enocean.protocol.packet import Packet  # type: ignore
    from enocean.communicators.serial import SerialCommunicator  # type: ignore
except Exception:
    # Fallback minimal si la lib n'est pas dispo au moment de l'import
    Packet = Any  # type: ignore
    SerialCommunicator = object  # type: ignore


FrameCallback = Callable[[Any], None]  # Signature d'un callback trame


class Communicator:
    """Gère la connexion et l'écoute du dongle EnOcean (USB/TCM)."""

    def __init__(self, port: Optional[str] = None, baudrate: int = 57600) -> None:
        # Port série (ex : "/dev/ttyUSB0"), None -> autodétection si lib le gère
        self.sender_id = None
        self.port = port
        self.baudrate = baudrate
        # Instance du communicateur de la lib python-enocean (ou équivalent)
        self._comm = SerialCommunicator(port=self.port, baudrate=self.baudrate)
        # Gestion simple des callbacks d'écoute
        self._callbacks: List[FrameCallback] = []
        # Thread d'écoute
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Démarre la communication et le thread d'écoute."""
        if self._running:
            return
        self._comm.start()  # Ouvre le port et lance l’écoute bas-niveau
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Arrête proprement l’écoute et ferme le port série."""
        self._running = False
        try:
            self._comm.stop()
        finally:
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            self._thread = None

    def send(self, packet: Any) -> None:
        """Envoie une trame via le dongle."""
        self._comm.send(packet)

    def add_listener(self, callback: FrameCallback) -> None:
        """Enregistre un callback appelé pour chaque trame entrante."""
        self._callbacks.append(callback)

    def remove_listener(self, callback: FrameCallback) -> None:
        """Désenregistre un callback d’écoute."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit(self, frame: Any) -> None:
        """Diffuse la trame à tous les callbacks enregistrés."""
        for cb in list(self._callbacks):
            try:
                cb(frame)
            except Exception:
                # On ignore les erreurs de callback pour ne pas casser l’écoute
                pass

    def _listen_loop(self) -> None:
        """
        Boucle d'écoute qui récupère les trames de la lib et les diffuse.
        S'appuie sur l'API iterator() de python-enocean si présente.
        """
        # La lib python-enocean expose souvent un itérateur sur les frames reçues
        while self._running:
            try:
                for p in self._comm.receive():
                    # p est une instance Packet (ou équivalent)
                    self._emit(p)
                # Petite pause pour éviter l'utilisation CPU inutile
                time.sleep(0.01)
            except Exception:
                # On ne tue pas le thread pour une exception ; log à ajouter si besoin
                time.sleep(0.1)

    def receive_frames(self) -> Iterable[Any]:
        """
        Générateur pratique : permet d'itérer sur toutes les trames entrantes
        sans passer par des callbacks (utilisé par pairing.py).
        """
        queue: List[Any] = []

        def _collector(frame: Any) -> None:
            queue.append(frame)

        self.add_listener(_collector)
        try:
            while self._running:
                # Vide la file et renvoie les trames une par une
                while queue:
                    yield queue.pop(0)
                time.sleep(0.01)
        finally:
            self.remove_listener(_collector)
communicator = Communicator(
    port=os.environ.get("SERIAL_PORT", "/dev/ttyUSB0"),
    baudrate=57600,
)

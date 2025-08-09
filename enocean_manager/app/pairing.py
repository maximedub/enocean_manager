# pairing.py
# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Optional, Dict, Any
import time
from communicator import Communicator
from eep import EEPRegistry, EEPProfile

RORG_UTE = 0xD4
RORG_VLD = 0xD2
RORG_4BS = 0xA5
RORG_RPS = 0xF6

class PairingManager:
    def __init__(self, comm: Communicator, eep_registry: Optional[EEPRegistry] = None) -> None:
        self.comm = comm
        self.registry = eep_registry or EEPRegistry()

    def _maybe_extract_eep_code(self, frame: Any) -> Optional[str]:
        try:
            rorg = int(getattr(frame, "rorg", -1))
            if rorg == RORG_UTE:
                data = getattr(frame, "data", None) or []
                if len(data) >= 4:
                    func_hex = f"{data[1]:02X}"
                    type_hex = f"{data[2]:02X}"
                    return f"D2-{func_hex}-{type_hex}"
            if rorg in (RORG_VLD, RORG_4BS):
                return None
        except Exception:
            return None
        return None

    def _frame_to_info(self, frame: Any) -> Dict[str, Any]:
        info: Dict[str, Any] = {}
        emitter = getattr(frame, "sender", None) or getattr(frame, "address", None)
        if emitter is not None:
            try:
                if isinstance(emitter, int):
                    info["device_id"] = f"{emitter:08X}"
                elif isinstance(emitter, (bytes, bytearray)) and len(emitter) == 4:
                    info["device_id"] = emitter.hex().upper()
                else:
                    info["device_id"] = str(emitter).upper().replace("0X", "")
            except Exception:
                info["device_id"] = str(emitter)

        try:
            rorg = int(getattr(frame, "rorg", -1))
            if rorg >= 0:
                info["rorg"] = f"{rorg:02X}"
        except Exception:
            pass

        eep = self._maybe_extract_eep_code(frame)
        if eep:
            info["eep_code"] = eep
        return info

    def listen_for_teach_in(self, timeout: Optional[float] = 60.0) -> Optional[Dict[str, Any]]:
        start = time.time()
        for frame in self.comm.receive_frames():
            info = self._frame_to_info(frame)
            rorg_hex = info.get("rorg")
            is_teach_in = rorg_hex in {"D4"}
            if is_teach_in:
                eep_code = info.get("eep_code")
                if eep_code and self.registry.exists(eep_code):
                    p: EEPProfile = self.registry.load(eep_code)
                    info["profile_description"] = p.description
                    info["supported_commands"] = p.get_supported_commands()
                    info["supported_states"] = p.get_supported_states()
                    info["parameters"] = p.get_parameters()
                return info
            if timeout is not None and (time.time() - start) > timeout:
                return None
        return None

import time
import struct
import serial
from typing import Tuple, Optional, Dict

ESP3_PKT_TYPE_RADIO_ERP1 = 0x01
ESP3_PKT_TYPE_COMMON_CMD = 0x05

RORG_UTE = 0xD4
RORG_A5  = 0xA5
RORG_D2  = 0xD2

# ---- CRC8 (ESP3) ----
def crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def build_erp1_frame(rorg: int, data: bytes, sender_id: bytes, status: int = 0x00, opt_data: bytes = b"") -> bytes:
    assert len(sender_id) == 4
    body = bytes([rorg]) + data + sender_id + bytes([status])
    data_len = len(body)
    opt_len  = len(opt_data)
    header = struct.pack(">HBB", data_len, opt_len, ESP3_PKT_TYPE_RADIO_ERP1)
    crc_h  = bytes([crc8(header)])
    pkt = b"\x55" + header + crc_h + body + opt_data
    crc_d = bytes([crc8(body + opt_data)])
    return pkt + crc_d

# ---- ESP3 Common Command: CO_RD_IDBASE (0x08) ----
def build_common_cmd(cmd: int, payload: bytes = b"") -> bytes:
    data_len = len(payload) + 1  # includes command byte
    opt_len  = 0
    header = struct.pack(">HBB", data_len, opt_len, ESP3_PKT_TYPE_COMMON_CMD)
    crc_h  = bytes([crc8(header)])
    body = bytes([cmd]) + payload
    pkt = b"\x55" + header + crc_h + body
    crc_d = bytes([crc8(body)])
    return pkt + crc_d

def parse_esp3_frame(port: serial.Serial, timeout_s: float = 2.0) -> Optional[Dict]:
    # minimal parser to get ERP1 frames
    start = time.time()
    while time.time() - start < timeout_s:
        b = port.read(1)
        if b != b'\x55':
            continue
        header = port.read(4)  # data_len(2), opt_len(1), pkt_type(1)
        if len(header) < 4:
            continue
        data_len = (header[0] << 8) | header[1]
        opt_len  = header[2]
        pkt_type = header[3]
        crc_h    = port.read(1)
        # skip CRC validation for header simplicity (or validate)
        data     = port.read(data_len)
        opt      = port.read(opt_len)
        crc_d    = port.read(1)
        return {
            "pkt_type": pkt_type,
            "data": data,
            "opt": opt
        }
    return None

def read_base_id(serial_port: str, baud: int = 57600) -> bytes:
    with serial.Serial(serial_port, baudrate=baud, timeout=2) as ser:
        # CO_RD_IDBASE = 0x08
        ser.write(build_common_cmd(0x08))
        ser.flush()
        # Read response
        resp = parse_esp3_frame(ser, timeout_s=2.0)
        if not resp or resp["pkt_type"] != ESP3_PKT_TYPE_COMMON_CMD:
            # Fallback : unknown
            raise RuntimeError("Impossible de lire le Base ID via ESP3.")
        # Réponse attendue: data[0]=0x08 (cmd), data[1]=RET_CODE, data[2:6]=BaseID
        data = resp["data"]
        if len(data) < 7 or data[1] != 0x00:
            raise RuntimeError("Réponse CO_RD_IDBASE invalide.")
        base_id = data[2:6]
        return base_id

def bytes_id_to_str(b: bytes) -> str:
    return ":".join(f"{x:02X}" for x in b)

def str_id_to_bytes(s: str) -> bytes:
    parts = s.replace("-", ":").split(":")
    if len(parts) != 4:
        raise ValueError("ID attendu sur 4 octets, ex: 05:97:9C:FA")
    return bytes(int(p, 16) for p in parts)

# ---- Ecoute Teach-In AUTO ----
def listen_teach_in(serial_port: str, timeout: int = 12, baud: int = 57600) -> Optional[Dict]:
    """
    Écoute les trames pendant `timeout` secondes pour détecter un Teach-In/identification.
    Retourne { "rorg": 0xD2/0xA5..., "id": "AA:BB:CC:DD" } si on déduit un device (même si certains émettent pas un vrai UTE).
    """
    with serial.Serial(serial_port, baudrate=baud, timeout=0.2) as ser:
        start = time.time()
        while time.time() - start < timeout:
            f = parse_esp3_frame(ser, timeout_s=0.5)
            if not f or f["pkt_type"] != ESP3_PKT_TYPE_RADIO_ERP1:
                continue
            data = f["data"]
            if len(data) < 1 + 4 + 1:
                continue
            rorg   = data[0]
            sender = data[-5:-1]
            # Heuristique : si on voit D2 (actionneur) ou A5 (capteurs) on récupère l'ID.
            if rorg in (RORG_D2, RORG_A5, RORG_UTE):
                return {
                    "rorg": rorg,
                    "id": bytes_id_to_str(sender)
                }
    return None

# ---- Envoi UTE (FORCE) ----
def teachin_ute(serial_port: str, sender_base_id: bytes, target_id: bytes,
                eep_rorg: int, eep_func: int, eep_type: int, manufacturer_id: int = 0xFFFF,
                channel: int = 0, baud: int = 57600) -> None:
    """
    Construit un ERP1 UTE minimal pour annoncer l'EEP au récepteur.
    DATA UTE (simplifié/générique) = [FUNC, TYPE, MANUF_H, MANUF_L, REQ(0x00), CHANNEL, EEP_RORG] + TARGET_ID(4)
    Certains fabricants exigent d'autres flags/champs. Adapter si besoin.
    """
    payload = bytes([
        eep_func & 0xFF,
        eep_type & 0xFF,
        (manufacturer_id >> 8) & 0xFF,
        manufacturer_id & 0xFF,
        0x00,                 # Request Teach-In
        channel & 0xFF,
        eep_rorg & 0xFF
    ]) + target_id

    frame = build_erp1_frame(
        rorg=RORG_UTE,
        data=payload,
        sender_id=sender_base_id,
        status=0x00,
        opt_data=b""
    )

    with serial.Serial(serial_port, baudrate=baud, timeout=2) as ser:
        ser.write(frame)
        ser.flush()
        # on tente de lire un ACK ESP3 basique (non bloquant)
        time.sleep(0.1)


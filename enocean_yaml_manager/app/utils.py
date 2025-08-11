# Fonctions utilitaires : conversions d'ID et formats YAML attendus par HA.
from typing import List

def hex_str_normalize(hex_str: str) -> str:
    """Normalise un ID hexa : supprime '0x', ':', espaces ; renvoie en MAJ."""
    s = (hex_str or "").replace("0x","").replace(":","").replace(" ","").strip()
    return s.upper()

def hex_str_to_bytes_list(hex_str: str) -> List[int]:
    """
    Convertit '0595DD72' → [0x05,0x95,0xDD,0x72].
    Autorise chaîne vide (utile pour light sans dev_id), sinon 8 hex requis.
    """
    s = hex_str_normalize(hex_str)
    if s == "":
        return []
    if len(s) != 8:
        raise ValueError("Un ID EnOcean fait 4 octets (8 hex). Exemple: 0595DD72")
    return [int(s[i:i+2], 16) for i in range(0, 8, 2)]

def bytes_list_to_yaml_list(b: List[int]) -> List[int]:
    """Home Assistant attend une liste d'entiers (base 10)."""
    return [int(x) for x in (b or [])]

def bytes_list_to_hex_str(b: List[int]) -> str:
    """Convertit [5,149,221,114] → '0595DD72'."""
    return "".join(f"{x:02X}" for x in (b or []))

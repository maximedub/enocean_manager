import json
import os
from typing import Tuple

def load_eep(eep_dir: str, eep_code: str) -> Tuple[int,int,int]:
    """
    Lit un fichier JSON EEP (ex. D2-01-12.json) et renvoie (rorg, func, type) en int.
    Le fichier peut spécifier le code "eep": "D2-01-12" ou les champs séparés.
    """
    norm = eep_code.strip().upper().replace("_", "-")
    path = os.path.join(eep_dir, f"{norm}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"EEP JSON introuvable: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Essayer via "profile.eep"
    prof = data.get("profile", {})
    eep = prof.get("eep", norm)
    parts = eep.split("-")
    if len(parts) == 3:
        rorg = int(parts[0], 16)
        func = int(parts[1], 16)
        typ  = int(parts[2], 16)
        return rorg, func, typ

    # fallback si structure différente
    raise ValueError(f"EEP non lisible dans JSON: {path}")


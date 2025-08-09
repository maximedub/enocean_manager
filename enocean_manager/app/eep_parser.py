# app/eep_parser.py
import os
from .eep import EEPRegistry

# Dossier des JSON (monté par l’add-on, ex: /data/profile_json)
_EEP_DIR = os.environ.get("EEP_JSON_DIR", "/data/profile_json")
_registry = EEPRegistry(base_dir=_EEP_DIR)

def download_eep_file(local_only: bool = False) -> str:
    # Ici, si tu veux télécharger/mettre à jour les JSON, fais-le.
    # Pour l’instant on renvoie juste le dossier utilisé.
    return _EEP_DIR

def parse_eep_file(eep_code: str | None = None):
    """
    Si eep_code est fourni: renvoie le profil JSON chargé.
    Sinon: expose la liste des codes disponibles.
    """
    if eep_code:
        profile = _registry.load(eep_code)
        return {
            "code": profile.code,
            "description": profile.description,
            "rorg": profile.rorg,
            "func": profile.func,
            "type": profile.type,
            "commands": profile.get_supported_commands(),
            "states": profile.get_supported_states(),
            "parameters": profile.get_parameters(),
            "teach_in": profile.get_teach_in_info(),
        }
    else:
        return {"available": _registry.list_codes()}

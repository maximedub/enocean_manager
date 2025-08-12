# Charge les fichiers EEP JSON (placés dans /app/eep) et expose
# - list_eep(): liste des profils {eep, title, channel_min, channel_max}
# - get_eep(eep): profil complet + range canaux
#
# Les JSON proviennent du site EnOcean (ex. D2-01-12.json). On extrait
# la range des canaux depuis le FunctionGroup "Actuator Set Output" (direction "to")
# sur la clé "channel".
#
# Exemple joint (D2-01-12.json) : titre, range 0..1, etc. :contentReference[oaicite:3]{index=3}
import json
import os
from typing import Dict, Any, List, Optional, Tuple

EEP_DIR = "/app/eep"

_cache: Dict[str, Dict[str, Any]] = {}     # eep -> contenu JSON
_index: Dict[str, Dict[str, Any]] = {}     # eep -> {title, channel_min, channel_max}

def _find_channel_range(profile: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
    """Parcourt functionGroups pour retrouver 'channel.range' dans les fonctions 'to'."""
    groups = (profile.get("profile", {}) or {}).get("functionGroups", []) or []
    chan_min: Optional[int] = None
    chan_max: Optional[int] = None
    for g in groups:
        if g.get("direction") != "to":
            continue
        for fn in (g.get("functions") or []):
            if fn.get("key") != "channel":
                continue
            for v in (fn.get("values") or []):
                rng = v.get("range")
                if rng and "min" in rng and "max" in rng:
                    chan_min = int(rng["min"])
                    chan_max = int(rng["max"])
                    return chan_min, chan_max
    return chan_min, chan_max

def _index_one(path: str) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        eep = data.get("profile", {}).get("eep")
        title = data.get("profile", {}).get("title")
        if not eep:
            return
        _cache[eep] = data
        cmin, cmax = _find_channel_range(data)
        _index[eep] = {
            "eep": eep,
            "title": title or eep,
            "channel_min": cmin,
            "channel_max": cmax,
        }
    except Exception:
        # On ignore silencieusement les JSON invalides
        pass

def _ensure_loaded() -> None:
    if _index:
        return
    if not os.path.isdir(EEP_DIR):
        return
    for name in os.listdir(EEP_DIR):
        if not name.lower().endswith(".json"):
            continue
        _index_one(os.path.join(EEP_DIR, name))

def list_eep() -> List[Dict[str, Any]]:
    """Liste {eep, title, channel_min, channel_max}."""
    _ensure_loaded()
    # Tri par code EEP
    return sorted(_index.values(), key=lambda x: x["eep"])

def get_eep(eep: str) -> Optional[Dict[str, Any]]:
    """Retourne le profil complet + méta (ajoute channel_min/max)."""
    _ensure_loaded()
    data = _cache.get(eep)
    if not data:
        return None
    meta = _index.get(eep, {})
    out = dict(data)
    out["_meta"] = meta
    return out

def suggest_channels(eep: str) -> List[int]:
    """Propose une liste de canaux par défaut d'après la range EEP."""
    prof = get_eep(eep)
    if not prof:
        return []
    meta = prof.get("_meta", {})
    cmin = meta.get("channel_min")
    cmax = meta.get("channel_max")
    if cmin is None or cmax is None:
        return []
    return list(range(int(cmin), int(cmax) + 1))

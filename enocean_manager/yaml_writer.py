from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from pathlib import Path
from typing import Dict

PACKAGES_PATH = Path("/config/packages")
PACKAGES_PATH.mkdir(parents=True, exist_ok=True)
TARGET_FILE = PACKAGES_PATH / "enocean_auto.yaml"

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)

def _ensure_list(m: CommentedMap, key: str):
    if key not in m or not isinstance(m[key], CommentedSeq):
        m[key] = CommentedSeq()
    return m[key]

def _has_switch_entry(seq: CommentedSeq, entry: Dict) -> bool:
    for it in seq:
        if not isinstance(it, dict):
            continue
        # On déduplique par (platform, id, channel, name)
        if it.get("platform") == entry.get("platform") and \
           it.get("id") == entry.get("id") and \
           it.get("channel") == entry.get("channel"):
            return True
    return False

def add_switch_dual(id_str: str, name_prefix: str) -> None:
    """
    Ajoute deux entrées switch enocean (channel 0 et 1) pour un actionneur 2 sorties.
    id_str: "05:97:9C:FA"
    """
    if TARGET_FILE.exists():
        data = yaml.load(TARGET_FILE.read_text(encoding="utf-8"))
        if data is None:
            data = CommentedMap()
    else:
        data = CommentedMap()

    switch_list = _ensure_list(data, "switch")

    # Format attendu par HA : id: [0xAA, 0xBB, 0xCC, 0xDD]
    parts = [f"0x{p}" for p in id_str.split(":")]
    id_arr = f"[{', '.join(parts)}]"

    for ch in (0, 1):
        entry = CommentedMap()
        entry["platform"] = "enocean"
        entry["name"] = f"{name_prefix} (Canal {ch+1})"
        entry["id"] = id_arr
        entry["channel"] = ch
        if not _has_switch_entry(switch_list, entry):
            switch_list.append(entry)

    with TARGET_FILE.open("w", encoding="utf-8") as f:
        yaml.dump(data, f)


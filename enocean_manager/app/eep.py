# eep.py
# -*- coding: utf-8 -*-
from __future__ import annotations
import os, json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Dict, List, Optional

DEFAULT_EEP_DIR = os.environ.get("EEP_JSON_DIR") or os.path.join(
    os.path.dirname(__file__), "profile_json"
)

class EEPNotFoundError(FileNotFoundError): pass
class EEPInvalidError(ValueError): pass

def _normalize_code(eep_code: str) -> str:
    return eep_code.strip().upper().replace("_", "-")

def _code_to_filename(eep_code: str) -> str:
    return f"{_normalize_code(eep_code)}.json"

@dataclass
class EEPProfile:
    code: str
    raw: Dict[str, Any]
    rorg: str = field(default="")
    func: str = field(default="")
    type: str = field(default="")
    description: str = field(default="")
    commands: List[Dict[str, Any]] = field(default_factory=list)
    states: List[Dict[str, Any]] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    teach_in: Dict[str, Any] = field(default_factory=dict)
    units: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, code: str, data: Dict[str, Any]) -> "EEPProfile":
        rorg = (data.get("rorg") or data.get("RORG") or "").strip().upper()
        func = (data.get("func") or data.get("FUNC") or "").strip().upper()
        typ  = (data.get("type") or data.get("TYPE") or "").strip().upper()
        desc = (data.get("description") or data.get("label") or data.get("name") or "").strip()
        if not (rorg and func and typ):
            raise EEPInvalidError(f"Profil EEP incomplet : rorg/func/type manquants dans {code}")
        return cls(
            code=_normalize_code(code), raw=data,
            rorg=rorg, func=func, type=typ, description=desc,
            commands=data.get("commands") or data.get("actions") or [],
            states=data.get("states") or data.get("channels") or [],
            parameters=data.get("parameters") or data.get("params") or {},
            teach_in=data.get("teach_in") or data.get("teachIn") or {},
            units=data.get("units") or {},
        )

    def get_supported_commands(self): return self.commands
    def get_supported_states(self):   return self.states
    def get_parameters(self):         return self.parameters
    def get_teach_in_info(self):      return self.teach_in

class EEPRegistry:
    def __init__(self, base_dir: Optional[str] = None) -> None:
        self.base_dir = base_dir or DEFAULT_EEP_DIR
        if not os.path.isdir(self.base_dir):
            raise FileNotFoundError(
                f"Dossier de profils EEP introuvable : {self.base_dir}. "
                f"Définis EEP_JSON_DIR ou place tes JSON dans {DEFAULT_EEP_DIR}."
            )

    def _path_for(self, eep_code: str) -> str:
        return os.path.join(self.base_dir, _code_to_filename(eep_code))

    @lru_cache(maxsize=512)
    def load(self, eep_code: str) -> EEPProfile:
        path = self._path_for(eep_code)
        if not os.path.isfile(path):
            raise EEPNotFoundError(f"Profil {eep_code} introuvable : {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return EEPProfile.from_json(_normalize_code(eep_code), data)

    def exists(self, eep_code: str) -> bool:
        return os.path.isfile(self._path_for(eep_code))

    def list_codes(self) -> List[str]:
        return sorted(
            os.path.splitext(n)[0].upper()
            for n in os.listdir(self.base_dir)
            if n.lower().endswith(".json")
        )

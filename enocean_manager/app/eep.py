# enocean_manager/eep.py
# -*- coding: utf-8 -*-
"""
Chargement et accès aux profils EEP au format JSON.
- Lecture par code EEP (ex : "D2-01-12")
- Mise en cache en mémoire
- Recherche utilitaire (par RORG/FUNC/TYPE)
- Accès aux sections utiles : commandes, paramètres, teach-in, unités, etc.

Le dossier des profils peut être défini par la variable d'environnement EEP_JSON_DIR.
Par défaut : chemin relatif "profiles_json" au sein du package.
"""

from __future__ import annotations  # Permet les annotations de types auto-référencées
import os  # Gestion des chemins et variables d'environnement
import json  # Lecture JSON
from dataclasses import dataclass, field  # Pour structurer les données proprement
from functools import lru_cache  # Cache mémoire simple et efficace
from typing import Any, Dict, List, Optional  # Types pour clarté


# Constante : sous-dossier par défaut où se trouvent les profils JSON
DEFAULT_EEP_DIR = os.environ.get("EEP_JSON_DIR") or os.path.join(
    os.path.dirname(__file__), "profiles_json"
)


class EEPNotFoundError(FileNotFoundError):
    """Erreur levée lorsqu'un profil EEP JSON n'est pas trouvé sur disque."""
    pass


class EEPInvalidError(ValueError):
    """Erreur levée lorsque le JSON du profil est invalide ou incomplet."""
    pass


def _normalize_code(eep_code: str) -> str:
    """Normalise un code EEP (ex: 'd2-01-12' -> 'D2-01-12')."""
    return eep_code.strip().upper().replace("_", "-")


def _code_to_filename(eep_code: str) -> str:
    """Convertit un code EEP en nom de fichier JSON (ex : D2-01-12.json)."""
    return f"{_normalize_code(eep_code)}.json"


@dataclass
class EEPProfile:
    """Représentation d'un profil EEP chargé depuis JSON."""
    code: str  # Code EEP "RORG-FUNC-TYPE" (ex: "D2-01-12")
    raw: Dict[str, Any]  # Contenu JSON brut pour accès intégral
    rorg: str = field(default="")
    func: str = field(default="")
    type: str = field(default="")
    description: str = field(default="")
    commands: List[Dict[str, Any]] = field(default_factory=list)  # Commandes supportées
    states: List[Dict[str, Any]] = field(default_factory=list)  # États/valeurs remontées
    parameters: Dict[str, Any] = field(default_factory=dict)  # Paramètres configurables
    teach_in: Dict[str, Any] = field(default_factory=dict)  # Informations teach-in (s'il y en a)
    units: Dict[str, Any] = field(default_factory=dict)  # Unités des champs (optionnel)

    @classmethod
    def from_json(cls, code: str, data: Dict[str, Any]) -> "EEPProfile":
        """
        Construit un profil depuis le JSON brut.
        Valide les champs de base et remplit les sections usuelles.
        """
        # Extraction robuste avec valeurs par défaut
        rorg = (data.get("rorg") or data.get("RORG") or "").strip().upper()
        func = (data.get("func") or data.get("FUNC") or "").strip().upper()
        typ = (data.get("type") or data.get("TYPE") or "").strip().upper()
        desc = (data.get("description") or data.get("label") or data.get("name") or "").strip()

        if not (rorg and func and typ):
            # Si les 3 identifiants ne sont pas présents, le JSON est insuffisant
            raise EEPInvalidError(
                f"Profil EEP incomplet : rorg/func/type manquants dans {code}"
            )

        # Sections optionnelles, les archives JSON EnOcean sont parfois hétérogènes
        commands = data.get("commands") or data.get("actions") or []
        states = data.get("states") or data.get("channels") or []
        parameters = data.get("parameters") or data.get("params") or {}
        teach_in = data.get("teach_in") or data.get("teachIn") or {}
        units = data.get("units") or {}

        return cls(
            code=_normalize_code(code),
            raw=data,
            rorg=rorg,
            func=func,
            type=typ,
            description=desc,
            commands=commands,
            states=states,
            parameters=parameters,
            teach_in=teach_in,
            units=units,
        )

    # -------- Méthodes utilitaires d'accès aux infos fréquentes -------- #

    def get_supported_commands(self) -> List[Dict[str, Any]]:
        """Retourne la liste des commandes/action utilisables (payloads, labels…)."""
        return self.commands

    def get_supported_states(self) -> List[Dict[str, Any]]:
        """Retourne la liste des états remontés (channels/sensors)."""
        return self.states

    def get_parameters(self) -> Dict[str, Any]:
        """Retourne les paramètres configurables du module."""
        return self.parameters

    def get_teach_in_info(self) -> Dict[str, Any]:
        """Retourne les informations liées au teach-in (RORG, payloads, filtres…)."""
        return self.teach_in


class EEPRegistry:
    """
    Registre de profils EEP stockés en JSON.
    - Charge à la demande avec cache
    - Permet de lister et rechercher par RORG/FUNC/TYPE
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        # Dossier de base où se trouvent les *.json
        self.base_dir = base_dir or DEFAULT_EEP_DIR
        # Vérifie l'existence au démarrage pour fournir un message clair
        if not os.path.isdir(self.base_dir):
            raise FileNotFoundError(
                f"Dossier de profils EEP introuvable : {self.base_dir}. "
                f"Définis EEP_JSON_DIR ou place tes JSON dans {DEFAULT_EEP_DIR}."
            )

    def _path_for(self, eep_code: str) -> str:
        """Renvoie le chemin absolu du fichier JSON pour ce code EEP."""
        return os.path.join(self.base_dir, _code_to_filename(eep_code))

    @lru_cache(maxsize=512)
    def load(self, eep_code: str) -> EEPProfile:
        """
        Charge un profil EEP depuis disque (avec cache).
        Lève EEPNotFoundError si le fichier est manquant.
        """
        path = self._path_for(eep_code)
        if not os.path.isfile(path):
            raise EEPNotFoundError(f"Profil {eep_code} introuvable : {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return EEPProfile.from_json(_normalize_code(eep_code), data)

    def exists(self, eep_code: str) -> bool:
        """True si le JSON du profil existe sur disque."""
        return os.path.isfile(self._path_for(eep_code))

    def list_codes(self) -> List[str]:
        """Liste tous les codes EEP disponibles (d’après les fichiers *.json)."""
        codes = []
        for name in os.listdir(self.base_dir):
            if not name.lower().endswith(".json"):
                continue
            codes.append(os.path.splitext(name)[0].upper())
        return sorted(codes)

    def search(self, rorg: Optional[str] = None,
               func: Optional[str] = None,
               typ: Optional[str] = None) -> List[str]:
        """
        Recherche approximative par RORG/FUNC/TYPE.
        Renvoie une liste de codes EEP correspondant.
        """
        rorg = (rorg or "").strip().upper()
        func = (func or "").strip().upper()
        typ = (typ or "").strip().upper()

        results: List[str] = []
        for code in self.list_codes():
            cr, cf, ct = code.split("-")
            if rorg and cr != rorg:
                continue
            if func and cf != func:
                continue
            if typ and ct != typ:
                continue
            results.append(code)
        return results

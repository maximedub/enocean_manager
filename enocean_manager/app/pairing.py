# enocean_manager/pairing.py
# -*- coding: utf-8 -*-
"""
Gestion de l'appairage (Teach-In) :
- Écoute des trames entrantes pour détecter automatiquement un teach-in
- Extraction des infos minimales (ID émetteur, éventuel code EEP)
- Intégration avec EEPRegistry (pour charger le profil s'il est connu)

Remarque : selon les appareils, le teach-in peut se faire via différents RORG (ex: UTE 0xD4, 4BS 0xA5, VLD 0xD2, RPS 0xF6).
Ce module implémente une détection générique et te laisse spécialiser si besoin.
"""

from __future__ import annotations  # Annotations futures
from typing import Optional, Dict, Any  # Types
import time  # Timeout d’écoute

from enocean_manager.communicator import Communicator  # Couche de com
from enocean_manager.eep import EEPRegistry, EEPProfile  # Accès aux profils JSON


# Quelques RORG usuels (valeurs hex) ; à adapter selon ta pile de trames
RORG_UTE = 0xD4  # Universal Teach-In (UTE)
RORG_VLD = 0xD2  # Variable Length Data (souvent D2-xx-xx)
RORG_4BS = 0xA5  # 4BS (A5-xx-xx)
RORG_RPS = 0xF6  # Rocker (F6-xx-xx)


class PairingManager:
    """Orchestre l’écoute teach-in et la résolution du profil EEP."""

    def __init__(self, comm: Communicator, eep_registry: Optional[EEPRegistry] = None) -> None:
        # Communicator pour écouter les trames
        self.comm = comm
        # Registre EEP (charge depuis JSON)
        self.registry = eep_registry or EEPRegistry()

    def _maybe_extract_eep_code(self, frame: Any) -> Optional[str]:
        """
        Tente d'extraire un code EEP "RORG-FUNC-TYPE" à partir d'une trame teach-in.
        Cette extraction dépend fortement de la lib et du device ; ici on fournit un
        squelette robuste que tu peux spécialiser avec ta pile Packet.
        """
        try:
            # Exemple générique : si la lib expose frame.rorg, frame.data[]
            rorg = int(getattr(frame, "rorg", -1))
            # Pour UTE (0xD4), le profil peut être inclus dans le payload teach-in
            if rorg == RORG_UTE:
                data = getattr(frame, "data", None) or []
                # Heuristique : certains JSON décrivent teachIn.eepFields -> RORG/FUNC/TYPE
                # Ici on illustre : data[1], data[2], data[3] contiendraient FUNC/TYPE approximatifs
                # À spécialiser quand tu confirmes la structure exacte côté lib.
                if len(data) >= 4:
                    # On ne peut pas deviner RORG uniquement via UTE ; on va tenter D2 ou A5 selon device
                    # Priorité : D2 (modules type actuateurs), puis A5 (capteurs 4BS)
                    # Tu peux ajouter une vraie lecture via teach-in payload si tes JSON la décrivent.
                    func_hex = f"{data[1]:02X}"
                    type_hex = f"{data[2]:02X}"
                    # Heuristique rapide (améliorable) : privilégie D2 si frame vient d’un actuateur
                    return f"D2-{func_hex}-{type_hex}"
            # Si la trame elle-même est déjà d’un RORG mappé (ex: D2, A5), on peut tenter un fallback
            if rorg in (RORG_VLD, RORG_4BS):
                # Sans fonction/type explicites, on ne peut pas conclure fermement.
                # On retourne None ici, la résolution pourra se faire via un mapping d’ID connu si tu en as un.
                return None
        except Exception:
            return None
        return None

    def _frame_to_info(self, frame: Any) -> Dict[str, Any]:
        """
        Simplifie une trame reçue en dictionnaire exploitable pour l'appairage.
        Retourne au minimum l'ID émetteur ; ajoute le code EEP si détectable.
        """
        info: Dict[str, Any] = {}
        # ID émetteur (ex: 0x0597495E). Le nom d’attribut varie selon la lib.
        emitter = getattr(frame, "sender", None) or getattr(frame, "address", None)
        if emitter is not None:
            # Format lisible : hex en majuscules sans '0x'
            try:
                if isinstance(emitter, int):
                    info["device_id"] = f"{emitter:08X}"
                elif isinstance(emitter, (bytes, bytearray)) and len(emitter) == 4:
                    info["device_id"] = emitter.hex().upper()
                else:
                    # Fallback : string déjà formatée par la lib
                    info["device_id"] = str(emitter).upper().replace("0X", "")
            except Exception:
                info["device_id"] = str(emitter)

        # Récupère le RORG si dispo
        try:
            rorg = int(getattr(frame, "rorg", -1))
            if rorg >= 0:
                info["rorg"] = f"{rorg:02X}"
        except Exception:
            pass

        # Tente d’extraire un code EEP
        eep = self._maybe_extract_eep_code(frame)
        if eep:
            info["eep_code"] = eep

        return info

    def listen_for_teach_in(self, timeout: Optional[float] = 60.0) -> Optional[Dict[str, Any]]:
        """
        Écoute les trames entrantes jusqu’à détecter une candidate teach-in.
        - timeout (secondes) : None pour écouter indéfiniment
        Retourne un dict avec au moins:
            { "device_id": "0597495E", "eep_code": "D2-01-12" (si trouvé), "rorg": "D2"/"A5"/"D4" }
        ou None si rien reçu avant timeout.
        """
        start = time.time()
        for frame in self.comm.receive_frames():
            # Construit une info simplifiée depuis la trame
            info = self._frame_to_info(frame)

            # Critères minimalistes de "teach-in probable"
            # - si RORG est UTE (0xD4) : souvent teach-in
            # - ou si trame contient un flag teach-in (à spécialiser selon ta lib/JSON)
            rorg_hex = info.get("rorg")
            is_teach_in = rorg_hex in {"D4"}  # Heuristique simple ; complète au besoin

            # On accepte aussi le cas où le JSON de profil a un teach-in "pattern" connu (à implémenter si nécessaire)

            if is_teach_in:
                # Si on détecte un EEP, on tente de charger le profil
                eep_code = info.get("eep_code")
                if eep_code and self.registry.exists(eep_code):
                    profile: EEPProfile = self.registry.load(eep_code)
                    info["profile_description"] = profile.description
                    info["supported_commands"] = profile.get_supported_commands()
                    info["supported_states"] = profile.get_supported_states()
                    info["parameters"] = profile.get_parameters()
                return info

            # Gestion du timeout
            if timeout is not None and (time.time() - start) > timeout:
                return None

        # Si receive_frames() s'arrête (comm.stop), on retourne None
        return None

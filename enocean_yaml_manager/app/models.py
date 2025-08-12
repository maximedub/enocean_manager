# -*- coding: utf-8 -*-
"""
Modèles Pydantic (v2) pour l'API de l'add-on EnOcean YAML Manager.

Objectifs :
- Définir des schémas stables pour la saisie/édition en UI.
- Fournir des valeurs par défaut robustes (ex. emitter.kind).
- Normaliser les IDs (hex en MAJ, sans espaces).
- Rester compatibles avec d’anciens imports (alias ChannelConfig).

NOTE : Ces modèles servent à piloter l'export YAML conforme aux plateformes
Home Assistant "enocean" (switch/light/sensor/binary_sensor).
"""

from __future__ import annotations

from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class ChannelEmitter(BaseModel):
    """Émetteur associé à un canal d’un récepteur (optionnel côté UI)."""

    # ID hex de l’émetteur (ex "FFC43886" noté sur l’émetteur)
    id: str = Field(..., description="ID hexadécimal de l'émetteur (ex: FFC43886)")

    # Type d’entité HA pour l’émetteur (quand exposé dans HA) – défaut robuste
    kind: Literal["binary_sensor", "switch"] = Field(
        "binary_sensor",
        description="Type d'entité HA pour l'émetteur (défaut: binary_sensor)",
    )

    # Libellé d’affichage
    label: Optional[str] = Field(
        default=None,
        description="Libellé lisible pour l'émetteur (optionnel)",
    )

    @field_validator("id")
    @classmethod
    def _normalize_id(cls, v: str) -> str:
        """Met l’ID émetteur en MAJ et supprime les espaces parasites."""
        return (v or "").strip().upper()


class Channel(BaseModel):
    """Un canal d’un récepteur (actionneur) : ex. D2-01-xx canal 0/1/2…"""

    # Index de canal (>=0)
    channel: int = Field(..., ge=0, description="Index du canal (>=0)")

    # Libellé du canal
    label: str = Field(..., description="Libellé du canal")

    # Émetteur optionnel qui pilote CE canal (pratique pour le regroupement)
    emitter: Optional[ChannelEmitter] = Field(
        default=None, description="Émetteur optionnel attaché à ce canal"
    )


class LightSender(BaseModel):
    """Paramètres spécifiques aux lights EnOcean (sender obligatoire côté HA)."""

    # ID hex du sender (obligatoire pour light.platform: enocean)
    sender_id: str = Field(..., description="ID hexadécimal du sender (ex: FFC43886)")

    @field_validator("sender_id")
    @classmethod
    def _normalize_sender_id(cls, v: str) -> str:
        """Sender en MAJ sans espaces."""
        return (v or "").strip().upper()


class SensorOptions(BaseModel):
    """Options spécifiques aux capteurs (suivant ce que HA supporte)."""

    # Device class HA ("temperature", "humidity", "powersensor", "windowhandle")
    device_class: Optional[str] = Field(
        default=None, description="Classe de capteur HA (ex: temperature)"
    )
    # Unité libre (peu/pas utilisée par le schéma HA, laissée optionnelle)
    unit_of_measurement: Optional[str] = Field(
        default=None, description="Unité (optionnel)"
    )
    # Seuils/plages optionnels (certains device_class les utilisent)
    min_temp: Optional[float] = Field(default=None, description="Min (°C)")
    max_temp: Optional[float] = Field(default=None, description="Max (°C)")
    range_from: Optional[float] = Field(default=None, description="Plage depuis")
    range_to: Optional[float] = Field(default=None, description="Plage jusqu'à")


class Device(BaseModel):
    """
    Appareil principal décrit côté UI/registre :
    - id_hex : ID hex du récepteur (actionneur/senseur – ex: FFAABBCC)
    - ha_type : comment il est exposé dans HA (switch/light/sensor)
    - eep : profil EEP (optionnel, info)
    - channels : pour switch (canaux), chaque canal peut lier un émetteur
    - light_sender : pour light (sender_id obligatoire côté HA)
    - sensor_options : options spécifiques capteur (voir SensorOptions)
    """

    id_hex: str = Field(..., description="ID hex du récepteur (ex: FFAABBCC)")
    label: str = Field(..., description="Libellé affiché pour l'appareil")
    ha_type: Literal["switch", "light", "sensor"] = Field(..., description="Type HA")
    eep: Optional[str] = Field(default=None, description="EEP (optionnel)")
    channels: List[Channel] = Field(default_factory=list, description="Canaux (switch)")
    light_sender: Optional[LightSender] = Field(
        default=None, description="Paramètres 'light' (sender_id, ...)"
    )
    sensor_options: Optional[SensorOptions] = Field(
        default=None, description="Options capteur (device_class, ...)"
    )

    @field_validator("id_hex")
    @classmethod
    def _normalize_id_hex(cls, v: str) -> str:
        """Met l’ID récepteur en MAJ et supprime les espaces parasites."""
        return (v or "").strip().upper()

    @model_validator(mode="after")
    def _defaults_and_cleanup(self) -> "Device":
        """
        Filets de sécurité :
        - Assure une liste de canaux compacte (supprime None éventuels).
        - Laisse Pydantic appliquer le défaut 'binary_sensor' sur emitter.kind.
        """
        self.channels = [c for c in (self.channels or []) if c is not None]
        return self


class Registry(BaseModel):
    """
    Registre complet manipulé par l'API.

    Remarque : côté persistance YAML "config", on exporte généralement
    une liste de devices ; en mémoire, on est plus à l’aise avec un dict.
    """
    devices: Dict[str, Device] = Field(default_factory=dict)

    def model_dump(self, *args, **kwargs):
        """Expose un dump pydantic classique (compat avec le reste du code)."""
        return super().model_dump(*args, **kwargs)


# ---------------------------------------------------------------------------
# Compatibilité : certains scripts importent "ChannelConfig"
# On fournit un alias propre vers Channel pour éviter les ImportError.
# ---------------------------------------------------------------------------
ChannelConfig = Channel

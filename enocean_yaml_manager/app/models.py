# Modèles Pydantic (v2) pour la validation des payloads API
# ---------------------------------------------------------
# - Normalise la structure Device / Channel / Emitter
# - Définit des valeurs par défaut robustes (ex: emitter.kind)
# - Facilite l’export YAML (types bien cadrés)
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


class ChannelEmitter(BaseModel):
    """Décrit un émetteur lié à un canal (optionnel)."""
    id: str = Field(..., description="ID hexadécimal de l'émetteur (ex: FFC43886)")
    # IMPORTANT : valeur par défaut = "binary_sensor" pour éviter 422 si non fourni par l'UI
    kind: Literal["binary_sensor", "switch"] = Field(
        "binary_sensor",
        description="Type d'entité pour l'émetteur (binary_sensor ou switch)",
    )
    label: Optional[str] = Field(
        default=None,
        description="Libellé lisible de l'émetteur (optionnel)"
    )

    @field_validator("id")
    @classmethod
    def normalize_id(cls, v: str) -> str:
        """Force l'ID hex en majuscules sans espaces."""
        return (v or "").strip().upper()


class Channel(BaseModel):
    """Un canal d'un récepteur (ex: canal 0/1 d'un actionneur D2-01-xx)."""
    channel: int = Field(..., ge=0, description="Index du canal (>=0)")
    label: str = Field(..., description="Libellé du canal")
    emitter: Optional[ChannelEmitter] = Field(
        default=None,
        description="Émetteur (optionnel) qui pilote ce canal"
    )


class LightSender(BaseModel):
    """Paramètres spécifiques pour une light émulée par envoi (ex: D2 avec sender)."""
    sender_id: str = Field(..., description="ID hex du 'sender' utilisé pour la light")

    @field_validator("sender_id")
    @classmethod
    def normalize_sender_id(cls, v: str) -> str:
        return (v or "").strip().upper()


class SensorOptions(BaseModel):
    """Options spécifiques aux capteurs (device_class etc.)."""
    device_class: Optional[str] = Field(default=None, description="Classe du capteur (HA)")
    unit_of_measurement: Optional[str] = Field(default=None, description="Unité (optionnel)")
    min_temp: Optional[float] = Field(default=None, description="Min (optionnel)")
    max_temp: Optional[float] = Field(default=None, description="Max (optionnel)")
    range_from: Optional[float] = Field(default=None, description="Plage depuis (optionnel)")
    range_to: Optional[float] = Field(default=None, description="Plage jusqu'à (optionnel)")


class Device(BaseModel):
    """
    Appareil principal :
    - id_hex : ID du récepteur (ou device), ex: FFAABBCC
    - ha_type : comment on doit l'exposer dans Home Assistant (switch/light/sensor)
    - eep : profil EEP (optionnel, mais utile pour suggestions de canaux)
    - channels : canaux configurés (émetteur optionnel par canal)
    - light_sender / sensor_options : spécifiques selon ha_type
    """
    id_hex: str = Field(..., description="ID hex du récepteur")
    label: str = Field(..., description="Libellé lisible de l'appareil")
    ha_type: Literal["switch", "light", "sensor"] = Field(..., description="Type HA")
    eep: Optional[str] = Field(default=None, description="EEP (optionnel)")
    channels: List[Channel] = Field(default_factory=list, description="Canaux")
    light_sender: Optional[LightSender] = Field(default=None, description="Light sender (optionnel)")
    sensor_options: Optional[SensorOptions] = Field(default=None, description="Options capteur (optionnel)")

    @field_validator("id_hex")
    @classmethod
    def normalize_id_hex(cls, v: str) -> str:
        """ID du récepteur en majuscules sans espaces."""
        return (v or "").strip().upper()

    @model_validator(mode="after")
    def defaults_and_consistency(self) -> "Device":
        """
        Filets de sécurité :
        - si un emitter est fourni sans 'kind', pydantic l'a déjà fixé à 'binary_sensor'
        - supprime les canaux vides (défensif si jamais transmis)
        """
        self.channels = [c for c in (self.channels or []) if c is not None]
        return self


# ----- Structures utilitaires pour (dé)sérialiser le registre entier -----

class Registry(BaseModel):
    """Snapshot complet du registre côté add-on (clé -> Device)."""
    devices: dict[str, Device] = Field(default_factory=dict)

    def model_dump(self, *args, **kwargs):  # aide pour compat compatibilité
        return super().model_dump(*args, **kwargs)

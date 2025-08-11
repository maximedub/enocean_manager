# Modèles Pydantic : structures de données échangées via l'API
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field

# Types Home Assistant pris en charge par l'intégration EnOcean core
HAType = Literal["switch", "light", "sensor", "binary_sensor"]
SensorDeviceClass = Literal["temperature", "humidity", "powersensor", "windowhandle"]

class ChannelConfig(BaseModel):
    """Décrit un canal de switch et son éventuel émetteur associé (1 max par canal)."""
    channel: int = Field(..., ge=0)             # numéro de canal
    label: str = "Canal"                        # libellé utilisateur pour l'entité
    emitter_id: Optional[str] = None            # ID émetteur (hex) lié au canal
    emitter_kind: Optional[Literal["binary_sensor","switch"]] = None  # type entité créée
    emitter_label: Optional[str] = None         # libellé de l’émetteur

class LightSender(BaseModel):
    """Pour les lights, HA exige un sender_id (ID émetteur)."""
    sender_id: str                               # ex. "FFC6EA04"

class SensorOptions(BaseModel):
    """Options spécifiques aux capteurs, selon device_class."""
    device_class: SensorDeviceClass = "powersensor"
    min_temp: int = 0
    max_temp: int = 40
    range_from: int = 255
    range_to: int = 0

class Device(BaseModel):
    """Appareil EnOcean déclaré côté HA (récepteur ou capteur)."""
    id_hex: str                                  # ex. "0595DD72" ; peut être vide pour light sans dev_id
    label: str = "Appareil EnOcean"              # nom utilisateur
    ha_type: HAType = "switch"                   # plateforme HA ciblée
    channels: List[ChannelConfig] = []           # utile si ha_type == "switch"
    light_sender: Optional[LightSender] = None   # utile si ha_type == "light"
    sensor_options: Optional[SensorOptions] = None  # utile si ha_type == "sensor"

class Registry(BaseModel):
    """Registre complet des appareils (persisté en JSON dans /data)."""
    devices: Dict[str, Device] = {}              # clé = id_hex (uppercase) ou clé spéciale pour light sans dev_id

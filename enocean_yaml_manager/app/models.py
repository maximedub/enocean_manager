# Modèles Pydantic : structures de données échangées via l'API
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field

HAType = Literal["switch", "light", "sensor", "binary_sensor"]
SensorDeviceClass = Literal["temperature", "humidity", "powersensor", "windowhandle"]

class ChannelEmitter(BaseModel):
    """Décrit un émetteur lié à un canal."""
    id: str                                   # ID émetteur (hex)
    kind: Literal["binary_sensor","switch"]   # type d'entité HA pour l'émetteur
    label: Optional[str] = None               # libellé de l'émetteur

class ChannelConfig(BaseModel):
    """Configuration d’un canal de switch."""
    channel: int = Field(..., ge=0)           # numéro de canal
    label: str = "Canal"                      # libellé utilisateur
    emitter: Optional[ChannelEmitter] = None  # 1 émetteur max par canal

class LightSender(BaseModel):
    """Pour les lights, HA exige sender_id."""
    sender_id: str

class SensorOptions(BaseModel):
    """Options spécifiques aux capteurs, selon device_class."""
    device_class: SensorDeviceClass = "powersensor"
    min_temp: int = 0
    max_temp: int = 40
    range_from: int = 255
    range_to: int = 0

class Device(BaseModel):
    """Appareil EnOcean (récepteur ou capteur) géré par l'add-on."""
    id_hex: str                                  # ex. "0595DD72" ; peut être vide pour light sans dev_id
    label: str = "Appareil EnOcean"              # nom utilisateur
    ha_type: HAType = "switch"                   # switch | light | sensor | binary_sensor
    eep: Optional[str] = None                    # Code EEP (ex. "D2-01-12")
    channels: List[ChannelConfig] = []           # utile si ha_type == "switch"
    light_sender: Optional[LightSender] = None   # utile si ha_type == "light"
    sensor_options: Optional[SensorOptions] = None

class Registry(BaseModel):
    """Registre persistant de l'add-on."""
    devices: Dict[str, Device] = {}              # clé = id_hex (uppercase) ou clé spéciale pour light sans dev_id

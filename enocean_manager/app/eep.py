import os
from bs4 import BeautifulSoup
from typing import List, Dict

EEP_DIRECTORY = "/app/eep"
EEP_FILE_EXTENSION = ".xml"

def load_eep_profiles() -> List[Dict]:
    """
    Charge tous les fichiers EEP XML du répertoire défini et extrait les profils.
    """
    profiles = []
    if not os.path.isdir(EEP_DIRECTORY):
        return profiles

    for filename in os.listdir(EEP_DIRECTORY):
        if not filename.endswith(EEP_FILE_EXTENSION):
            continue
        path = os.path.join(EEP_DIRECTORY, filename)
        try:
            profiles.extend(parse_eep_file(path))
        except Exception as e:
            print(f"Erreur lors de l’analyse de {filename} : {e}")

    return profiles

def parse_eep_file(filepath: str) -> List[Dict]:
    """
    Analyse un fichier XML EEP et retourne une liste de profils avec champs et descriptions.
    """
    with open(filepath, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "xml")

    result = []

    profile = soup.find("profile")
    if not profile:
        return result

    eep = profile.find("eep").text if profile.find("eep") else "Inconnu"
    function = profile.find("functionname").text if profile.find("functionname") else "Sans nom"

    inputs = []
    for input_ in soup.find_all("input"):
        inputs.append(parse_field(input_))

    outputs = []
    for output in soup.find_all("output"):
        outputs.append(parse_field(output))

    result.append({
        "eep": eep,
        "fonction": function,
        "commandes": {
            "entrées": inputs,
            "sorties": outputs
        }
    })

    return result

def parse_field(tag) -> Dict:
    """
    Traduit un champ de type <input> ou <output> vers une structure lisible.
    """
    name = tag.find("fieldname").text if tag.find("fieldname") else "Champ inconnu"
    bitoffs = tag.find("bitoffs").text if tag.find("bitoffs") else "?"
    bitsize = tag.find("bitsize").text if tag.find("bitsize") else "?"
    value_desc = []

    for value in tag.find_all("value"):
        desc = value.find("description").text if value.find("description") else "?"
        value_desc.append(desc)

    return {
        "nom": name,
        "bit_offset": bitoffs,
        "taille_bits": bitsize,
        "valeurs": value_desc
    }


import os
from bs4 import BeautifulSoup

EEP_XML_DIRECTORY = "/app/eep"

class EEPDevice:
    def __init__(self, eep_code):
        """
        Initialise un périphérique EEP à partir de son code, ex : D2-01-0C
        """
        self.eep_code = eep_code.upper()
        self.filename = f"{self.eep_code}.xml"
        self.filepath = os.path.join(EEP_XML_DIRECTORY, self.filename)
        self.soup = None
        self.valid = os.path.exists(self.filepath)

        if self.valid:
            with open(self.filepath, "r", encoding="utf-8") as f:
                self.soup = BeautifulSoup(f, "xml")
        else:
            raise FileNotFoundError(f"Fichier EEP introuvable : {self.filename}")

    def get_title(self):
        return self._text("title")

    def get_function(self):
        return self._text("function")

    def get_description(self):
        return self._text("description")

    def get_manufacturer(self):
        return self._text("manufacturer")

    def get_type(self):
        return self._text("type")

    def get_profiles(self):
        profiles = []
        for p in self.soup.find_all("profile"):
            eep = p.find("eep").text if p.find("eep") else "???"
            func = p.find("functionname").text if p.find("functionname") else "???"
            type_ = p.find("typename").text if p.find("typename") else "???"
            profiles.append({
                "eep": eep,
                "function": func,
                "type": type_
            })
        return profiles

    def _text(self, tagname):
        tag = self.soup.find(tagname)
        return tag.text.strip() if tag else "?"

    def to_dict(self):
        return {
            "eep_code": self.eep_code,
            "title": self.get_title(),
            "function": self.get_function(),
            "description": self.get_description(),
            "manufacturer": self.get_manufacturer(),
            "type": self.get_type(),
            "profiles": self.get_profiles()
        }

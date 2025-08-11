# Service enocean :
https://github.com/home-assistant/core/tree/dev/homeassistant/components/enocean

# EnOcean Manager Add-ons (HA)

Ce dépôt contient l’add-on **EnOcean YAML Manager** qui génère deux fichiers :

- `/config/packages/enocean_auto.yaml` : configuration **HA** (consommée par l’intégration EnOcean)
- `/config/packages/enocean_yaml_config.yaml` : **groupements** lisibles (récepteurs ↔ émetteurs / canaux)

## Installation dans Home Assistant

1. Dans *Paramètres → Add-ons → Add-on store* (bouton en haut à droite) → **Repositories**  
2. Collez l’URL de ce dépôt Git **(HTTPS)** puis **Add** → le dépôt apparaît dans le Store.  
3. Installez **EnOcean YAML Manager** puis démarrez-le.  
4. Ouvrez l’UI via le bouton **OPEN WEB UI** (ou `http://<HA>:9123/ui`).

> Réf. : *Create an add-on repository* et *Common tasks – Installing a third-party add-on repository*. 

## Pré-requis Home Assistant

Activez les *packages* si vous utilisez `/config/packages` :
```yaml
homeassistant:
  packages: !include_dir_named packages

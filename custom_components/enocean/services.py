# custom_components/enocean/services.yaml
# Déclare les services pour l’UI HA (docs & sélecteurs). La logique est dans __init__.py / association.py.

association_listen:
  name: "Écoute association (Teach-in)"
  description: >
    Met le dongle en écoute pour détecter le prochain teach-in (UTE/4BS/F6).
    Si respond_ute = true et que le teach-in est de type UTE et que le Base ID est connu,
    l’intégration essayera d’envoyer la réponse d’association (si supportée par la pile).
    Publie un évènement 'enocean_association_found' avec { sender, rorg, raw }.
  fields:
    timeout:
      name: "Délai"
      description: "Durée d’écoute en secondes (5–60, défaut 15)."
      required: false
      default: 15
      selector:
        number:
          min: 5
          max: 60
          step: 1
          mode: slider
    respond_ute:
      name: "Répondre aux UTE"
      description: "Si possible, envoie la réponse d’association UTE."
      required: false
      default: true
      selector:
        boolean: {}

association_d2_teach:
  name: "Teach-in D2 (ON/OFF)"
  description: >
    Envoie un télégramme D2-01 (ON/OFF) vers un récepteur pendant sa fenêtre LRN,
    optionnellement sur un canal donné. Répéter plusieurs fois peut aider.
  fields:
    id:
      name: "ID du récepteur (4 octets)"
      description: 'Ex: [0x05, 0x97, 0x9C, 0xFA]'
      required: true
      selector:
        object: {}
    channel:
      name: "Canal"
      description: "Canal cible (0–15, défaut 0)."
      required: false
      default: 0
      selector:
        number:
          min: 0
          max: 15
          step: 1
    action:
      name: "Action"
      description: "Commande à envoyer."
      required: false
      default: "on"
      selector:
        select:
          options:
            - "on"
            - "off"
    repeats:
      name: "Répétitions"
      description: "Nombre d’envois (1–5, défaut 2)."
      required: false
      default: 2
      selector:
        number:
          min: 1
          max: 5
          step: 1

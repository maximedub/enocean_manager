# Déclare les schémas des services du custom component 'enocean'.
# Ces descriptions apparaîtront dans l’UI ("Outils de développement" > "Services").

association_listen:
  name: Écoute association (Teach-in)
  description: >
    Met le dongle en écoute et détecte le prochain teach-in (UTE/4BS/F6). 
    En cas de UTE, envoie automatiquement la réponse (si Base ID prêt).
    Publie un évènement 'enocean_association_found' avec {sender, rorg, raw}.
  fields:
    timeout:
      name: Délai
      description: Durée d’écoute en secondes (par défaut 15).
      example: 20
      required: false
      selector:
        number:
          min: 5
          max: 60
          step: 1
          mode: slider
    respond_ute:
      name: Répondre UTE
      description: Envoyer l’accusé de réception au teach-in UTE détecté.
      default: true
      required: false
      selector:
        boolean: {}

association_d2_teach:
  name: Teach-in D2 (ON/OFF)
  description: >
    Envoie un télégramme D2-01 (ON/OFF) sur un canal d’un actionneur (id).
    À lancer pendant que le module est en mode LRN pour qu’il apprenne le sender HA.
  fields:
    id:
      name: ID du récepteur (4 octets)
      description: ID EnOcean du module récepteur (liste d’octets).
      example: [0x05, 0x97, 0x9C, 0xFA]
      required: true
      selector:
        object: {}
    channel:
      name: Canal
      description: Canal (0 par défaut).
      required: false
      default: 0
      selector:
        number:
          min: 0
          max: 15
          step: 1
    action:
      name: Action
      description: ON ou OFF.
      required: false
      default: "on"
      selector:
        select:
          options:
            - "on"
            - "off"
    repeats:
      name: Répétitions
      description: Nombre d’envois (utile pendant LRN).
      required: false
      default: 2
      selector:
        number:
          min: 1
          max: 5
          step: 1

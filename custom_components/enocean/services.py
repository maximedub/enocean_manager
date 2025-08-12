# Déclaration des services pour Home Assistant (remplace services.py)

enocean_manager.associate:
  name: Associer (teach-in)
  description: Lance une association UTE avec un module EnOcean donné.
  fields:
    receiver_id:
      name: ID du module récepteur
      description: ID EnOcean du module cible (ex. 0x05,0x97,0x9C,0xFA).
      required: true
      example: "0x05,0x97,0x9C,0xFA"
      selector:
        text:
    channel:
      name: Canal (optionnel)
      description: Canal/sortie du module si applicable (0/1…).
      required: false
      example: 0
      selector:
        number:
          min: 0
          max: 7
          mode: box

enocean_manager.disassociate:
  name: Désassocier
  description: Envoie une demande de désappairage au module.
  fields:
    receiver_id:
      name: ID du module récepteur
      description: ID EnOcean du module cible (ex. 0x05,0x97,0x9C,0xFA).
      required: true
      selector:
        text:

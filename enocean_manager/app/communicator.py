from enocean.communicators.serialcommunicator import SerialCommunicator

# Port série EnOcean (à adapter si nécessaire)
PORT = '/dev/serial/by-id/usb-EnOcean_GmbH_EnOcean_USB_300_DC_FT4T6Q61-if00-port0'
SENDER_ID = [0xFF, 0xC6, 0xEA, 0x01]

# Communicateur unique accessible partout
communicator = SerialCommunicator(port=PORT)
communicator.port = PORT
communicator.sender_id = SENDER_ID

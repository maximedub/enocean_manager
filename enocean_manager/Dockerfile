name: "EnOcean Manager"
version: "1.0.0"
slug: "enocean_manager"
description: "Add-on Home Assistant pour gestion avancée EnOcean (profils EEP JSON)"
arch:
  - aarch64
  - armv7
  - amd64
startup: services
boot: auto
init: false
host_network: true
map:
  - config:rw
options:
  serial_port: "/dev/ttyUSB0"
  json_dir: "/data/profile_json"
schema:
  serial_port: str
  json_dir: str
image: "local/enocean_manager:{arch}"

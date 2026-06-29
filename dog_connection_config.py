# Configure how the SL1680 sends commands to the dog.
#
# Use "wired" for the shippable dog-mounted Ethernet link.
# Use "wireless" for handheld/demo operation over Wi-Fi.
COMMAND_TRANSPORT = "wired"

WIRED_DOG_HOST = "10.42.0.1"
WIRELESS_DOG_HOST = "192.168.123.46"
DOG_COMMAND_PORT = 5005
DOG_COMMAND_TIMEOUT_S = 2.0

# Static IPs for the direct Ethernet link.
BOARD_WIRED_IP = "10.42.0.2"
DOG_WIRED_IP = "10.42.0.1"

# DOA is intentionally a placeholder for now. The message protocol already
# carries doa_deg so the audio direction code can be added later.
DOA_ENABLED = False

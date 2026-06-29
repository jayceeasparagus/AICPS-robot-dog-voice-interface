#!/bin/sh
set -eu

systemctl disable dog-voice-receiver.service
echo "Dog voice receiver will not start on boot. Use dog_voice_on.sh when needed."

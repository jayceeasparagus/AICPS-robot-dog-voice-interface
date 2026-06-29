#!/bin/sh
set -eu

systemctl enable dog-wired-network.service
systemctl enable dog-voice-receiver.service
echo "Dog voice receiver will start on boot."

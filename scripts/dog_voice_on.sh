#!/bin/sh
set -eu

systemctl start dog-wired-network.service
systemctl start dog-voice-receiver.service
systemctl status dog-voice-receiver.service --no-pager

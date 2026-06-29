#!/bin/sh
set -eu

systemctl stop dog-voice-receiver.service
systemctl status dog-voice-receiver.service --no-pager || true

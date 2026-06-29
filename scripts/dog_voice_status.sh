#!/bin/sh
set -eu

systemctl status dog-wired-network.service --no-pager || true
systemctl status dog-voice-receiver.service --no-pager || true

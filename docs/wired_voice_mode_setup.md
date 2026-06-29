# Wired Voice Mode Setup

This is the shippable/default setup:

- SL1680 board runs `speech_to_dog.py` automatically when powered.
- Board uses wired Ethernet to reach the dog at `10.42.0.1`.
- Dog receiver is installed as a service, but it does not need to run unless voice mode is enabled.
- Messages are JSON and include a `doa_deg` field, which is `null` until DOA is integrated.

## Network

Direct Ethernet link:

```text
Board eth0: 10.42.0.2/24
Dog eth0:   10.42.0.1/24
Port:       5005
```

## Board Install

Run on the SL1680 board:

```sh
cd /home/aicps/robot-dog-voice-interface
cp deploy/systemd/board-wired-network.service /etc/systemd/system/
cp deploy/systemd/speech-to-dog.service /etc/systemd/system/
chmod +x scripts/board_set_wired_ip.sh
systemctl daemon-reload
systemctl enable board-wired-network.service
systemctl enable speech-to-dog.service
systemctl restart board-wired-network.service
systemctl restart speech-to-dog.service
```

Check:

```sh
ifconfig eth0
systemctl status board-wired-network.service
systemctl status speech-to-dog.service
```

## Dog Install

Run on the dog/Jetson:

```sh
cd /home/unitree/voice_interface
cp deploy/systemd/dog-wired-network.service /etc/systemd/system/
cp deploy/systemd/dog-voice-receiver.service /etc/systemd/system/
chmod +x scripts/dog_set_wired_ip.sh
chmod +x scripts/dog_voice_*.sh
systemctl daemon-reload
systemctl enable dog-wired-network.service
systemctl disable dog-voice-receiver.service
```

`dog-wired-network.service` may be enabled because it only assigns the static
Ethernet address. `dog-voice-receiver.service` should stay disabled by default
for a shared robot.

## Daily Dog Use

Turn voice mode on:

```sh
cd /home/unitree/voice_interface
sh scripts/dog_voice_on.sh
```

Turn voice mode off:

```sh
cd /home/unitree/voice_interface
sh scripts/dog_voice_off.sh
```

Check voice mode:

```sh
cd /home/unitree/voice_interface
sh scripts/dog_voice_status.sh
```

## Safe Test

On dog:

```sh
python3 dog_command_receiver.py --message-only
```

On board:

```sh
python3 board_command_sender.py check
```

Then test the full board pipeline:

```sh
python3 speech_to_dog.py
```

Say:

```text
go check
go stand
go stop
```

Only run the dog receiver without `--message-only` when you are ready for real commands.

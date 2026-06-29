import json
import time


VALID_COMMANDS = {
    "check",
    "stop",
    "stand",
    "sit",
    "stand_down",
    "recover",
    "walk_forward",
    "walk_backward",
    "walk_left",
    "walk_right",
    "rotate_left",
    "rotate_right",
    "release",
}


def normalize_command(command):
    return command.strip().lower()


def validate_command(command):
    command = normalize_command(command)
    if command not in VALID_COMMANDS:
        raise ValueError(
            "Invalid command '{}'. Valid commands: {}".format(
                command,
                ", ".join(sorted(VALID_COMMANDS)),
            )
        )
    return command


def build_command_message(
    command,
    source="voice",
    doa_deg=None,
    confidence=None,
    phrase=None,
):
    return {
        "type": "go2_command",
        "version": 1,
        "command": validate_command(command),
        "source": source,
        "doa_deg": doa_deg,
        "confidence": confidence,
        "phrase": phrase,
        "timestamp": time.time(),
    }


def encode_message(message):
    return (json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8")


def parse_command_message(raw_text):
    text = raw_text.strip()
    if not text:
        raise ValueError("Empty command message")

    if text.startswith("{"):
        payload = json.loads(text)
        command = validate_command(payload.get("command", ""))
        payload["command"] = command
        return payload

    command = validate_command(text)
    return build_command_message(command, source="plain_text")

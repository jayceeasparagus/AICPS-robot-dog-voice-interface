import queue
import re
import threading
import traceback

from board_command_sender import send_command as send_wired_command
from board_wireless_sender import send_command as send_wireless_command
from dog_connection_config import (
    COMMAND_TRANSPORT,
    DOG_COMMAND_PORT,
    DOG_COMMAND_TIMEOUT_S,
    WIRED_DOG_HOST,
    WIRELESS_DOG_HOST,
)
from qna_matcher import QnAMatcher
from speech_to_text.pipeline import SpeechToTextPipeline


WAKE_WORDS = ["go"]

TOKEN_TO_DOG_COMMAND = {
    "{go2_stop}": "stop",
    "{go2_stand}": "stand",
    "{go2_sit}": "sit",
    "{go2_stand_down}": "stand_down",
    "{go2_recover}": "recover",
    "{go2_walk_forward}": "walk_forward",
    "{go2_walk_backward}": "walk_backward",
    "{go2_walk_left}": "walk_left",
    "{go2_walk_right}": "walk_right",
    "{go2_rotate_left}": "rotate_left",
    "{go2_rotate_right}": "rotate_right",
}


def send_dog_command(command):
    if COMMAND_TRANSPORT == "wired":
        return send_wired_command(
            command,
            host=WIRED_DOG_HOST,
            port=DOG_COMMAND_PORT,
            timeout=DOG_COMMAND_TIMEOUT_S,
        )

    if COMMAND_TRANSPORT == "wireless":
        return send_wireless_command(
            command,
            host=WIRELESS_DOG_HOST,
            port=DOG_COMMAND_PORT,
            timeout=DOG_COMMAND_TIMEOUT_S,
        )

    raise ValueError("Unsupported COMMAND_TRANSPORT: {}".format(COMMAND_TRANSPORT))


class VoiceToDogAssistant:
    def __init__(self):
        self.awake = False
        self.latest_text = ""
        self.latest_command_text = ""
        self.latest_match = None

        self.command_queue = queue.Queue()
        self.running = True

        print("Loading QnA matcher...")
        self.matcher = QnAMatcher()
        print("QnA matcher ready.")

        self.worker_thread = threading.Thread(
            target=self.command_worker,
            daemon=True,
        )
        self.worker_thread.start()

    def normalize(self, text):
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def has_wake_word(self, text):
        text = self.normalize(text)
        words = text.split()

        for wake in WAKE_WORDS:
            wake = self.normalize(wake)
            wake_words = wake.split()

            if len(wake_words) == 1:
                if wake_words[0] in words:
                    return True
            elif wake in text:
                return True

        return False

    def remove_wake_word(self, text):
        text = self.normalize(text)

        for wake in WAKE_WORDS:
            wake = self.normalize(wake)
            text = text.replace(wake, "").strip()

        return text

    def enqueue_command(self, command_text):
        command_text = self.normalize(command_text)

        if not command_text:
            print("Empty command. Ignoring.")
            self.awake = False
            print("Ready for wake word.")
            return

        print("Queued command:", command_text)
        self.command_queue.put(command_text)

        self.awake = False
        print("Ready for wake word.")

    def command_worker(self):
        while self.running:
            try:
                command_text = self.command_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.latest_command_text = command_text

                print("\n==============================")
                print("COMMAND TEXT:", command_text)

                match = self.matcher.match(command_text)
                self.latest_match = match

                print("Best QnA question:", match["best_question"])
                print("Similarity:", round(match["score"], 3))
                print("Answer token:", match["answer"])

                if not match["matched"]:
                    print("Rejected: command not confident enough.")
                    continue

                dog_command = TOKEN_TO_DOG_COMMAND.get(match["answer"])
                if dog_command is None:
                    print("Rejected: unsupported dog command token:", match["answer"])
                    continue

                print("Sending dog command:", dog_command)
                response = send_dog_command(dog_command)
                print("Dog response:", response)
                print("==============================\n")

            except Exception:
                print("\n[COMMAND WORKER ERROR]")
                traceback.print_exc()

            finally:
                self.command_queue.task_done()
                print("Listening for wake word...")

    def handle_transcript(self, text, inference_time):
        try:
            if not text or not text.strip():
                return

            self.latest_text = text
            print(f"Heard: {text} ({inference_time * 1000:.0f} ms)")

            normalized_text = self.normalize(text)

            if self.has_wake_word(normalized_text):
                print("Wake word detected.")
                command_text = self.remove_wake_word(normalized_text)

                if command_text:
                    self.enqueue_command(command_text)
                else:
                    print("Waiting for command...")
                    self.awake = True

                return

            if self.awake:
                self.enqueue_command(normalized_text)
                return

            print("Ignoring speech before wake word.")

        except Exception:
            print("\n[TRANSCRIPT HANDLER ERROR]")
            traceback.print_exc()
            self.awake = False
            print("Ready for wake word.")

    def stop(self):
        self.running = False


def main():
    assistant = VoiceToDogAssistant()

    pipeline = SpeechToTextPipeline(
        model="base",
        handler=assistant.handle_transcript,
        echo=False,
    )

    print("\nVoice-to-dog assistant running.")
    print("Wake words:", WAKE_WORDS)
    print("Command transport:", COMMAND_TRANSPORT)
    if COMMAND_TRANSPORT == "wireless":
        print("Dog host:", WIRELESS_DOG_HOST)
    elif COMMAND_TRANSPORT == "wired":
        print("Dog host:", WIRED_DOG_HOST)
    print()
    print("Supported dog commands:")
    print("  stand")
    print("  sit")
    print("  stand down")
    print("  stop")
    print("  walk forward")
    print("  walk backward")
    print("  walk left")
    print("  walk right")
    print("  rotate left")
    print("  rotate right")
    print()
    print("Examples:")
    print("  go stand up")
    print("  go sit")
    print("  go stand down")
    print("  go stop")
    print("  go walk forward")
    print("  go rotate left")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        pipeline.run()
    except KeyboardInterrupt:
        print("\nStopping voice-to-dog assistant...")
    except Exception:
        print("\n[PIPELINE ERROR]")
        traceback.print_exc()
    finally:
        assistant.stop()
        print("Exited cleanly.")


if __name__ == "__main__":
    main()

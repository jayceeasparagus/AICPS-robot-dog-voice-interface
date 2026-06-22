import re
import queue
import threading
import traceback

from speech_to_text.pipeline import SpeechToTextPipeline
from qna_matcher import QnAMatcher


WAKE_WORDS = ["go"]


class VoiceRobotAssistant:
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
            daemon=True
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
            else:
                if wake in text:
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

        # Immediately reset so the voice pipeline can keep listening.
        self.awake = False
        print("Ready for wake word.")

    def command_worker(self):
        """
        Runs QnA matching separately from the STT callback.
        This prevents QnA/embedding/tool calls from blocking the speech loop.
        """

        while self.running:
            try:
                command_text = self.command_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            try:
                self.latest_command_text = command_text

                print("\n==============================")
                print("COMMAND TEXT:", command_text)

                print("[DEBUG] Starting QnA match...")
                result = self.matcher.match_and_run(command_text)
                print("[DEBUG] Finished QnA match.")

                self.latest_match = result

                print("MATCHED:", result["matched"])
                print("ACTION OUTPUT:", result["action_output"])
                print("==============================\n")

            except Exception:
                print("\n[COMMAND WORKER ERROR]")
                traceback.print_exc()

            finally:
                self.command_queue.task_done()
                print("Listening for wake word...")

    def handle_transcript(self, text, inference_time):
        """
        Called automatically every time Moonshine outputs text.
        Keep this function quick.
        """

        try:
            if not text or not text.strip():
                return

            self.latest_text = text

            print(f"Heard: {text} ({inference_time * 1000:.0f} ms)")

            normalized_text = self.normalize(text)

            # Case 1: wake word + command together
            # Example: "robot move forward"
            if self.has_wake_word(normalized_text):
                print("Wake word detected.")

                command_text = self.remove_wake_word(normalized_text)

                if command_text:
                    self.enqueue_command(command_text)
                else:
                    print("Waiting for command...")
                    self.awake = True

                return

            # Case 2: wake word was already heard
            # Example:
            #   "robot"
            #   "move forward"
            if self.awake:
                self.enqueue_command(normalized_text)
                return

            # Case 3: random speech before wake word
            print("Ignoring speech before wake word.")

        except Exception:
            print("\n[TRANSCRIPT HANDLER ERROR]")
            traceback.print_exc()
            self.awake = False
            print("Ready for wake word.")

    def stop(self):
        self.running = False


def main():
    assistant = VoiceRobotAssistant()

    pipeline = SpeechToTextPipeline(
        model="base",
        handler=assistant.handle_transcript,
        echo=False,
    )

    print("\nVoice robot assistant running.")
    print("Wake words:", WAKE_WORDS)
    print()
    print("Examples:")
    print("  robot")
    print("  move forward")
    print()
    print("Or:")
    print("  robot move forward")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        pipeline.run()

    except KeyboardInterrupt:
        print("\nStopping voice robot assistant...")

    except Exception:
        print("\n[PIPELINE ERROR]")
        traceback.print_exc()

    finally:
        assistant.stop()
        print("Exited cleanly.")


if __name__ == "__main__":
    main()

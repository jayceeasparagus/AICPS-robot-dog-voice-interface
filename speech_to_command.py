import re
import traceback

from speech_to_text.pipeline import SpeechToTextPipeline
from qna_matcher import QnAMatcher


WAKE_WORDS = ["on"]


class VoiceRobotAssistant:
    def __init__(self):
        self.awake = False
        self.latest_text = ""
        self.latest_command_text = ""
        self.latest_match = None

        print("Loading QnA matcher...")
        self.matcher = QnAMatcher()
        print("QnA matcher ready.")

    def normalize(self, text):
        text = text.lower().strip()
        text = re.sub(r"[^a-z0-9\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def has_wake_word(self, text):
        text = self.normalize(text)

        for wake in WAKE_WORDS:
            wake = self.normalize(wake)

            # Safer than: wake in text
            # This avoids matching "on" inside random words.
            words = text.split()
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

    def reset_after_command(self):
        """
        Always return to waiting-for-wake-word state after a command.
        """
        self.awake = False

    def process_command(self, command_text):
        """
        Speech command text -> QnA matcher -> robot command/tool output
        """

        try:
            command_text = self.normalize(command_text)

            if not command_text:
                print("Empty command. Ignoring.")
                self.reset_after_command()
                return

            self.latest_command_text = command_text

            print("\n==============================")
            print("COMMAND TEXT:", command_text)

            result = self.matcher.match_and_run(command_text)

            self.latest_match = result

            print("MATCHED:", result["matched"])
            print("ACTION OUTPUT:", result["action_output"])
            print("==============================\n")

        except Exception:
            print("\n[PROCESS COMMAND ERROR]")
            print("Something went wrong while processing the command.")
            traceback.print_exc()

        finally:
            # This is important.
            # Even if the command is unknown or errors, go back to wake-word mode.
            self.reset_after_command()

    def handle_transcript(self, text, inference_time):
        """
        Called automatically every time Moonshine outputs text.
        """

        try:
            if not text or not text.strip():
                return

            self.latest_text = text

            print(f"Heard: {text} ({inference_time * 1000:.0f} ms)")

            normalized_text = self.normalize(text)

            # Case 1:
            # User says wake word and command together:
            #   "on walk forward"
            if self.has_wake_word(normalized_text):
                print("Wake word detected.")

                command_text = self.remove_wake_word(normalized_text)

                if command_text:
                    self.process_command(command_text)
                else:
                    print("Waiting for command...")
                    self.awake = True

                return

            # Case 2:
            # User already said wake word.
            # Next transcript is the command.
            if self.awake:
                self.process_command(normalized_text)
                return

            # Case 3:
            # Speech before wake word.
            print("Ignoring speech before wake word.")

        except Exception:
            print("\n[TRANSCRIPT HANDLER ERROR]")
            print("Something went wrong inside handle_transcript().")
            traceback.print_exc()
            self.reset_after_command()


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
    print("  on")
    print("  walk forward")
    print()
    print("Or:")
    print("  on walk forward")
    print()
    print("Press Ctrl+C to stop.")
    print()

    try:
        pipeline.run()

    except KeyboardInterrupt:
        print("\nStopping voice robot assistant.")

    except Exception:
        print("\n[PIPELINE ERROR]")
        print("The speech pipeline crashed.")
        traceback.print_exc()


if __name__ == "__main__":
    main()

import os
import sys
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from utils.logger import logger


def main():
    logger.info("=== Dark App Factory Feedback ===")
    logger.info("The factory has delivered your app. How is it?")

    try:
        # Interactive prompts -- these are user-facing CLI, not log output.
        # Using input() is correct here since this is a questionnaire script.
        rating_str = input("Rate the vibe (1-10): ").strip()
        try:
            rating = int(rating_str)
            if not 1 <= rating <= 10:
                raise ValueError
        except ValueError:
            logger.warning("Invalid rating '%s', defaulting to 5", rating_str)
            rating = 5

        missing = input("What feature is missing? ").strip()
        broken = input("What looks broken/janky? ").strip()

        feedback = (
            f"\n## Feedback (Rating: {rating}/10)\n"
            f"- **Missing**: {missing}\n"
            f"- **Broken**: {broken}\n"
        )

        # Save to feedback.md
        with open("feedback.md", "a", encoding="utf-8") as f:
            f.write(feedback)

        # Append to vibe.md to influence next run
        with open("vibe.md", "a", encoding="utf-8") as f:
            f.write(f"\n\n> **User Feedback**: {missing}. Fix: {broken}.")

        logger.success("Feedback recorded. Next run will incorporate it.")
        input("Press Enter to close...")

    except KeyboardInterrupt:
        logger.info("Feedback skipped.")


if __name__ == "__main__":
    main()

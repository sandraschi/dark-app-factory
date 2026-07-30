import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from utils.logger import logger


def main():
    import glob

    logger.info("=== Dark App Factory Feedback ===")

    # Check if the most recent run failed
    last_verdict = ""
    critique_paths = sorted(glob.glob("critique.md"), key=os.path.getmtime, reverse=True)
    if critique_paths:
        with open(critique_paths[0], encoding="utf-8") as f:
            content = f.read()
            if "VERDICT: FAIL" in content:
                last_verdict = "FAIL"
            elif "VERDICT: PASS" in content:
                last_verdict = "PASS"

    if last_verdict == "FAIL":
        logger.info("The most recent build did not pass quality gate.")
        want_notes = input("Record notes for the next attempt? (y/N): ").strip().lower()
        if want_notes not in ("y", "yes"):
            logger.info("Skipping feedback.")
            return
    else:
        logger.info("The factory has delivered your app. How is it?")

    try:
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

        with open("feedback.md", "a", encoding="utf-8") as f:
            f.write(feedback)

        logger.success("Feedback recorded.")
        input("Press Enter to close...")

    except KeyboardInterrupt:
        logger.info("Feedback skipped.")


if __name__ == "__main__":
    main()

import os
import subprocess

from src.utils.logger import logger


class GitManager:
    """Handles Git initialization and commits for generated applications."""

    def __init__(self, target_dir: str):
        self.target_dir = target_dir

    def run_git(self, args: list) -> bool:
        """Helper to run git commands in the target directory."""
        try:
            subprocess.run(
                ["git", *args],
                cwd=self.target_dir,
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git Error: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("Git binary not found. Please install git.")
            return False

    def initialize(self):
        """Initializes a git repo and makes the first commit."""
        logger.info(f"Initializing Git repository in {self.target_dir}...")

        if os.path.exists(os.path.join(self.target_dir, ".git")):
            logger.warning("Git repository already exists. Skipping initialization.")
            return

        if self.run_git(["init"]):
            self.run_git(["add", "."])
            if self.run_git(["commit", "-m", "Initial build from Dark App Factory"]):
                logger.success("Git initialized and initial commit created.")
            else:
                logger.warning("Git init succeeded but failed to create initial commit.")

    def commit_changes(self, message: str):
        """Adds all changes and commits them."""
        self.run_git(["add", "."])
        if self.run_git(["commit", "-m", message]):
            logger.success(f"Changes committed: {message}")

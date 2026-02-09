"""Deploy generated HTML to GitHub Pages via git push."""

import logging
import os
import subprocess

import config

logger = logging.getLogger(__name__)


def deploy():
    """Push output directory to gh-pages branch on GitHub.

    The output/ directory is managed as a separate git worktree/repo
    that pushes to the gh-pages branch.
    """
    output_dir = config.OUTPUT_DIR

    # Initialize git repo in output/ if not already done
    git_dir = os.path.join(output_dir, ".git")
    if not os.path.exists(git_dir):
        logger.info("Initializing git repo in output/")
        _run_git(["init"], output_dir)
        _run_git(["checkout", "-b", "gh-pages"], output_dir)
        remote_url = f"https://github.com/{config.GITHUB_REPO}.git"
        _run_git(["remote", "add", "origin", remote_url], output_dir)

    # Stage all changes
    _run_git(["add", "-A"], output_dir)

    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=output_dir,
        capture_output=True,
    )
    if result.returncode == 0:
        logger.info("No changes to deploy")
        return False

    # Commit and push
    from datetime import datetime
    msg = f"Morning Wire — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    _run_git(["commit", "-m", msg], output_dir)

    try:
        _run_git(["push", "-u", "origin", "gh-pages", "--force"], output_dir)
        logger.info("Deployed to GitHub Pages: %s", config.GITHUB_PAGES_URL)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Push failed: %s", e)
        return False


def setup_repo():
    """One-time setup: create the GitHub repo if it doesn't exist."""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", config.GITHUB_REPO],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            logger.info("Creating GitHub repo %s", config.GITHUB_REPO)
            subprocess.run(
                ["gh", "repo", "create", config.GITHUB_REPO, "--public", "--description",
                 "Daily investor intelligence briefing"],
                check=True, capture_output=True, text=True,
            )
    except FileNotFoundError:
        logger.warning("gh CLI not found — create the repo manually")
    except subprocess.CalledProcessError as e:
        logger.warning("Failed to create repo: %s", e)


def _run_git(args, cwd):
    """Run a git command in the specified directory."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, check=True,
    )
    if result.stdout.strip():
        logger.debug("git %s: %s", " ".join(args), result.stdout.strip())
    return result

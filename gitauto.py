#!/usr/bin/env python3

import sys
import os
import subprocess
import importlib
import json
from pathlib import Path
from typing import Optional, List
import site

__version__ = "2.0.3"

# ----------------------------
# Auto-add Gemini AI venv to sys.path
# ----------------------------
AI_VENV = Path.home() / ".gitauto" / "ai_venv"
if AI_VENV.exists():
    if os.name == "nt":
        site_packages = AI_VENV / "Lib" / "site-packages"
    else:
        pyver = f"{sys.version_info.major}.{sys.version_info.minor}"
        site_packages = AI_VENV / "lib" / f"python{pyver}" / "site-packages"
    if site_packages.exists():
        sys.path.insert(0, str(site_packages))

# ----------------------------
# Terminal colors
# ----------------------------
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

# ----------------------------
# GitAuto Core
# ----------------------------
class GitAuto:
    def __init__(self):
        self.config_dir = Path.home() / ".gitauto"
        self.config_file = self.config_dir / "config.json"
        self.ai_venv = AI_VENV
        self.config = self.load_config()
        self.interactive = sys.stdin.isatty()

    # ----------------------------
    # Config management
    # ----------------------------
    def load_config(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, config: dict):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f)
        try:
            os.chmod(self.config_file, 0o600)
        except Exception:
            # ignore permission errors on non-posix platforms
            pass
        self.config = config

    def get_api_key(self) -> Optional[str]:
        return self.config.get("api_key")

    def get_provider(self) -> Optional[str]:
        return self.config.get("provider")

    # ----------------------------
    # Print helpers
    # ----------------------------
    def print_header(self, text: str):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*30}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*30}{Colors.END}\n")

    def print_success(self, text: str):
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")

    def print_error(self, text: str):
        print(f"{Colors.RED}✗ {text}{Colors.END}")

    def print_info(self, text: str):
        print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

    def print_warning(self, text: str):
        print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

    # ----------------------------
    # Shell command helpers
    # ----------------------------
    def run_command(self, command: List[str], capture_output=True) -> tuple:
        try:
            if capture_output:
                result = subprocess.run(
                    command, capture_output=True, text=True, check=False
                )
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(command, check=False)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)

    # ----------------------------
    # Git helpers
    # ----------------------------
    def is_git_repo(self) -> bool:
        success, _, _ = self.run_command(["git", "rev-parse", "--git-dir"])
        return success

    def get_git_status(self) -> str:
        success, output, _ = self.run_command(["git", "status", "--short"])
        return output if success else ""

    def get_diff(self) -> str:
        # prefer staged changes, fall back to unstaged
        success, output, _ = self.run_command(["git", "diff", "--cached"])
        if not success or not output:
            success, output, _ = self.run_command(["git", "diff"])
        return output if success else ""

    def get_current_branch(self) -> str:
        success, output, _ = self.run_command(["git", "branch", "--show-current"])
        return output if success else "main"

    def get_branches(self) -> List[str]:
        success, output, _ = self.run_command(["git", "branch", "-a"])
        if not success:
            return []
        branches = []
        for line in output.split("\n"):
            branch = line.strip().replace("* ", "").replace("remotes/origin/", "")
            if branch and not branch.startswith("HEAD"):
                branches.append(branch)
        # keep order and de-duplicate
        return list(dict.fromkeys(branches))

    def get_remote_url(self) -> str:
        success, output, _ = self.run_command(["git", "remote", "get-url", "origin"])
        return output if success else "No remote configured"

    # ----------------------------
    # Lazy AI library installer
    # ----------------------------
    def install_ai_library(self, provider: str):
        if provider == "openai":
            try:
                import openai  # noqa: F401
            except ImportError:
                self.print_info("OpenAI library not found. Installing...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet", "openai"]
                )
        elif provider == "anthropic":
            try:
                import anthropic  # noqa: F401
            except ImportError:
                self.print_info("Anthropic library not found. Installing...")
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "--quiet", "anthropic"]
                )
        elif provider == "gemini":
            if not self.ai_venv.exists():
                self.print_info("Creating dedicated Gemini virtual environment...")
                subprocess.check_call([sys.executable, "-m", "venv", str(self.ai_venv)])
            try:
                import google.generativeai  # noqa: F401
            except ImportError:
                self.print_info("Installing Gemini AI in venv...")
                if os.name == "nt":
                    python_bin = self.ai_venv / "Scripts" / "python.exe"
                else:
                    python_bin = self.ai_venv / "bin" / "python"
                subprocess.check_call([str(python_bin), "-m", "pip", "install", "--quiet", "google-generativeai"])

    # ----------------------------
    # Generate AI commit message (concise)
    # ----------------------------
    def generate_commit_message(self, diff: str) -> Optional[str]:
        api_key = self.get_api_key()
        provider = self.get_provider()
        if not api_key or not provider:
            self.print_warning("No AI provider or API key configured.")
            return None

        # show provider and ensure libraries are available
        self.print_info(f"Using AI provider: {provider}")
        self.install_ai_library(provider)

        # concise prompt: short, imperative-style message (<=50 chars)
        prompt = (
            "Generate a very short (one-line, imperative tense, <=50 chars) "
            "git commit message summarizing the changes below:\n\n"
            f"{diff[:3000]}"
        )

        try:
            if provider == "openai":
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=50,
                )
                return response.choices[0].message.content.strip()
            elif provider == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
                return msg.content[0].text.strip()
            elif provider == "gemini":
                genai = importlib.import_module("google.generativeai")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(prompt)
                if hasattr(response, "text") and response.text:
                    return response.text.strip()
                if hasattr(response, "candidates") and response.candidates:
                    cand = response.candidates[0]
                    part = cand.content.parts[0]
                    return getattr(part, "text", "").strip()
                return None
        except Exception as e:
            self.print_error(f"AI generation failed: {e}")
            return None

    # ----------------------------
    # Interactive AI setup
    # ----------------------------
    def setup_ai(self):
        self.print_header("GitAuto AI Setup")
        provider = input("Enter AI provider (openai/anthropic/gemini) or leave empty to skip: ").strip().lower()
        if provider in ("openai", "anthropic", "gemini"):
            api_key = input(f"Enter API key for {provider}: ").strip()
            if api_key:
                self.save_config({"provider": provider, "api_key": api_key})
                self.print_success(f"{provider} API key saved!")
            else:
                self.print_warning("No API key entered. Skipping.")
        else:
            self.print_warning("Skipped AI setup.")

    # ----------------------------
    # Push resolver (hybrid)
    # ----------------------------
    def push_with_hybrid_resolver(self, branch: str) -> bool:
        """
        Attempts push. If push rejected due to remote changes, attempt a hybrid resolution:
          1) try pull --rebase (auto)
          2) if pull --rebase fails due to conflicts, inform user and offer choices:
             - abort (leave local staged/working tree)
             - perform git pull --no-rebase (merge)
             - force push (dangerous)
        Returns True on successful push, False otherwise.
        """
        self.print_info(f"Attempting to push to origin/{branch}...")
        ok, _, stderr = self.run_command(["git", "push", "origin", branch], capture_output=True)
        if ok:
            self.print_success(f"Pushed to origin/{branch}")
            return True

        # detect non-fast-forward / rejection
        if "fetch first" in stderr.lower() or "non-fast-forward" in stderr.lower() or "rejected" in stderr.lower():
            self.print_warning("Push was rejected — remote contains work you don't have locally.")
            # Non-interactive: try a safe automatic rebase then push
            if not self.interactive:
                self.print_info("Non-interactive mode: attempting 'git pull --rebase origin <branch>' and re-push.")
                ok_pull, out_pull, err_pull = self.run_command(["git", "pull", "--rebase", "origin", branch], capture_output=True)
                if not ok_pull:
                    self.print_error(f"Automatic rebase failed: {err_pull or out_pull}")
                    return False
                # try push again
                ok2, _, err2 = self.run_command(["git", "push", "origin", branch], capture_output=True)
                if ok2:
                    self.print_success(f"Pushed to origin/{branch} after rebase.")
                    return True
                else:
                    self.print_error(f"Push still failed: {err2}")
                    return False

            # interactive: present hybrid options
            self.print_info("Choose how to resolve the remote divergence:")
            self.print_info("  1) Auto rebase (git pull --rebase) then push (recommended)")
            self.print_info("  2) Merge (git pull --no-rebase) then push")
            self.print_info("  3) Force push (git push --force) — destructive, use with caution")
            self.print_info("  4) Abort (do nothing)")
            choice = input("Select (1/2/3/4) [1]: ").strip() or "1"

            if choice == "1":
                self.print_info("Running: git pull --rebase origin {branch}")
                ok_pull, out_pull, err_pull = self.run_command(["git", "pull", "--rebase", "origin", branch], capture_output=True)
                if ok_pull:
                    self.print_success("Rebase successful. Attempting push...")
                    ok2, _, err2 = self.run_command(["git", "push", "origin", branch], capture_output=True)
                    if ok2:
                        self.print_success(f"Pushed to origin/{branch} after rebase.")
                        return True
                    else:
                        self.print_error(f"Push failed after rebase: {err2}")
                        return False
                else:
                    # rebase failed — likely conflicts
                    self.print_error(f"Rebase failed: {err_pull or out_pull}")
                    self.print_warning("Repository may now be in a conflicted state. Resolve conflicts manually or choose another option.")
                    # offer fallback choices
                    fallback = input("Run merge (2), force push (3) or abort (4)? [4]: ").strip() or "4"
                    if fallback == "2":
                        # attempt merge
                        ok_m, out_m, err_m = self.run_command(["git", "pull", "--no-rebase", "origin", branch], capture_output=True)
                        if ok_m:
                            ok_push, _, err_push = self.run_command(["git", "push", "origin", branch], capture_output=True)
                            if ok_push:
                                self.print_success("Merged and pushed successfully.")
                                return True
                            else:
                                self.print_error(f"Push after merge failed: {err_push}")
                                return False
                        else:
                            self.print_error(f"Merge failed: {err_m or out_m}")
                            return False
                    elif fallback == "3":
                        ok_f, _, err_f = self.run_command(["git", "push", "--force", "origin", branch], capture_output=True)
                        if ok_f:
                            self.print_success("Force-pushed to remote (destructive).")
                            return True
                        else:
                            self.print_error(f"Force push failed: {err_f}")
                            return False
                    else:
                        self.print_info("Aborted push resolution. Please resolve manually.")
                        return False

            elif choice == "2":
                self.print_info("Running: git pull --no-rebase origin {branch} (merge)")
                ok_m, out_m, err_m = self.run_command(["git", "pull", "--no-rebase", "origin", branch], capture_output=True)
                if ok_m:
                    ok_push, _, err_push = self.run_command(["git", "push", "origin", branch], capture_output=True)
                    if ok_push:
                        self.print_success("Merged and pushed successfully.")
                        return True
                    else:
                        self.print_error(f"Push after merge failed: {err_push}")
                        return False
                else:
                    self.print_error(f"Merge failed: {err_m or out_m}")
                    return False

            elif choice == "3":
                confirm = input("Force push will overwrite remote history. Type 'FORCE' to confirm: ").strip()
                if confirm == "FORCE":
                    ok_f, _, err_f = self.run_command(["git", "push", "--force", "origin", branch], capture_output=True)
                    if ok_f:
                        self.print_success("Force-pushed to remote (destructive).")
                        return True
                    else:
                        self.print_error(f"Force push failed: {err_f}")
                        return False
                else:
                    self.print_info("Force push cancelled.")
                    return False
            else:
                self.print_info("Aborted push resolution. Please resolve manually.")
                return False
        else:
            # unknown push failure
            self.print_error(f"Push failed: {stderr}")
            return False

    # ----------------------------
    # Commit flow (single iteration)
    # Returns: "restart", "continue", "abort"
    # ----------------------------
    def commit_flow(self) -> str:
        # Show status / changes
        status = self.get_git_status()
        if not status:
            self.print_warning("No changes detected!")
            if self.interactive:
                cont = input("Continue anyway? (y/n): ").strip().lower()
                if cont != "y":
                    return "abort"
        else:
            print(f"\n{Colors.CYAN}Changes detected:{Colors.END}")
            print(status)

        # Add files (user can specify files or '.' for all)
        add_files = input("Files to add (. for all): ").strip() if self.interactive else "."
        if not add_files:
            add_files = "."
        add_cmd = ["git", "add"]
        # support splitting multiple files by space, keep '.' as single arg
        if add_files == ".":
            add_cmd.append(".")
        else:
            add_cmd.extend(add_files.split())
        ok, _, err = self.run_command(add_cmd)
        if not ok:
            self.print_error(f"Failed to add files: {err}")
            return "abort"
        self.print_success(f"Added: {add_files}")

        # Commit message
        commit_message = None
        use_ai = bool(self.get_api_key() and self.get_provider())

        if self.interactive:
            ai_choice = input("Generate commit message with AI? (y/n): ").strip().lower()
            if ai_choice == "y" and use_ai:
                diff = self.get_diff()
                if diff:
                    while True:  # regeneration loop
                        provider_name = self.get_provider()
                        print(f"{Colors.YELLOW}Generating commit message via {provider_name}...{Colors.END}")
                        commit_message = self.generate_commit_message(diff)

                        if not commit_message:
                            self.print_error("AI failed to generate a commit message!")
                            commit_message = input("Enter commit message manually: ").strip()
                            break

                        # show concise suggestion only (the AI is instructed to be short)
                        print(f"\n{Colors.GREEN}AI Commit Message:{Colors.END} {commit_message}")
                        confirm = input("Use this message? (y=yes, r=regenerate, m=manual): ").strip().lower()

                        if confirm == "y":
                            break
                        elif confirm == "r":
                            continue
                        elif confirm == "m":
                            commit_message = input("Enter commit message manually: ").strip()
                            break

            if not commit_message:
                commit_message = input("Enter commit message: ").strip()
        else:
            if use_ai:
                diff = self.get_diff()
                commit_message = self.generate_commit_message(diff)
            if not commit_message:
                commit_message = "Auto commit"

        if not commit_message:
            self.print_error("Commit message cannot be empty!")
            return "abort"

        ok, _, err = self.run_command(["git", "commit", "-m", commit_message])
        if not ok:
            self.print_error(f"Commit failed: {err}")
            return "abort"
        self.print_success(f"Committed: {commit_message}")

        # After commit: allow undo and optionally restart commit workflow
        if self.interactive:
            undo = input("Undo last commit? (y/n): ").strip().lower()
            if undo == "y":
                ok, _, err = self.run_command(["git", "reset", "--soft", "HEAD~1"])
                if ok:
                    self.print_success("Last commit undone. Changes are staged again.")
                    redo = input("Do you want to commit again? (y/n): ").strip().lower()
                    if redo == "y":
                        return "restart"
                    else:
                        # user does not want to continue with branch/push tasks
                        return "abort"
                else:
                    self.print_error(f"Failed to undo commit: {err}")
                    return "abort"

        return "continue"

    # ----------------------------
    # Main workflow
    # ----------------------------
    def run(self):
        self.print_header(f"GitAuto v{__version__}")

        if not self.is_git_repo():
            self.print_error("Not a git repository! Run 'git init' first.")
            sys.exit(1)

        self.print_info(f"Remote: {self.get_remote_url()}")
        current_branch = self.get_current_branch()
        self.print_info(f"Current branch: {current_branch}")

        # Loop commit_flow according to return status
        while True:
            status = self.commit_flow()
            if status == "restart":
                # user undid and wants to redo commit flow: loop again
                continue
            elif status == "continue":
                # proceed to branch/push tasks
                break
            elif status == "abort":
                # stop remaining tasks, finish run()
                self.print_header("Aborted")
                self.print_warning("Workflow aborted after undo/no-op.")
                return
            else:
                # unknown -> abort
                self.print_error("Unexpected status from commit flow. Aborting.")
                return

        # handle branch list display and switching
        branches = self.get_branches()
        if branches:
            print(f"{Colors.CYAN}Available branches:{Colors.END}")
            for b in branches[:50]:
                pref = "→" if b == current_branch else " "
                print(f"  {pref} {b}")

        if self.interactive:
            switch = input(f"Switch branch? (leave empty to stay on '{current_branch}'): ").strip()
            if switch:
                ok, _, err = self.run_command(["git", "checkout", switch])
                if ok:
                    self.print_success(f"Switched to: {switch}")
                    current_branch = switch
                else:
                    create = input("Branch doesn't exist. Create it? (y/n): ").strip().lower()
                    if create == "y":
                        ok, _, err = self.run_command(["git", "checkout", "-b", switch])
                        if ok:
                            self.print_success(f"Created and switched to: {switch}")
                            current_branch = switch
                        else:
                            self.print_error(f"Failed: {err}")

        # Push
        if self.interactive:
            push = input("Push to remote? (y/n): ").strip().lower()
            if push == "y":
                pushed = self.push_with_hybrid_resolver(current_branch)
                if not pushed:
                    # ask user if they want to try upstream set or force or abort
                    extra = input("Push unsuccessful. Try set-upstream and push? (y=--set-upstream, f=force, n=skip): ").strip().lower()
                    if extra == "y":
                        ok, _, err = self.run_command(["git", "push", "--set-upstream", "origin", current_branch], capture_output=False)
                        if ok:
                            self.print_success("Upstream set and pushed.")
                        else:
                            self.print_error(f"Failed to set upstream: {err}")
                    elif extra == "f":
                        confirm = input("Type 'FORCE' to confirm destructive force-push: ").strip()
                        if confirm == "FORCE":
                            ok, _, err = self.run_command(["git", "push", "--force", "origin", current_branch], capture_output=False)
                            if ok:
                                self.print_success("Force-pushed to remote (destructive).")
                            else:
                                self.print_error(f"Force push failed: {err}")
                        else:
                            self.print_info("Force push cancelled.")
                    else:
                        self.print_info("Skipping push; resolve manually later.")

        self.print_header("All Done!")


# Entry point
def main():
    bot = GitAuto()

    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ('-v', '--version'):
            print(f"GitAuto v{__version__}")
            sys.exit(0)
        if arg in ('setup', '--setup'):
            bot.setup_ai()
            sys.exit(0)
        if arg in ('--pre-commit', '--commit-msg'):
            sys.exit(0)

    try:
        bot.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Aborted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()

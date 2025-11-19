#!/usr/bin/env python3

import os
import sys
import subprocess
import importlib
import json
from pathlib import Path
from typing import Optional, List

__version__ = "2.2.0"

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
        self.config_dir = Path.home() / '.gitauto'
        self.config_file = self.config_dir / 'config.json'
        self.ai_venv = self.config_dir / 'ai_venv'
        self.config = self.load_config()
        self.interactive = sys.stdin.isatty()

    # ----------------------------
    # Config management
    # ----------------------------
    def load_config(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def save_config(self, config: dict):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        os.chmod(self.config_file, 0o600)
        self.config = config

    def get_api_key(self) -> Optional[str]:
        return self.config.get('api_key')

    def get_provider(self) -> Optional[str]:
        return self.config.get('provider')

    # ----------------------------
    # Print helpers
    # ----------------------------
    def print_header(self, text: str):
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

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
        success, _, _ = self.run_command(['git', 'rev-parse', '--git-dir'])
        return success

    def get_git_status(self) -> str:
        success, output, _ = self.run_command(['git', 'status', '--short'])
        return output if success else ""

    def get_diff(self) -> str:
        success, output, _ = self.run_command(['git', 'diff', '--cached'])
        if not success or not output:
            success, output, _ = self.run_command(['git', 'diff'])
        return output if success else ""

    def get_current_branch(self) -> str:
        success, output, _ = self.run_command(['git', 'branch', '--show-current'])
        return output if success else "main"

    def get_branches(self) -> List[str]:
        success, output, _ = self.run_command(['git', 'branch', '-a'])
        if not success:
            return []
        branches = []
        for line in output.split('\n'):
            branch = line.strip().replace('* ', '').replace('remotes/origin/', '')
            if branch and not branch.startswith('HEAD'):
                branches.append(branch)
        return list(set(branches))

    def get_remote_url(self) -> str:
        success, output, _ = self.run_command(['git', 'remote', 'get-url', 'origin'])
        return output if success else "No remote configured"

    # ----------------------------
    # Lazy AI library installer
    # ----------------------------
    def install_ai_library(self, provider: str):
        if provider == 'openai':
            try:
                import openai
            except ImportError:
                self.print_info("OpenAI library not found. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "openai"])
                import openai
        elif provider == 'anthropic':
            try:
                import anthropic
            except ImportError:
                self.print_info("Anthropic library not found. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "anthropic"])
                import anthropic
        elif provider == 'gemini':
            if not self.ai_venv.exists():
                self.print_info("Creating dedicated Gemini virtual environment...")
                subprocess.check_call([sys.executable, "-m", "venv", str(self.ai_venv)])

            if os.name == "nt":
                python_bin = self.ai_venv / "Scripts" / "python.exe"
                site_packages = self.ai_venv / "Lib" / "site-packages"
            else:
                python_bin = self.ai_venv / "bin" / "python"
                site_packages = self.ai_venv / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"

            try:
                import google.generativeai
            except ImportError:
                self.print_info("Gemini library not found. Installing in isolated venv...")
                subprocess.check_call([str(python_bin), "-m", "pip", "install", "--quiet", "google-generativeai"])
                sys.path.insert(0, str(site_packages))

    # ----------------------------
    # Generate AI commit message
    # ----------------------------
    def generate_commit_message(self, diff: str) -> Optional[str]:
        api_key = self.get_api_key()
        provider = self.get_provider()
        if not api_key or not provider:
            self.print_warning("No AI provider or API key configured.")
            return None

        self.print_info(f"Using AI provider: {provider}")
        self.install_ai_library(provider)

        try:
            if provider == 'openai':
                import openai
                client = openai.OpenAI(api_key=api_key)
                self.print_info("Generating commit message with OpenAI GPT...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user",
                               "content": f"Generate a concise git commit message for changes:\n{diff[:3000]}"}],
                    max_tokens=100,
                )
                return response.choices[0].message.content.strip()

            elif provider == 'anthropic':
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                self.print_info("Generating commit message with Claude...")
                msg = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": f"Generate a concise git commit message for changes:\n{diff[:3000]}"
                    }]
                )
                return msg.content[0].text.strip()

            elif provider == 'gemini':
                import importlib
                genai = importlib.import_module("google.generativeai")
                genai.configure(api_key=api_key)
                self.print_info("Generating commit message with Gemini AI...")
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(f"Generate a concise git commit message for changes:\n{diff[:3000]}")
                if hasattr(response, "text") and response.text:
                    return response.text.strip()
                if hasattr(response, "candidates"):
                    cand = response.candidates[0]
                    part = cand.content.parts[0]
                    return getattr(part, "text", "").strip()
                return "Generated commit message unavailable."

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
    # Main workflow
    # ----------------------------
    def run(self):
        self.print_header(f"Git Automation Tool v{__version__}")

        if not self.is_git_repo():
            self.print_error("Not a git repository! Run 'git init' first.")
            sys.exit(1)

        self.print_info(f"Remote: {self.get_remote_url()}")
        current_branch = self.get_current_branch()
        self.print_info(f"Current branch: {current_branch}")

        status = self.get_git_status()
        if not status:
            self.print_warning("No changes detected!")
            if self.interactive:
                cont = input("Continue anyway? (y/n): ").strip().lower()
                if cont != "y":
                    sys.exit(0)
        else:
            print(f"\n{Colors.CYAN}Changes detected:{Colors.END}")
            print(status)

        # ----------------------------
        # 1️⃣ Add files
        # ----------------------------
        add_files = input("Files to add (. for all): ").strip() if self.interactive else "."
        if not add_files:
            add_files = "."
        ok, _, err = self.run_command(["git", "add"] + (add_files.split() if add_files != "." else ["."]))
        if not ok:
            self.print_error(f"Failed to add files: {err}")
            sys.exit(1)
        self.print_success(f"Added: {add_files}")

        # ----------------------------
        # 2️⃣ Commit message
        # ----------------------------
        commit_message = None
        use_ai = self.get_api_key() and self.get_provider()

        if self.interactive:
            ai_choice = input("Generate commit message with AI? (y/n): ").strip().lower()
            if ai_choice == "y" and use_ai:
                diff = self.get_diff()
                if diff:
                    commit_message = self.generate_commit_message(diff)
                    if commit_message:
                        print(f"\n{Colors.GREEN}AI Commit Message:{Colors.END} {commit_message}")
                        confirm = input("Use this message? (y=yes, r=regen, n=manual): ").strip().lower()
                        if confirm == "r":
                            commit_message = self.generate_commit_message(diff)
                        elif confirm == "n":
                            commit_message = input("Enter commit message manually: ").strip()
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
            sys.exit(1)

        ok, _, err = self.run_command(["git", "commit", "-m", commit_message])
        if not ok:
            self.print_error(f"Commit failed: {err}")
            sys.exit(1)
        self.print_success(f"Committed: {commit_message}")

        # ----------------------------
        # 3️⃣ Branch selection
        # ----------------------------
        branches = self.get_branches()
        if branches:
            print(f"{Colors.CYAN}Available branches:{Colors.END}")
            for b in branches[:10]:
                pref = "→" if b == current_branch else " "
                print(f"  {pref} {b}")

        if self.interactive:
            switch = input(f"Switch branch? (leave empty to stay on '{current_branch}'): ").strip()
            if switch:
                ok, _, err = self.run_command(["git", "checkout", switch])
                if ok:
                    self.print_success(f"Switched to: {switch}")
                else:
                    create = input("Branch doesn't exist. Create it? (y/n): ").strip().lower()
                    if create == "y":
                        ok, _, err = self.run_command(["git", "checkout", "-b", switch])
                        if ok:
                            self.print_success(f"Created and switched to: {switch}")
                        else:
                            self.print_error(f"Failed: {err}")

        # ----------------------------
        # 4️⃣ Push
        # ----------------------------
        if self.interactive:
            push = input("Push to remote? (y/n): ").strip().lower()
            if push == "y":
                ok, _, _ = self.run_command(["git", "push", "origin", current_branch], capture_output=False)
                if ok:
                    self.print_success(f"Pushed to origin/{current_branch}")
                else:
                    up = input("Set upstream and push? (y/n): ").strip().lower()
                    if up == "y":
                        ok, _, err = self.run_command(
                            ["git", "push", "--set-upstream", "origin", current_branch],
                            capture_output=False
                        )
                        if ok:
                            self.print_success("Upstream set and pushed.")
                        else:
                            self.print_error(err)

        self.print_header("All Done!")
        self.print_success("Automation Completed Successfully")


# ----------------------------
# Entry point
# ----------------------------
def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ('-v', '--version'):
            print(f"GitAuto v{__version__}")
            sys.exit(0)
        if arg in ('setup', '--setup'):
            GitAuto().setup_ai()
            sys.exit(0)
        if arg in ('--pre-commit', '--commit-msg'):
            sys.exit(0)

    bot = GitAuto()
    try:
        bot.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Aborted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == '__main__':
    main()

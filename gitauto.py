#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, List

__version__ = "2.0.0"

# ----------------------------
# Lazy imports
# ----------------------------
def lazy_import_openai():
    import openai
    from openai import OpenAI
    return openai, OpenAI

def lazy_import_anthropic():
    import anthropic
    return anthropic

def lazy_import_gemini():
    try:
        import google.generativeai as genai
        return genai
    except ImportError:
        return None

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
    # Run shell command
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
    # AI Commit generation
    # ----------------------------
    def generate_commit_message(self, diff: str) -> Optional[str]:
        api_key = self.get_api_key()
        provider = self.get_provider()
        if not api_key or not provider:
            self.print_warning("No AI provider or API key configured.")
            return None

        self.print_info(f"Using AI provider: {provider}")

        try:
            if provider == 'anthropic':
                anthropic = lazy_import_anthropic()
                if not anthropic:
                    self.print_warning("Anthropic library not installed.")
                    return None
                client = anthropic.Anthropic(api_key=api_key)
                self.print_info("Generating commit message with Anthropic Claude...")
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    messages=[{
                        "role": "user",
                        "content": f"Generate a concise git commit message for changes:\n{diff[:3000]}"
                    }]
                )
                return message.content[0].text.strip()

            elif provider == 'openai':
                openai, OpenAI = lazy_import_openai()
                if not OpenAI:
                    self.print_warning("OpenAI library not installed.")
                    return None
                client = OpenAI(api_key=api_key)
                self.print_info("Generating commit message with OpenAI GPT...")
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user",
                               "content": f"Generate a concise git commit message for changes:\n{diff[:3000]}"}],
                    max_tokens=100,
                    temperature=1.0,
                    n=1,
                )
                return response.choices[0].message.content.strip()

            elif provider == 'gemini':
                try:
                    import google.generativeai as genai
                except ImportError:
                    try:
                        import subprocess, sys
                        self.print_info("Gemini library not found. Installing...")
                        subprocess.check_call(
                            [sys.executable, "-m", "pip", "install", "--user", "--quiet", "google-generativeai"]
                        )
                        import google.generativeai as genai
                    except Exception as e:
                        self.print_error(f"Failed to install Gemini library: {str(e)}")
                        return None

                genai.configure(api_key=api_key)
                self.print_info("Generating commit message with Gemini AI...")
                model = genai.GenerativeModel("gemini-2.5-flash")
                response = model.generate_content(
                    f"Generate a concise git commit message for changes:\n{diff[:3000]}"
                )
                return response.text.strip()


            else:
                self.print_warning(f"Unknown AI provider '{provider}'.")
                return None

        except Exception as e:
            self.print_error(f"AI generation failed: {str(e)}")
            return None

    # ----------------------------
    # AI setup
    # ----------------------------
    def setup_ai(self):
        print(f"{Colors.HEADER}{Colors.BOLD}GitAuto AI Setup{Colors.END}\n")
        provider = input("Enter AI provider (anthropic/openai/gemini) or leave empty to skip: ").strip().lower()
        if provider in ("anthropic", "openai", "gemini"):
            api_key = input(f"Enter API key for {provider}: ").strip()
            if api_key:
                self.save_config({"provider": provider, "api_key": api_key})
                self.print_success(f"{provider} API key saved!")
            else:
                print("No API key entered. Skipping setup.")
        else:
            print("Skipped AI setup. You can run 'gitauto setup' later.")

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
                proceed = input("Continue anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    sys.exit(0)
        else:
            print(f"\n{Colors.CYAN}Changes detected:{Colors.END}")
            print(status)

        # Add files
        if self.interactive:
            add_files = input("Files to add (. for all, or specific files): ").strip()
        else:
            add_files = "."
        if not add_files:
            add_files = "."
        if add_files == ".":
            success, _, error = self.run_command(['git', 'add', '.'])
        else:
            files = add_files.split()
            success, _, error = self.run_command(['git', 'add'] + files)
        if not success:
            self.print_error(f"Failed to add files: {error}")
            sys.exit(1)
        self.print_success(f"Added files: {add_files}")

        # Commit
        use_ai = self.get_api_key() and self.get_provider()
        commit_message = None

        while True:
            if use_ai and self.interactive:
                generate = input("Generate commit message with AI? (y/n): ").strip().lower()
                if generate == 'y':
                    diff = self.get_diff()
                    if diff:
                        commit_message = self.generate_commit_message(diff)
                        if commit_message:
                            print(f"\n{Colors.GREEN}AI Generated Commit Message:{Colors.END} {commit_message}")
                            choice = input("Use this message? (y = yes, r = regenerate, n = cancel): ").strip().lower()
                            if choice == 'r':
                                continue
                            elif choice == 'n':
                                commit_message = input("Enter commit message manually: ").strip()
                            break
            if not commit_message and self.interactive:
                commit_message = input("Enter commit message: ").strip()
            if not commit_message:
                self.print_error("Commit message cannot be empty!")
                sys.exit(1)
            break

        # Commit
        success, _, error = self.run_command(['git', 'commit', '-m', commit_message])
        if not success:
            self.print_error(f"Failed to commit: {error}")
            sys.exit(1)
        self.print_success(f"Committed: {commit_message}")

        # Branch
        branches = self.get_branches()
        if branches:
            print(f"{Colors.CYAN}Available branches:{Colors.END}")
            for i, branch in enumerate(branches[:10], 1):
                marker = "→" if branch == current_branch else " "
                print(f"  {marker} {branch}")

        if self.interactive:
            switch_branch = input(f"Switch branch? (leave empty to stay on '{current_branch}'): ").strip()
            if switch_branch:
                success, _, error = self.run_command(['git', 'checkout', switch_branch])
                if success:
                    self.print_success(f"Switched to branch: {switch_branch}")
                    current_branch = switch_branch
                else:
                    create_new = input(f"Branch doesn't exist. Create it? (y/n): ").strip().lower()
                    if create_new == 'y':
                        success, _, error = self.run_command(['git', 'checkout', '-b', switch_branch])
                        if success:
                            self.print_success(f"Created and switched to branch: {switch_branch}")
                            current_branch = switch_branch
                        else:
                            self.print_error(f"Failed to create branch: {error}")

        # Push
        if self.interactive:
            push = input("Push to remote? (y/n): ").strip().lower()
            if push == 'y':
                self.print_info(f"Pushing to origin/{current_branch}...")
                success, output, error = self.run_command(['git', 'push', 'origin', current_branch], capture_output=False)
                if success:
                    self.print_success(f"Successfully pushed to origin/{current_branch}")
                else:
                    upstream = input("Set upstream and push? (y/n): ").strip().lower()
                    if upstream == 'y':
                        success, _, error = self.run_command(['git', 'push', '--set-upstream', 'origin', current_branch], capture_output=False)
                        if success:
                            self.print_success("Successfully pushed and set upstream")
                        else:
                            self.print_error(f"Failed to push: {error}")
            else:
                self.print_info("Skipped push")

        self.print_header("All Done!")
        self.print_success("Automation Completed Successfully")

# ----------------------------
# Entry point
# ----------------------------
def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ('-v', '--version'):
            print(f"GitAuto v{__version__}")
            sys.exit(0)
        if sys.argv[1] == 'setup':
            gitauto = GitAuto()
            gitauto.setup_ai()
            sys.exit(0)
        if sys.argv[1] == '--pre-commit' or sys.argv[1] == '--commit-msg':
            # Hooks placeholder
            sys.exit(0)

    gitauto = GitAuto()
    try:
        gitauto.run()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Aborted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {str(e)}{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()

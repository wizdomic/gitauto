#!/usr/bin/env python3

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional, List

try:
    import anthropic
except ImportError:
    anthropic = None

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

class GitAuto:
    def __init__(self):
        self.config_dir = Path.home() / '.gitauto'
        self.config_file = self.config_dir / 'config.json'
        self.api_key = self.load_api_key()

    def load_api_key(self) -> Optional[str]:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('anthropic_api_key')
            except:
                pass
        return os.getenv('ANTHROPIC_API_KEY')

    def save_api_key(self, api_key: str):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump({'anthropic_api_key': api_key}, f)
        os.chmod(self.config_file, 0o600)
        self.api_key = api_key

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

    def run_command(self, command: List[str], capture_output=True) -> tuple:
        try:
            if capture_output:
                result = subprocess.run(command, capture_output=True, text=True, check=False)
                return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
            else:
                result = subprocess.run(command, check=False)
                return result.returncode == 0, "", ""
        except Exception as e:
            return False, "", str(e)

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

    def generate_commit_message(self, diff: str) -> Optional[str]:
        if not self.api_key:
            self.print_warning("No API key found. AI commit generation disabled.")
            return None

        if not anthropic:
            self.print_warning("Anthropic library not installed. AI commit generation disabled.")
            return None

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            self.print_info("Generating commit message with AI...")

            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": f"""Generate a concise, clear git commit message for these changes.
Follow conventional commits format (type: description).
Types: feat, fix, docs, style, refactor, test, chore.
Keep it under 72 characters.

Changes:
{diff[:3000]}"""
                }]
            )

            commit_msg = message.content[0].text.strip()
            return commit_msg
        except Exception as e:
            self.print_error(f"AI generation failed: {str(e)}")
            return None

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

    def run(self):
        self.print_header("Git Automation Tool")

        if not self.is_git_repo():
            self.print_error("Not a git repository! Please run 'git init' first.")
            sys.exit(1)

        remote_url = self.get_remote_url()
        self.print_info(f"Remote: {remote_url}")

        current_branch = self.get_current_branch()
        self.print_info(f"Current branch: {current_branch}")

        status = self.get_git_status()
        if not status:
            self.print_warning("No changes detected!")
            proceed = input(f"\n{Colors.YELLOW}Continue anyway? (y/n): {Colors.END}").strip().lower()
            if proceed != 'y':
                sys.exit(0)
        else:
            print(f"\n{Colors.CYAN}Changes detected:{Colors.END}")
            print(status)

        print(f"\n{Colors.BOLD}Step 1: Add Files{Colors.END}")
        add_files = input(f"{Colors.CYAN}Files to add (. for all, or specific files): {Colors.END}").strip()

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

        print(f"\n{Colors.BOLD}Step 2: Commit Message{Colors.END}")

        use_ai = False
        if self.api_key and anthropic:
            use_ai_input = input(f"{Colors.CYAN}Generate commit message with AI? (y/n): {Colors.END}").strip().lower()
            use_ai = use_ai_input == 'y'

        commit_message = None

        if use_ai:
            diff = self.get_diff()
            if diff:
                commit_message = self.generate_commit_message(diff)
                if commit_message:
                    print(f"\n{Colors.GREEN}AI Generated:{Colors.END} {commit_message}")
                    use_generated = input(f"{Colors.CYAN}Use this message? (y/n): {Colors.END}").strip().lower()
                    if use_generated != 'y':
                        commit_message = None

        if not commit_message:
            commit_message = input(f"{Colors.CYAN}Enter commit message: {Colors.END}").strip()

        if not commit_message:
            self.print_error("Commit message cannot be empty!")
            sys.exit(1)

        success, _, error = self.run_command(['git', 'commit', '-m', commit_message])

        if not success:
            self.print_error(f"Failed to commit: {error}")
            sys.exit(1)

        self.print_success(f"Committed: {commit_message}")

        print(f"\n{Colors.BOLD}Step 3: Branch Management{Colors.END}")

        branches = self.get_branches()
        if branches:
            print(f"{Colors.CYAN}Available branches:{Colors.END}")
            for i, branch in enumerate(branches[:10], 1):
                marker = "→" if branch == current_branch else " "
                print(f"  {marker} {branch}")

        switch_branch = input(f"{Colors.CYAN}Switch branch? (leave empty to stay on '{current_branch}'): {Colors.END}").strip()

        if switch_branch:
            success, _, error = self.run_command(['git', 'checkout', switch_branch])
            if success:
                self.print_success(f"Switched to branch: {switch_branch}")
                current_branch = switch_branch
            else:
                create_new = input(f"{Colors.YELLOW}Branch doesn't exist. Create it? (y/n): {Colors.END}").strip().lower()
                if create_new == 'y':
                    success, _, error = self.run_command(['git', 'checkout', '-b', switch_branch])
                    if success:
                        self.print_success(f"Created and switched to branch: {switch_branch}")
                        current_branch = switch_branch
                    else:
                        self.print_error(f"Failed to create branch: {error}")

        print(f"\n{Colors.BOLD}Step 4: Push Changes{Colors.END}")

        push = input(f"{Colors.CYAN}Push to remote? (y/n): {Colors.END}").strip().lower()

        if push == 'y':
            self.print_info(f"Pushing to origin/{current_branch}...")

            success, output, error = self.run_command(['git', 'push', 'origin', current_branch], capture_output=False)

            if success:
                self.print_success(f"Successfully pushed to origin/{current_branch}")
            else:
                upstream = input(f"{Colors.YELLOW}Set upstream and push? (y/n): {Colors.END}").strip().lower()
                if upstream == 'y':
                    success, _, error = self.run_command(['git', 'push', '--set-upstream', 'origin', current_branch], capture_output=False)
                    if success:
                        self.print_success(f"Successfully pushed and set upstream")
                    else:
                        self.print_error(f"Failed to push: {error}")
        else:
            self.print_info("Skipped push")

        self.print_header("All Done!")
        self.print_success("Automation Completed Successfully")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        gitauto = GitAuto()
        print(f"{Colors.HEADER}{Colors.BOLD}GitAuto Setup{Colors.END}\n")
        print("To enable AI-powered commit messages, provide your Anthropic API key.")
        print("Get one at: https://console.anthropic.com/")
        api_key = input(f"\n{Colors.CYAN}Enter Anthropic API key (or leave empty to skip): {Colors.END}").strip()
        if api_key:
            gitauto.save_api_key(api_key)
            gitauto.print_success("API key saved successfully!")
        else:
            print("Skipped API key setup. You can run 'gitauto setup' anytime.")
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

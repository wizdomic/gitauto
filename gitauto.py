#!/usr/bin/env python3
import os, sys, subprocess, json, logging
from pathlib import Path
from typing import Optional, List

__version__ = "2.2.0"

# ----------------------------
# Lazy imports for AI models
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
    HEADER = '\033[95m'; BLUE = '\033[94m'; CYAN = '\033[96m'
    GREEN = '\033[92m'; YELLOW = '\033[93m'; RED = '\033[91m'
    END = '\033[0m'; BOLD = '\033[1m'

# ----------------------------
# GitAuto Core
# ----------------------------
class GitAuto:
    def __init__(self, debug=False):
        self.config_dir = Path.home() / ".gitauto"
        self.config_file = self.config_dir / "config.json"
        self.config = self.load_config()
        self.interactive = sys.stdin.isatty()
        self.debug = debug
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

    # ----------------------------
    # Config system
    # ----------------------------
    def load_config(self) -> dict:
        if self.config_file.exists():
            try:
                return json.load(open(self.config_file))
            except Exception:
                pass
        return {}

    def save_config(self, config: dict):
        self.config_dir.mkdir(exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)
        os.chmod(self.config_file, 0o600)
        self.config = config
        logging.debug(f"Saved config: {config}")

    def get_provider(self) -> Optional[str]:
        return self.config.get("provider")

    def get_api_key(self) -> Optional[str]:
        return self.config.get("api_key")

    # ----------------------------
    # Git helpers
    # ----------------------------
    def run_command(self, cmd: List[str], capture=True):
        logging.debug(f"Running command: {' '.join(cmd)}")
        try:
            if capture:
                r = subprocess.run(cmd, capture_output=True, text=True)
                return r.returncode==0, r.stdout.strip(), r.stderr.strip()
            else:
                r = subprocess.run(cmd)
                return r.returncode==0, "", ""
        except Exception as e:
            return False, "", str(e)

    def is_git_repo(self) -> bool:
        success, _, _ = self.run_command(["git", "rev-parse", "--git-dir"])
        return success

    def get_current_branch(self) -> str:
        success, out, _ = self.run_command(["git", "branch", "--show-current"])
        return out if success else "main"

    def get_branches(self) -> List[str]:
        success, out, _ = self.run_command(["git", "branch", "-a"])
        if not success:
            return []
        branches = [line.strip().replace("* ", "").replace("remotes/origin/", "") 
                    for line in out.splitlines() if line.strip() and not line.startswith("HEAD")]
        return list(set(branches))

    def get_diff(self) -> str:
        success, out, _ = self.run_command(["git", "diff", "--cached"])
        if not success or not out:
            success, out, _ = self.run_command(["git", "diff"])
        return out if success else ""

    def get_git_status(self) -> List[str]:
        success, out, _ = self.run_command(["git", "status", "--short"])
        return out.splitlines() if success else []

    def undo_last_commit(self):
        confirm = input("Undo last commit? (y/n): ").strip().lower()
        if confirm != "y":
            print(f"{Colors.YELLOW}Aborted undo.{Colors.END}")
            return
        success, _, err = self.run_command(["git", "reset", "--soft", "HEAD~1"])
        if success:
            print(f"{Colors.GREEN}✓ Last commit undone, changes staged.{Colors.END}")
        else:
            print(f"{Colors.RED}✗ Undo failed: {err}{Colors.END}")

    # ----------------------------
    # Git Hooks integration
    # ----------------------------
    def install_hooks(self, repo_path: Optional[str] = None):
        repo_path = repo_path or os.getcwd()
        git_dir = Path(repo_path) / ".git" / "hooks"
        git_dir.mkdir(parents=True, exist_ok=True)

        pre_commit = git_dir / "pre-commit"
        pre_commit.write_text(
            "#!/usr/bin/env bash\n"
            "command -v gitauto >/dev/null 2>&1 && gitauto --ai-commit\n"
        )
        pre_commit.chmod(0o755)

        commit_msg = git_dir / "commit-msg"
        commit_msg.write_text(
            "#!/usr/bin/env bash\n"
            "command -v gitauto >/dev/null 2>&1 && gitauto --ai-commit \"$1\"\n"
        )
        commit_msg.chmod(0o755)

        print(f"{Colors.GREEN}✓ Git hooks installed in {repo_path}{Colors.END}")

    # ----------------------------
    # Smart branch naming
    # ----------------------------
    def suggest_branch_name(self) -> str:
        status = self.get_git_status()
        if not status:
            name = "update-changes"
        else:
            first_file = status[0].split()[1].split("/")[-1].split(".")[0]
            name = f"{first_file}-update"
        print(f"{Colors.CYAN}Suggested branch name: {name}{Colors.END}")
        return name

    # ----------------------------
    # AI commit generation
    # ----------------------------
    def generate_commit_message(self, diff: str) -> Optional[str]:
        provider = self.get_provider()
        api_key = self.get_api_key()
        if not provider or not api_key:
            return None
        print(f"{Colors.CYAN}Generating AI commit message ({provider})...{Colors.END}")
        try:
            if provider=="openai":
                _, OpenAI = lazy_import_openai()
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":f"Generate commit message for changes:\n{diff[:3000]}"}],
                    max_tokens=100
                )
                return resp.choices[0].message.content.strip()
            elif provider=="anthropic":
                anthropic = lazy_import_anthropic()
                client = anthropic.Anthropic(api_key=api_key)
                resp = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    messages=[{"role":"user","content":f"Generate commit message for changes:\n{diff[:3000]}"}],
                    max_tokens=500
                )
                return resp.content[0].text.strip()
            elif provider=="gemini":
                genai = lazy_import_gemini()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-2.5-flash")
                resp = model.generate_content(f"Generate concise commit message:\n{diff[:3000]}")
                return resp.text.strip()
        except Exception as e:
            print(f"{Colors.RED}✗ AI generation failed: {e}{Colors.END}")
        return None

    # ----------------------------
    # Debug mode / logging
    # ----------------------------
    def debug_log(self, msg: str):
        if self.debug:
            print(f"{Colors.YELLOW}[DEBUG]{Colors.END} {msg}")

    # ----------------------------
    # Setup AI provider
    # ----------------------------
    def setup_ai(self):
        provider = input("AI provider (openai/anthropic/gemini): ").strip().lower()
        if provider not in ("openai","anthropic","gemini"):
            print("Invalid provider. Skipping.")
            return
        api_key = input(f"{provider} API key: ").strip()
        if api_key:
            self.save_config({"provider":provider,"api_key":api_key})
            print(f"{Colors.GREEN}✓ Saved AI config.{Colors.END}")

    # ----------------------------
    # Main workflow
    # ----------------------------
    def run(self):
        if not self.is_git_repo():
            print(f"{Colors.RED}✗ Not a git repository.{Colors.END}")
            sys.exit(1)

        branch = self.get_current_branch()
        print(f"{Colors.CYAN}Current branch: {branch}{Colors.END}")
        status = self.get_git_status()
        if status:
            print(f"{Colors.YELLOW}Changes detected:\n{status}{Colors.END}")
        else:
            print(f"{Colors.YELLOW}No changes detected.{Colors.END}")

        # Stage all changes
        self.run_command(["git", "add", "."])

        diff = self.get_diff()
        if not diff:
            print(f"{Colors.YELLOW}No changes to commit.{Colors.END}")
            return

        # Try AI commit first
        msg = None
        if self.get_provider() and self.get_api_key():
            msg = self.generate_commit_message(diff)

        # Fallback to manual message
        if not msg:
            print(f"{Colors.YELLOW}Enter commit message:{Colors.END}")
            msg = input("> ").strip()

        if msg:
            success, _, err = self.run_command(["git", "commit", "-m", msg])
            if success:
                print(f"{Colors.GREEN}✓ Commit created: {msg}{Colors.END}")
            else:
                print(f"{Colors.RED}✗ Commit failed: {err}{Colors.END}")

# ----------------------------
# CLI Entry
# ----------------------------
def main():
    debug_mode = "--debug" in sys.argv
    ga = GitAuto(debug=debug_mode)

    args = sys.argv[1:]

    if not args:
        ga.run()
        return

    if "-v" in args or "--version" in args:
        print(f"GitAuto v{__version__}")
        return

    elif "--install-hooks" in args:
        repo_path = args[1] if len(args) > 1 else None
        ga.install_hooks(repo_path)
        return

    elif "--undo" in args:
        ga.undo_last_commit()
        return

    elif "--suggest-branch" in args:
        ga.suggest_branch_name()
        return

    elif "--setup-model" in args:
        ga.setup_ai()
        return

    elif "--ai-commit" in args:
        ga.run()
        return

    elif "--debug" in args:
        print(f"{Colors.CYAN}Debug mode enabled.{Colors.END}")
        return

    else:
        ga.run()

if __name__=="__main__":
    main()

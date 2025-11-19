# **GitAuto**

GitAuto is a lightweight command-line tool that automates your everyday Git workflow — file staging, commit message generation (with optional AI-generated commit message), branch switching, and pushing changes — all in one guided interactive flow.

---

## **✨ Features**

* Interactive file selection
* AI-generated commit messages (Claude / OpenAI)
* Safe commit-approval loop (no auto-commit unless you confirm)
* Auto branch switch/create
* Auto push with upstream handling
* No configuration required
* Works on Linux, macOS, WSL and Git Bash

---

## **📦 Installation**

### **1. Clone the repository**

```bash
git clone https://github.com/wizdomic/gitauto.git
cd gitauto
```

### **2. Run installer**

```bash
chmod +x install.sh
./install.sh
```

### **3. Reload shell**

```bash
source ~/.bashrc    # or ~/.zshrc
```

Check version:

```bash
gitauto -v
```

---

## **⚙️ AI Commit Message Setup (Optional)**

### Option A → Run setup:

```bash
gitauto setup
```

### Option B → Environment variable:

```bash
export API_KEY="your-api-key"
```

Supports:
✔ Anthropic Claude
✔ OpenAI GPT
❗ Gemini (coming soon)

---

## **🚀 Usage**

Run inside any Git repository:

```bash
gitauto
```

The tool guides you through:

1. Select files (`.` for all)
2. Generate or write commit message
3. Approve commit before saving
4. Switch or create branch
5. Push to remote

---

## **🔧 Commands**

| Command         | Description           |
| --------------- | --------------------- |
| `gitauto`       | Start workflow        |
| `gitauto setup` | Add/Update AI API key |
| `gitauto -v`    | Show version          |
| `gitauto help`  | Show usage help       |

---

## **⬆️ Updating GitAuto**

Already included in repo: **update.sh**

To update:

```bash
chmod +x update.sh
./update.sh
```

---

## **🗑 Uninstallation**

Use the script included: **uninstall.sh**

```bash
chmod +x uninstall.sh
./uninstall.sh
```

This removes:

* `~/.local/bin/gitauto`
* `~/.gitauto`
* `~/.gitauto_venv`
* Dependencies installed by GitAuto

---

## **🐞 Troubleshooting**

### GitAuto not found:

```bash
echo $PATH
```

If `~/.local/bin` missing:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### AI not working:

```bash
gitauto --setup
pip install anthropic openai
```

### Python errors:

```bash
python3 -m venv venv
source venv/bin/activate
```
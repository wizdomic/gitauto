# GitAuto
![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![OS](https://img.shields.io/badge/OS-Linux%20%7C%20macOS%20%7C%20WSL%20%7C%20Git%20Bash-brightgreen)

## Description
GitAuto is a lightweight command-line tool that automates your everyday Git workflow — file staging, commit message generation (with optional AI-generated commit message), branch switching, and pushing changes — all in one guided interactive flow.

---

## ✨ Features

* File selection
* AI-generated commit messages (Claude / OpenAI / Gemini)
* Safe commit approval and regeneration (manual commit also supported)
* Undo commit option
* Auto branch switch/create
* Auto push with upstream handling (hybrid)
* No configuration required (optional AI)
* Works on Linux, macOS, WSL, and Git Bash

---

## 📦 Installation

### 1️⃣ Clone the repository (hidden folder)

```bash
git clone https://github.com/wizdomic/gitauto.git ~/.gitauto
cd ~/.gitauto
````

> `~/.gitauto` is hidden. Use `ls -a` to see it.

---

### 2️⃣ Run installer

```bash
chmod +x install.sh
./install.sh
```

---

### 3️⃣ Reload shell

```bash
source ~/.bashrc    # or source ~/.zshrc
```

---

### 4️⃣ Verify installation

```bash
gitauto -v
```

> If you get **command not found**, add `~/.local/bin` to your PATH:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## ⚙️ AI Commit Message Setup (Optional)

### Option A → Run setup:

```bash
gitauto setup
```

### Option B → Environment variable:

```bash
export API_KEY="your-api-key"
```

> For persistence, add this to `~/.bashrc`:

```bash
echo 'export API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

Supports:

* Anthropic Claude
* OpenAI GPT
* Gemini

---

## 🚀 Usage

Run inside any Git repository:

```bash
gitauto
```

The interactive workflow guides you through:

1. Select files (`.` for all)
2. Generate or write commit message
3. Approve commit before saving
4. Switch or create branch
5. Push to remote

---

## 🔧 Commands

| Command         | Description           |
| --------------- | --------------------- |
| `gitauto`       | Start workflow        |
| `gitauto setup` | Add/Update AI API key |
| `gitauto -v`    | Show version          |

---

## ⬆️ Updating GitAuto

```bash
cd ~/.gitauto
./update.sh
```

---

## 🗑 Uninstallation

```bash
cd ~/.gitauto
./uninstall.sh
```

Removes:

* `~/.local/bin/gitauto`
* `~/.gitauto`
* `~/.gitauto_venv`
* Dependencies installed by GitAuto

---

## 🐞 Troubleshooting

### 1️⃣ GitAuto not found

```bash
echo $PATH
```

If `~/.local/bin` is missing:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

### 2️⃣ AI not working

```bash
gitauto setup
```

---

## 📝 Contributing

We welcome contributions! Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

1. Fork the repo
2. Create a new branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Commit your changes (`git commit -m "Add my feature"`)
5. Push to the branch (`git push origin feature/my-feature`)
6. Open a Pull Request

---

## ⚖️ License

GitAuto is open-source for **personal, educational, or non-commercial use only**.  
Commercial use or selling is strictly prohibited. See the [LICENSE](LICENSE) file for details.

---

## ❤️ Acknowledgements

* Inspired by Git workflow automation needs
* AI-powered commit messages via Claude, OpenAI, Gemini

```

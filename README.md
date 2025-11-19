# GitAuto 🚀

**GitAuto** is a **Git automation tool** that helps developers quickly add, commit, and push changes, with optional **AI-generated commit messages**.

---

## **What it solves**

* Automates staging and committing files.
* Generates concise commit messages using AI (OpenAI, Anthropic, Gemini).
* Handles branch switching and pushing to remote.
* Saves time and keeps commit history clean.

---

## **Installation**

```bash
git clone https://github.com/your-username/GitAuto.git
cd GitAuto
./install.sh
```

Optional: set up AI during install or later with:

```bash
gitauto setup
```

---

## **Usage**

Run inside a Git repository:

```bash
gitauto
```

* Detects changes
* Adds files
* Generates commit messages (manual or AI)
* Switches branches
* Pushes to remote

---

## **Update**

```bash
./update.sh
```

* Pulls latest code
* Updates dependencies
* Updates gitauto script

---

## **Uninstall**

```bash
./uninstall.sh
```

* Removes gitauto script
* Deletes virtual environment
* Optionally removes config and repo clone

---

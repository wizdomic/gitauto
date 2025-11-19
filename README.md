# GitAuto - Intelligent Git Automation Tool

A powerful Python-based command-line tool that streamlines your git workflow with interactive prompts and AI-powered commit message generation.

## Features

- **Interactive File Selection**: Choose specific files or add all changes with a single command
- **AI-Powered Commits**: Generate meaningful commit messages using Claude AI
- **Smart Branch Management**: Easily switch branches or create new ones
- **Automated Push**: Push changes to remote with intelligent upstream handling
- **Beautiful CLI**: Color-coded output with clear status indicators
- **Cross-Platform**: Works on Linux, macOS, and Windows (with WSL)
- **Zero Configuration**: Works out of the box with any git repository

## Prerequisites

- Python 3.8 or higher
- Git
- pip3 (Python package manager)

## Installation

### Quick Install (Linux/macOS)

1. Clone or download this repository:

```bash
git clone https://github.com/wizdomic/gitauto.git
cd gitauto
```

2. Run the installation script:

```bash
chmod +x install.sh
./install.sh
```

3. Reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc for zsh users
```

### Manual Installation

1. Install Python dependencies:

```bash
pip3 install -r requirements.txt
```

2. Copy the script to your local bin:

```bash
mkdir -p ~/.local/bin
cp gitauto.py ~/.local/bin/gitauto
chmod +x ~/.local/bin/gitauto
```

3. Add to PATH (if not already):

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Configuration

### Enable AI Commit Generation (Optional)

To use AI-powered commit message generation:

1. Get an API key from [Anthropic Console](https://console.anthropic.com/) or [OpenAI](https://platform.openai.com/) or from GEMINI(in development)
2. Run the setup command:

```bash
gitauto setup
```

3. Enter your API key when prompted

Alternatively, set the environment variable:

```bash
export API_KEY="your-api-key-here"
```

## Troubleshooting

if it shows any error with python packages, just create a virtual environment with command :

```bash
python3 -m venv venv
source venv/bin/activate
```

### Now command:

```bash
 chmod +x install.sh ### it will install python file containing system configuration
```

```bash
./install.sh ### continue with configuration
```

## Usage

### After Installing It Perfectly

Run

```bash
gitauto -v
```

to check version

### Basic Workflow

Navigate to any git repository and run:

```bash
gitauto
```

The tool will guide you through:

1. **File Selection**: Choose which files to add

   - Enter `.` for all changes
   - Or specify individual files: `file1.py file2.py`

2. **Commit Message**:

   - Use AI to generate a commit message (if configured)
   - Or write your own custom message

3. **Branch Management**:

   - Stay on current branch
   - Switch to existing branch
   - Create and switch to new branch

4. **Push Changes**:
   - Push to remote repository
   - Automatically set upstream if needed

## Testing

Run the test script to verify installation:

```bash
./test.sh
```

This will create a temporary git repository and run through the entire workflow.

## How It Works

1. **Repository Check**: Verifies you're in a git repository
2. **Status Detection**: Shows current changes and branch information
3. **File Staging**: Adds specified files to staging area
4. **Commit Creation**:
   - Optionally generates commit message using Claude AI
   - Analyzes git diff to create meaningful commit messages
   - Follows conventional commit format (feat, fix, docs, etc.)
5. **Branch Operations**: Handles branch switching and creation
6. **Remote Push**: Pushes changes with automatic upstream configuration

## Conventional Commits

When using AI generation, commits follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or modifications
- `chore:` Maintenance tasks

### Command not found

If `gitauto` is not recognized:

1. Ensure `~/.local/bin` is in your PATH:

```bash
echo $PATH | grep ".local/bin"
```

2. If not, add it:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### AI generation not working

1. Verify API key is set:

```bash
gitauto setup
```

2. Check anthropic library is installed:

```bash
pip3 install --user anthropic
```

3. Ensure you have an active API key from [Anthropic Console](https://console.anthropic.com/) or or [OpenAI](https://platform.openai.com/)

### Python version issues

Ensure Python 3.8+:

```bash
python3 --version
```

## Uninstallation

Remove the installed files:

```bash
rm ~/.local/bin/gitauto
rm -rf ~/.gitauto
pip3 uninstall anthropic
```

## Security

- API keys are stored in `~/.gitauto/config.json` with restricted permissions (600)
- Credentials are never logged or transmitted except to Anthropic API
- Only git diff output is sent to AI for commit generation (max 3000 characters)

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - feel free to use and modify as needed.

## Support

For issues, questions, or suggestions:

- Create an issue in the repository
- Check existing issues for solutions
- Review the troubleshooting section above

## Roadmap

Planned features:

- [ ] Support for multiple AI providers (OpenAI, local models)
- [ ] Git hooks integration
- [ ] Team collaboration features
- [ ] Custom commit templates
- [ ] Interactive rebase support
- [ ] Stash management
- [ ] Pull request creation

## Credits

Built with:

- [Python](https://www.python.org/) - Core language
- [Anthropic Claude](https://www.anthropic.com/) / or [OpenAI](https://platform.openai.com/) - AI commit generation
- [Git](https://git-scm.com/) - Version control system

# gitauto
# gitauto
# gitauto

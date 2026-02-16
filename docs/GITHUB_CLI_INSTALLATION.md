# GitHub CLI Installation Guide

GitHub CLI (`gh`) is the official command-line tool for GitHub. It brings pull requests, issues, and other GitHub features to your terminal.

## Installation

### macOS

**Using Homebrew (recommended):**
```bash
brew install gh
```

**Using MacPorts:**
```bash
sudo port install gh
```

**Using Conda:**
```bash
conda install gh --channel conda-forge
```

### Windows

**Using WinGet:**
```bash
winget install --id GitHub.cli
```

**Using Scoop:**
```bash
scoop install gh
```

**Using Chocolatey:**
```bash
choco install gh
```

**Manual download:**
Download the MSI installer from [GitHub CLI Releases](https://github.com/cli/cli/releases/latest).

### Linux

**Debian/Ubuntu:**
```bash
(type -p wget >/dev/null || (sudo apt update && sudo apt-get install wget -y)) \
&& sudo mkdir -p -m 755 /etc/apt/keyrings \
&& wget -qO- https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null \
&& sudo chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
&& echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
&& sudo apt update \
&& sudo apt install gh -y
```

**Fedora/CentOS/RHEL:**
```bash
sudo dnf install 'dnf-command(config-manager)'
sudo dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
sudo dnf install gh
```

**Arch Linux:**
```bash
sudo pacman -S github-cli
```

## Authentication

After installation, authenticate with your GitHub account:

```bash
gh auth login
```

Follow the interactive prompts to:
1. Choose GitHub.com or GitHub Enterprise
2. Select authentication method (HTTPS or SSH)
3. Authenticate via browser or paste a token

## Verify Installation

Check that `gh` is installed correctly:

```bash
gh --version
```

Check authentication status:

```bash
gh auth status
```

## Common Commands

| Command | Description |
|---------|-------------|
| `gh repo clone <repo>` | Clone a repository |
| `gh pr create` | Create a pull request |
| `gh pr list` | List pull requests |
| `gh pr view <number>` | View a pull request |
| `gh pr checkout <number>` | Check out a pull request locally |
| `gh issue create` | Create an issue |
| `gh issue list` | List issues |
| `gh repo view` | View repository info |

## Useful Configuration

Enable shell completions (bash example):
```bash
gh completion -s bash > /etc/bash_completion.d/gh
```

Set default editor:
```bash
gh config set editor vim
```

Set default git protocol:
```bash
gh config set git_protocol ssh
```

## Resources

- [Official Documentation](https://cli.github.com/manual/)
- [GitHub CLI Repository](https://github.com/cli/cli)
- [Release Notes](https://github.com/cli/cli/releases)
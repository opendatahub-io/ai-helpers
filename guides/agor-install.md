# Agor Installation Guide

This guide covers installing Agor version 0.10.0.

> **Documentation**: https://agor.live/
> **Repository**: https://github.com/preset-io/agor

## Prerequisites

### Node.js 20.x

Agor requires Node.js version 20.x.

```bash
# Check your Node.js version
node --version

# If using nvm, switch to Node 20
nvm use 20
```

### Zellij (Required)

Agor requires [Zellij](https://zellij.dev/) >= 0.40 for persistent terminal sessions. **The daemon will not start without it.**

```bash
# macOS
brew install zellij

# Ubuntu/Debian
curl -L https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz | sudo tar -xz -C /usr/local/bin

# RHEL/CentOS
curl -L https://github.com/zellij-org/zellij/releases/latest/download/zellij-x86_64-unknown-linux-musl.tar.gz | sudo tar -xz -C /usr/local/bin

# Verify installation
zellij --version
```

## Fresh Installation

### 1. Install Agor

```bash
# Install Agor 0.10.0 specifically
npm install -g agor-live@0.10.0

# Verify installation
agor --version
```

### 2. Initialize Agor

The `agor init` command creates the `~/.agor/` directory, database, and prompts for authentication setup.

```bash
agor init
```

During initialization, you'll be prompted to:

1. **Enable authentication** (recommended for multiplayer features)
2. **Create an admin account** with email, username, and password

Example interactive flow:
```
✨ Initializing Agor...

📁 Creating directory structure...
   ✓ ~/.agor
   ✓ ~/.agor/repos
   ✓ ~/.agor/worktrees
   ...

💾 Setting up database...
   ✓ Created ~/.agor/agor.db

🌱 Seeding initial data...
   ✓ Created Main Board

? Enable authentication and multiplayer features? (Y/n) Y
   ✓ Enabled authentication

👤 Create your admin account:

? Email: you@example.com
? Username: yourname
? Password: ********
   ✓ Admin user created (you@example.com)
```

#### Non-Interactive Initialization

For scripted/automated setups, use `--force` to skip prompts. This creates a default admin user:

```bash
agor init --force
```

Default credentials (change after first login!):
- **Email**: `admin@agor.live`
- **Password**: `admin`

#### Single-User Mode (No Auth)

If you choose "No" when prompted about authentication, Agor runs in single-user mode. You can enable auth later:

```bash
agor config set daemon.requireAuth true
agor user create-admin
```

### 3. Start the Daemon

```bash
# Start the daemon
agor daemon start

# Verify daemon is running
agor daemon status

# Open the web UI
agor open
```

### 4. Login

After opening the UI, log in with the admin credentials you created during `agor init`.

## Authentication & API Keys

### AI Agent Credentials

Agor checks for AI credentials in this priority order:

1. **Per-User API Keys**: Settings → Agentic Tools (encrypted, per-user scope)
2. **Claude CLI Login**: Run `claude login` (credentials stored in `~/.claude/`)
3. **Environment Variables**: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY`

### Setting API Keys via CLI

```bash
agor config set credentials.ANTHROPIC_API_KEY "sk-ant-..."
agor config set credentials.OPENAI_API_KEY "sk-..."
agor config set credentials.GEMINI_API_KEY "..."
```

### User Management

```bash
# List users
agor user list

# Create additional users
agor user create

# Create admin user (if auth was disabled during init)
agor user create-admin

# Check current user
agor auth whoami
```

## Upgrading from a Previous Version

### 1. Backup Everything

```bash
# Stop daemon first
agor daemon stop

# Backup database
cp ~/.agor/agor.db ~/.agor/agor.db.backup-$(date +%Y%m%d-%H%M%S)

# Backup config
cp ~/.agor/config.yaml ~/.agor/config.yaml.backup-$(date +%Y%m%d-%H%M%S)

# Create full backup archive
tar -czf ~/agor-backup-$(date +%Y%m%d-%H%M%S).tar.gz ~/.agor/
```

### 2. Upgrade

```bash
# Upgrade to version 0.10.0
npm install -g agor-live@0.10.0

# Verify new version
agor --version
```

### 3. Run Migrations

```bash
# Run init to apply any new migrations (safe, idempotent)
agor init --skip-if-exists
```

### 4. Restart Daemon

```bash
agor daemon start
agor daemon status
```

## Troubleshooting

### Daemon Won't Start

If the daemon fails to start, check that Zellij is installed:

```bash
zellij --version
```

### Check Daemon Logs

```bash
agor daemon logs --tail 100
```

### Check Port Bindings

```bash
lsof -i :3030  # daemon
lsof -i :5173  # UI
```

### Gather Debug Info

```bash
# Save daemon logs
agor daemon logs --tail 200 > ~/agor-debug-logs.txt

# Check database
ls -lh ~/.agor/agor.db

# Export config
cat ~/.agor/config.yaml > ~/agor-config-export.yaml

# Check processes
ps aux | grep agor

# Check ports
lsof -i :3030
lsof -i :5173
```

Report issues at: https://github.com/preset-io/agor/issues

## Rollback (If Needed)

```bash
# Stop daemon
agor daemon stop

# Uninstall current version
npm uninstall -g agor-live

# Reinstall previous version
npm install -g agor-live@0.9.2

# Restore database from backup
cp ~/.agor/agor.db.backup-[timestamp] ~/.agor/agor.db

# Start daemon
agor daemon start
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `agor --version` | Check installed version |
| `agor init` | Initialize Agor (interactive) |
| `agor init --force` | Initialize with default admin |
| `agor init --skip-if-exists` | Run migrations only |
| `agor daemon start` | Start the daemon |
| `agor daemon stop` | Stop the daemon |
| `agor daemon status` | Check daemon status |
| `agor daemon logs --tail N` | View last N log lines |
| `agor open` | Open the web UI |
| `agor auth whoami` | Check current user |
| `agor user list` | List all users |
| `agor user create` | Create a new user |
| `agor user create-admin` | Create admin user |

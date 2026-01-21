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

```bash
# Install Agor 0.10.0 specifically
npm install -g agor-live@0.10.0

# Verify installation
agor --version

# Initialize Agor (creates ~/.agor/ directory and database)
agor init

# Start the daemon
agor daemon start

# Verify daemon is running
agor daemon status

# Open the web UI
agor open
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



# Quick Start Guide

Get started with AI Media Organizer in 5 minutes!

## Prerequisites

- Python 3.8+
- Ollama (local or remote)
- TMDB API Key

## Installation

```bash
# 1. Clone and setup
git clone <repository-url>
cd ai-media-organizer
pip install -r requirements.txt

# 2. Copy environment template
cp .env.example .env

# 3. Edit .env with your settings
nano .env  # or use your favorite editor
```

## Configuration

Edit `.env` file:

```bash
# Required: Get from https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_actual_tmdb_api_key

# Optional: Configure Ollama URL
# For local Ollama (default):
LOCAL_AI_URL=http://localhost:11434

# For remote Ollama server:
# LOCAL_AI_URL=http://192.168.1.100:11434
# LOCAL_AI_URL=http://your-server-ip:11434

# For custom domain/proxy:
# LOCAL_AI_URL=http://ai.example.com
# LOCAL_AI_URL=http://10.176.202.207.nip.io
```

**Configuration Examples:**

| Scenario | Configuration |
|----------|---------------|
| **Local Ollama** | `LOCAL_AI_URL=http://localhost:11434` (or omit, uses default from settings.yaml) |
| **Remote Server** | `LOCAL_AI_URL=http://192.168.1.100:11434` |
| **Custom Domain** | `LOCAL_AI_URL=http://ai.example.com` |
| **Nginx Proxy** | `LOCAL_AI_URL=http://server.nip.io` |

## Ollama Setup

### Install and Start Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# For LOCAL use only (default):
ollama serve

# For REMOTE access (allow other machines to connect):
OLLAMA_HOST=0.0.0.0:11434 ollama serve
```

**Important:** 
- **Local only**: Use `ollama serve` (listens on localhost:11434 only)
- **Remote access**: Use `OLLAMA_HOST=0.0.0.0:11434 ollama serve` (allows connections from other machines)

### Permanent Remote Access Setup

If you want Ollama to always accept remote connections:

**Method 1: Systemd Service (Recommended for Linux)**

```bash
# Create systemd override directory
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Create override configuration
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF

# Reload systemd and restart ollama
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Verify it's running
sudo systemctl status ollama
```

**Method 2: Environment Variable (For Manual Start)**

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.bashrc
source ~/.bashrc

# Then start ollama
ollama serve
```

**Verify Remote Access:**

```bash
# From the same machine
curl http://localhost:11434/api/version

# From a remote machine (replace with actual IP)
curl http://192.168.1.100:11434/api/version
```

### Install Ollama Model

```bash
# Pull the AI model (one-time setup)
ollama pull qwen2.5:7b

# Verify it's installed
ollama list
```

## Usage

### Test with Dry Run (Recommended First)

```bash
# Preview what will happen without making changes
python main.py /path/to/movies --type movie --dry-run --verbose
```

### Organize Movies

```bash
# Basic organization
python main.py /path/to/movies --type movie --verbose

# With country folders (e.g., US_United_States, CN_China)
python main.py /path/to/movies --type movie --country-folder --verbose
```

### Organize TV Shows

```bash
python main.py /path/to/tv-shows --type tv --verbose
```

## Configuration Priority

Remember:
1. **`.env` file** = Highest priority (overrides everything)
2. **`config/settings.yaml`** = Default values

## Deployment Architectures

### Local Deployment (Single Machine)

```
┌─────────────────────────────────────┐
│  Your Machine (localhost)           │
│                                      │
│  ┌──────────────────────────────┐  │
│  │  AI Media Organizer          │  │
│  │  (main.py)                   │  │
│  └──────────┬───────────────────┘  │
│             │ HTTP                  │
│             │ localhost:11434       │
│  ┌──────────▼───────────────────┐  │
│  │  Ollama Service              │  │
│  │  OLLAMA_HOST=localhost:11434 │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Setup:**
```bash
# Start Ollama (local only)
ollama serve

# Configure .env (or omit LOCAL_AI_URL)
LOCAL_AI_URL=http://localhost:11434
```

### Remote Deployment (Client-Server)

```
┌──────────────────────┐          ┌──────────────────────────┐
│  Client Machine      │          │  Server Machine          │
│                      │          │  (192.168.1.100)         │
│  ┌────────────────┐ │          │                          │
│  │ AI Media       │ │  HTTP    │  ┌────────────────────┐ │
│  │ Organizer      ├─┼──────────┼─▶│ Ollama Service     │ │
│  │ (main.py)      │ │ :11434   │  │ 0.0.0.0:11434      │ │
│  └────────────────┘ │          │  │ (qwen2.5:7b)       │ │
│                      │          │  └────────────────────┘ │
└──────────────────────┘          └──────────────────────────┘
```

**Setup:**

Server (192.168.1.100):
```bash
# Start Ollama with remote access
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Allow firewall
sudo firewall-cmd --add-port=11434/tcp --permanent
```

Client:
```bash
# Configure .env
LOCAL_AI_URL=http://192.168.1.100:11434
```

## Common Issues

### Connection Error to AI Server

**Problem:** Cannot connect to Ollama

**Solutions:**

```bash
# 1. Check if Ollama is running
curl http://localhost:11434/api/version

# 2. Check Ollama service status (Linux)
sudo systemctl status ollama

# 3. Check what address Ollama is listening on
sudo netstat -tlnp | grep 11434
# or
sudo ss -tlnp | grep 11434

# 4. If connecting from remote machine:
# - Ensure Ollama is listening on 0.0.0.0:11434
# - Check firewall allows port 11434
sudo firewall-cmd --add-port=11434/tcp --permanent  # Fedora/RHEL
sudo ufw allow 11434/tcp                             # Ubuntu/Debian
```

**Remote Connection Checklist:**
- ✅ Ollama started with `OLLAMA_HOST=0.0.0.0:11434`
- ✅ Firewall allows port 11434
- ✅ `.env` has correct `LOCAL_AI_URL`
- ✅ Server IP/domain is reachable: `ping your-server-ip`

### TMDB API Error

- Verify your API key in `.env`
- Get key from: https://www.themoviedb.org/settings/api

## Next Steps

- Check `README.md` for detailed documentation
- Review logs in `logs/` directory
- Customize prompts in `config/settings.yaml`

## Example Output Structure

```
Movies/
├── US_United_States/
│   └── Inception-盗梦空间-2010-tt1375666-27205/
│       ├── Inception-盗梦空间-2010-tt1375666-27205-1080p-BluRay-H264.mkv
│       ├── media_info.nfo
│       └── poster.jpg
└── CN_China/
    └── 让子弹飞-Let the Bullets Fly-2010-tt1533117-50800/
        ├── 让子弹飞-Let the Bullets Fly-2010-tt1533117-50800-1080p.mkv
        ├── media_info.nfo
        └── poster.jpg
```

## Help

```bash
# Show all options
python main.py --help

# Check logs
tail -f logs/media_organizer.log
```

For more details, see [README.md](README.md)

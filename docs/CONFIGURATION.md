# Configuration Guide

This document explains the configuration system in detail.

## Configuration Architecture

AI Media Organizer uses a two-tier configuration system:

```
┌─────────────────────────────────────┐
│  .env file (Environment Variables)  │  ← Highest Priority
│  - API Keys                          │
│  - Server URLs                       │
│  - Sensitive Information             │
└─────────────────────────────────────┘
              ↓ overrides
┌─────────────────────────────────────┐
│  config/settings.yaml                │  ← Default Configuration
│  - Application Defaults              │
│  - AI Prompts                        │
│  - File Extensions                   │
│  - Processing Parameters             │
└─────────────────────────────────────┘
```

## Priority Rules

1. **`.env` file has the highest priority**
   - Values set here override `config/settings.yaml`
   - Used for environment-specific settings
   - Not tracked in version control (in `.gitignore`)

2. **`config/settings.yaml` provides defaults**
   - Used when `.env` doesn't specify a value
   - Tracked in version control
   - Shared across all environments

## Environment Variables (`.env`)

### Setup

```bash
# Copy the template
cp .env.example .env

# Edit with your settings
nano .env
```

### Available Variables

#### TMDB_API_KEY (Required)

Your TMDB API key for fetching movie/TV metadata.

```bash
TMDB_API_KEY=your_actual_api_key_here
```

**Get your key:**
1. Register at https://www.themoviedb.org/
2. Go to Settings → API
3. Request an API key (free)

#### LOCAL_AI_URL (Optional)

URL to your Ollama server. If not set, uses value from `config/settings.yaml`.

```bash
# Local Ollama (default)
LOCAL_AI_URL=http://localhost:11434

# Remote Ollama
LOCAL_AI_URL=http://192.168.1.100:11434

# Custom domain
LOCAL_AI_URL=http://ai.example.com

# With nginx proxy
LOCAL_AI_URL=http://server.nip.io
```

**When to set this:**
- You're using a remote Ollama server
- You're using a custom port
- You're using a proxy or custom domain
- You want to override the default in `settings.yaml`

**When NOT to set this:**
- Using local Ollama on default port (11434)
- The value in `settings.yaml` is already correct

**Setting up Remote Ollama Server:**

If you're running Ollama on a separate machine, you need to configure it to accept remote connections:

```bash
# On the Ollama server machine:

# Method 1: One-time (temporary)
OLLAMA_HOST=0.0.0.0:11434 ollama serve

# Method 2: Permanent (systemd)
sudo mkdir -p /etc/systemd/system/ollama.service.d
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
EOF
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Method 3: Environment variable
echo 'export OLLAMA_HOST=0.0.0.0:11434' >> ~/.bashrc
source ~/.bashrc
ollama serve

# Configure firewall
sudo firewall-cmd --add-port=11434/tcp --permanent  # Fedora/RHEL
sudo firewall-cmd --reload
sudo ufw allow 11434/tcp                             # Ubuntu/Debian

# Verify remote access
curl http://server-ip:11434/api/version
```

**Security Considerations:**
- Ollama has no built-in authentication
- Only expose to trusted networks
- Consider using VPN or SSH tunnel for internet access
- Use firewall rules to restrict access by IP

## YAML Configuration (`config/settings.yaml`)

### API Settings

```yaml
api:
  tmdb_base_url: "https://api.themoviedb.org/3"
  local_ai_url: "http://localhost:11434"  # Default AI server
  timeout: 60  # API timeout in seconds
  ai_model: "qwen2.5:7b"  # AI model to use
```

**AI Model Options:**
- `qwen2.5:7b` - Fast, 7B parameters (recommended for testing)
- `qwen2.5:32b` - Better accuracy, 32B parameters (recommended for production)
- `qwen2.5:72b` - Best accuracy, 72B parameters (requires powerful hardware)

### Prompts

Customize AI prompts for parsing movie and TV show names:

```yaml
prompts:
  movie: |
    分析以下电影文件名，提取电影信息：
    文件名: {filename}
    ...
  
  tv_show: |
    分析以下TV剧集文件夹名，提取剧集信息：
    文件夹名: {filename}
    ...
```

**Customization Tips:**
- Add more context or examples to improve parsing
- Adjust language for better results
- Include specific instructions for your naming conventions

### Video Settings

```yaml
video:
  extensions: [".mp4", ".mkv", ".avi", ...]
  sample_patterns: ["sample", "Sample", "SAMPLE"]
```

**Customization:**
- Add custom video extensions
- Define patterns to identify sample files

### Subtitle Settings

```yaml
subtitle:
  extensions: [".srt", ".ass", ".ssa", ...]
  folder_names: ["subtitle", "subtitles", "subs", "字幕"]
```

**Customization:**
- Add custom subtitle formats
- Define folder names that contain subtitles

### Processing Settings

```yaml
processing:
  batch_size: 10  # Files to process in one batch
  max_retries: 3  # Retry attempts for failed operations
  dry_run: false  # Default mode (can be overridden by CLI)
```

## Configuration Examples

### Example 1: Local Development

**.env:**
```bash
TMDB_API_KEY=abc123def456
# LOCAL_AI_URL not set - uses default from settings.yaml
```

**config/settings.yaml:**
```yaml
api:
  local_ai_url: "http://localhost:11434"
  ai_model: "qwen2.5:7b"  # Fast model for testing
```

### Example 2: Remote Ollama Server

**.env:**
```bash
TMDB_API_KEY=abc123def456
LOCAL_AI_URL=http://192.168.1.100:11434  # Override to use remote server
```

**config/settings.yaml:**
```yaml
api:
  local_ai_url: "http://localhost:11434"  # Default (overridden by .env)
  ai_model: "qwen2.5:32b"  # Better accuracy
```

### Example 3: Production with Custom Domain

**.env:**
```bash
TMDB_API_KEY=production_api_key
LOCAL_AI_URL=http://ai-server.company.com
```

**config/settings.yaml:**
```yaml
api:
  local_ai_url: "http://localhost:11434"  # Default (overridden by .env)
  ai_model: "qwen2.5:72b"  # Best accuracy
  timeout: 120  # Longer timeout for large model
```

## Best Practices

### 1. Use `.env` for Secrets

✅ **DO:**
```bash
# .env
TMDB_API_KEY=your_secret_key
```

❌ **DON'T:**
```yaml
# config/settings.yaml
api:
  tmdb_api_key: "your_secret_key"  # Don't commit secrets!
```

### 2. Use `settings.yaml` for Defaults

✅ **DO:**
```yaml
# config/settings.yaml
api:
  ai_model: "qwen2.5:7b"
  timeout: 60
```

### 3. Override Only When Necessary

Only set `LOCAL_AI_URL` in `.env` if you need to override the default:

```bash
# Only if using remote server or custom setup
LOCAL_AI_URL=http://custom-server:11434
```

### 4. Document Custom Settings

If you modify `settings.yaml`, add comments:

```yaml
api:
  ai_model: "qwen2.5:32b"  # Using 32B for better Chinese name recognition
  timeout: 90  # Increased for slower server
```

## Troubleshooting

### Configuration Not Taking Effect

**Problem:** Changes to `.env` or `settings.yaml` don't work.

**Solutions:**
1. Restart the application after changing `.env`
2. Check `.env` is in the project root directory
3. Verify `.env` syntax (no quotes around values unless needed)
4. Use `--verbose` to see which config is loaded

### Can't Connect to AI Server

**Problem:** `Connection reset by peer` or `Connection refused` error.

**Solutions:**

**Step 1: Verify Ollama is Running**
```bash
# Check service status
sudo systemctl status ollama

# Check process
ps aux | grep ollama

# Try starting manually
ollama serve
```

**Step 2: Check Listening Address**
```bash
# See what address Ollama is listening on
sudo netstat -tlnp | grep 11434
# or
sudo ss -tlnp | grep 11434

# Expected output for local only:
# tcp  0  0  127.0.0.1:11434  0.0.0.0:*  LISTEN

# Expected output for remote access:
# tcp  0  0  0.0.0.0:11434    0.0.0.0:*  LISTEN
```

**Step 3: Test Connection**
```bash
# Local test
curl http://localhost:11434/api/version

# Remote test (from client machine)
curl http://your-server-ip:11434/api/version

# Should return: {"version":"0.x.x"}
```

**Step 4: Check Firewall (for remote access)**
```bash
# Fedora/RHEL/CentOS
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=11434/tcp --permanent
sudo firewall-cmd --reload

# Ubuntu/Debian
sudo ufw status
sudo ufw allow 11434/tcp
sudo ufw reload

# Check if port is accessible from outside
# (run from client machine)
telnet your-server-ip 11434
# or
nc -zv your-server-ip 11434
```

**Step 5: Verify Configuration**
```bash
# Check environment variables
env | grep OLLAMA

# Check .env file
cat .env | grep LOCAL_AI_URL

# Verify config/settings.yaml
cat config/settings.yaml | grep local_ai_url
```

**Common Issues:**

| Symptom | Cause | Solution |
|---------|-------|----------|
| `Connection refused` | Ollama not running | Start with `ollama serve` |
| `Connection refused` | Wrong port | Verify using port 11434 |
| `Connection timeout` | Firewall blocking | Open port 11434 |
| `Connection timeout` | Wrong IP address | Check server IP |
| Works locally but not remotely | Listening on 127.0.0.1 only | Set `OLLAMA_HOST=0.0.0.0:11434` |
| Inconsistent behavior | Config mismatch | Check `.env` vs `settings.yaml` |

### TMDB API Errors

**Problem:** API authentication fails.

**Solutions:**
1. Verify `TMDB_API_KEY` in `.env` is correct
2. Check key has read permissions
3. Test key: `curl "https://api.themoviedb.org/3/movie/550?api_key=YOUR_KEY"`

## Advanced Configuration

### Custom Prompts

Edit `config/settings.yaml` to customize AI prompts:

```yaml
prompts:
  movie: |
    Your custom prompt here...
    Include examples of your file naming conventions.
    
    File: {filename}
    
    Return JSON with: title, original_title, year, confidence
```

### Multiple Environments

Use different `.env` files for different environments:

```bash
# Development
cp .env.example .env.dev
# Edit .env.dev

# Production
cp .env.example .env.prod
# Edit .env.prod

# Load specific environment
ln -sf .env.dev .env  # Use dev config
ln -sf .env.prod .env  # Use prod config
```

## See Also

- [README.md](../README.md) - Main documentation
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
- [.env.example](../.env.example) - Environment template

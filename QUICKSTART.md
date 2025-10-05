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

# Optional: Only if you need to override config/settings.yaml
LOCAL_AI_URL=http://localhost:11434
```

## Install Ollama Model

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

## Common Issues

### Connection Error to AI Server

```bash
# Test if Ollama is accessible
curl http://localhost:11434/api/version

# If using remote server, update .env:
LOCAL_AI_URL=http://your-server-ip:11434
```

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

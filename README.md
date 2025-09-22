# AI Media Organizer

Automatically organize movie and TV show files using local AI and TMDB API. This tool intelligently recognizes Chinese and English media titles, fetches metadata from TMDB, and organizes files into a structured format compatible with media centers like Kodi.

## Features

- **AI-Powered Recognition**: Uses local AI (Ollama) to parse movie and TV show names from filenames
- **Multi-Language Support**: Handles Chinese and English titles intelligently
- **TMDB Integration**: Fetches accurate metadata, cast, directors, and posters
- **Smart File Organization**: Creates organized folder structures with proper naming
- **NFO File Generation**: Generates Kodi-compatible metadata files
- **Poster Download**: Automatically downloads movie posters
- **Subtitle Support**: Moves subtitle files and folders along with video files
- **Idempotent Operations**: Safe to run multiple times without duplicating work
- **Dry Run Mode**: Preview changes before applying them

## Quick Start

### 1. Prerequisites

- **Python 3.8+**
- **Ollama** running locally (for AI parsing)
- **TMDB API Key** (free registration required)

### 2. Install Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a language model (in another terminal)
ollama pull llama3.1:8b
```

### 3. Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd ai-media-organizer

# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 4. Configure API Keys

Edit `.env` file with your settings:

```bash
# Get TMDB API key from: https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_actual_api_key_here

# Verify Ollama is running on correct port
LOCAL_AI_URL=http://localhost:11434
```

### 5. Organize Your Media

```bash
# Organize movies (dry run first to preview)
python main.py /path/to/your/movies --type movie --dry-run --verbose

# Apply changes
python main.py /path/to/your/movies --type movie --verbose

# Organize TV shows
python main.py /path/to/your/tv-shows --type tv --verbose
```

## Usage Examples

### Basic Movie Organization
```bash
python main.py /media/movies --type movie
```

### TV Show Organization with Preview
```bash
python main.py /media/tv-shows --type tv --dry-run --verbose
```

### Verbose Output for Debugging
```bash
python main.py /media/movies --type movie --verbose
```

## File Naming Convention

### Movies
```
[Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID/
├── [Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID-resolution-format-codec-bitdepth-audio.ext
├── media_info.nfo
├── poster.jpg
└── [subtitle files]
```

### TV Shows (Future Feature)
```
[Show Original Title]-[Show Title]-IMDB_ID-TMDB_ID/
└── S01-Year/
    ├── [Show Original Title]-S01E01-[Episode Original Title]-[Episode Title]-format-codec-bitdepth-audio.ext
    ├── media_info.nfo
    └── poster.jpg
```

## Configuration

Edit `config/settings.yaml` to customize:
- AI prompts for parsing
- Video file extensions
- Sample file patterns
- API timeouts
- Subtitle file handling

## Troubleshooting

### Common Issues

**1. AI Parsing Errors**
- Ensure Ollama is running: `ollama serve`
- Check if model is available: `ollama list`
- Verify LOCAL_AI_URL in `.env`

**2. TMDB API Errors**
- Verify your API key is correct
- Check internet connection
- Ensure API key has proper permissions

**3. File Permission Errors**
- Ensure write permissions to target directories
- Run with appropriate user permissions

### Logs
Check logs for detailed information:
```bash
tail -f logs/media_organizer.log
tail -f logs/ai_responses.log
```

## CLI Options

```
Usage: main.py [OPTIONS] PATH

Options:
  --dry-run          Preview mode, do not actually move files
  --type [movie|tv]  Media type to process  [required]
  -v, --verbose      Enable verbose output
  --version          Show the version and exit.
  --help             Show this message and exit.
```

## Safety Features

- **Idempotent**: Safe to run multiple times
- **Backup**: Original files are moved, not copied
- **Organized Folder Detection**: Skips already organized content
- **Unmatched Files**: Files that cannot be identified are moved to `Unmatched` folder
- **Cleanup**: Redundant empty folders are moved to `Unwanted` folder

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests.

# AI Media Organizer

Automatically organize movie and TV show files using local AI and TMDB API. This tool intelligently recognizes Chinese and English media titles, fetches metadata from TMDB, and organizes files into a structured format compatible with media centers like Kodi.

📚 **Documentation:**
- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Configuration Guide](docs/CONFIGURATION.md) - Detailed configuration documentation
- [中文架构设计](docs/zh/architecture-design.md) - Architecture design (Chinese)
- [中文实现计划](docs/zh/implementation-plan.md) - Implementation plan (Chinese)

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
- **Ollama** running locally or remotely (for AI parsing)
- **TMDB API Key** (free registration required at https://www.themoviedb.org/settings/api)

### 2. Install Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a language model (in another terminal)
ollama pull qwen2.5:7b
# Or use a larger model for better accuracy:
# ollama pull qwen2.5:32b
```

### 3. Setup Project

```bash
# Clone the repository
git clone <repository-url>
cd ai-media-organizer

# Install Python dependencies
pip install -r requirements.txt

# Copy the environment template
cp .env.example .env
```

### 4. Configure Settings

**Configuration Priority (High to Low):**
1. **Environment variables in `.env` file** (highest priority, overrides everything)
2. **`config/settings.yaml` file** (default configuration)

#### Create `.env` File

Create a `.env` file in the project root with your API settings:

```bash
# TMDB API Key (Required)
# Get your key from: https://www.themoviedb.org/settings/api
TMDB_API_KEY=your_actual_tmdb_api_key_here

# Local AI URL (Optional - overrides config/settings.yaml if set)
# For local Ollama:
LOCAL_AI_URL=http://localhost:11434
# For remote Ollama:
# LOCAL_AI_URL=http://your-server-ip:11434
# Or with custom domain:
# LOCAL_AI_URL=http://your-server.example.com
```

**Important Notes:**
- `.env` file settings will **override** `config/settings.yaml`
- If you don't set `LOCAL_AI_URL` in `.env`, the value from `config/settings.yaml` will be used
- Never commit `.env` file to version control (it's in `.gitignore`)

#### Customize `config/settings.yaml` (Optional)

You can also edit `config/settings.yaml` for additional settings:

```yaml
api:
  tmdb_base_url: "https://api.themoviedb.org/3"
  local_ai_url: "http://localhost:11434"  # Default AI server URL
  timeout: 60
  ai_model: "qwen2.5:7b"  # Options: qwen2.5:7b, qwen2.5:32b, qwen2.5:72b

video:
  extensions: [".mp4", ".mkv", ".avi", ...]  # Supported video formats
  
subtitle:
  extensions: [".srt", ".ass", ".ssa", ...]  # Supported subtitle formats
  
processing:
  batch_size: 10
  max_retries: 3
```

### 5. Organize Your Media

```bash
# Step 1: Dry run to preview changes (recommended first time)
python main.py /path/to/your/movies --type movie --dry-run --verbose

# Step 2: Apply changes after reviewing
python main.py /path/to/your/movies --type movie --verbose

# For TV shows:
python main.py /path/to/your/tv-shows --type tv --verbose

# Organize movies into country-based folders:
python main.py /path/to/your/movies --type movie --country-folder --verbose
```

## Usage Examples

### Basic Movie Organization
```bash
# Simple movie organization
python main.py /media/movies --type movie

# With verbose output to see what's happening
python main.py /media/movies --type movie --verbose
```

### Movie Organization with Country Folders
```bash
# Organize movies into country-based folders (e.g., US_United_States, CN_China)
python main.py /media/movies --type movie --country-folder --verbose
```

### TV Show Organization
```bash
# Organize TV shows
python main.py /media/tv-shows --type tv --verbose

# Preview changes first (dry run)
python main.py /media/tv-shows --type tv --dry-run --verbose
```

### Preview Mode (Dry Run)
```bash
# Preview changes without actually moving files
python main.py /media/movies --type movie --dry-run --verbose

# Review the planned operations, then run without --dry-run to apply
python main.py /media/movies --type movie --verbose
```

### Real-World Example
```bash
# Step 1: Test with a small subset first
python main.py /media/test-movies --type movie --dry-run --verbose

# Step 2: Review logs to ensure correct parsing
tail -f logs/media_organizer.log

# Step 3: Apply to full library
python main.py /media/movies --type movie --country-folder --verbose
```

## File Naming Convention

### Movies (Standard Organization)
```
[Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID/
├── [Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID-resolution-format-codec-bitdepth-audio.ext
├── media_info.nfo
├── poster.jpg
└── [subtitle files]
```

**Example:**
```
Inception-盗梦空间-2010-tt1375666-27205/
├── Inception-盗梦空间-2010-tt1375666-27205-1080p-BluRay-H264-10bit-DTS.mkv
├── media_info.nfo
└── poster.jpg
```

### Movies (With Country Folders)

When using `--country-folder` option:

```
XX_Country_Name/
└── [Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID/
    ├── [Original Title]-[Localized Title]-Year-IMDB_ID-TMDB_ID-resolution-format-codec-bitdepth-audio.ext
    ├── media_info.nfo
    ├── poster.jpg
    └── [subtitle files]
```

**Example:**
```
US_United_States/
└── Inception-盗梦空间-2010-tt1375666-27205/
    ├── Inception-盗梦空间-2010-tt1375666-27205-1080p-BluRay-H264-10bit-DTS.mkv
    ├── media_info.nfo
    └── poster.jpg

CN_China/
└── 让子弹飞-Let the Bullets Fly-2010-tt1533117-50800/
    ├── 让子弹飞-Let the Bullets Fly-2010-tt1533117-50800-1080p-BluRay-H265-10bit-AAC.mkv
    ├── media_info.nfo
    └── poster.jpg
```

### TV Shows
```
[Show Original Title]-[Show Title]-IMDB_ID-TMDB_ID/
└── S01-Year/
    ├── [Show Original Title]-S01E01-[Episode Original Title]-[Episode Title]-format-codec-bitdepth-audio.ext
    ├── media_info.nfo
    └── poster.jpg
```

**Example:**
```
Game of Thrones-权力的游戏-tt0944947-1399/
└── S01-2011/
    ├── Game of Thrones-S01E01-Winter Is Coming-凛冬将至-1080p-BluRay-H265-10bit-DTS.mkv
    ├── media_info.nfo
    └── poster.jpg
```

## Configuration

### Configuration Priority

The application uses a two-tier configuration system:

1. **`.env` file** (Highest Priority)
   - Environment-specific settings
   - API keys and sensitive information
   - Overrides `config/settings.yaml` values
   - Not tracked in version control

2. **`config/settings.yaml`** (Default Configuration)
   - Application defaults
   - AI prompts and model settings
   - File extensions and patterns
   - Processing parameters

### Environment Variables (`.env`)

Create a `.env` file in the project root:

```bash
# Required
TMDB_API_KEY=your_tmdb_api_key

# Optional (overrides config/settings.yaml if set)
LOCAL_AI_URL=http://localhost:11434
```

**Available Environment Variables:**
- `TMDB_API_KEY` - Your TMDB API key (required)
- `LOCAL_AI_URL` - URL to your Ollama server (optional, defaults to value in settings.yaml)

### YAML Configuration (`config/settings.yaml`)

Customize default settings:

```yaml
api:
  tmdb_base_url: "https://api.themoviedb.org/3"
  local_ai_url: "http://localhost:11434"  # Default if not in .env
  timeout: 60
  ai_model: "qwen2.5:7b"  # Model to use: qwen2.5:7b, qwen2.5:32b, qwen2.5:72b

prompts:
  movie: |
    # Custom AI prompt for movie parsing
  tv_show: |
    # Custom AI prompt for TV show parsing

video:
  extensions: [".mp4", ".mkv", ".avi", ".mov", ...]
  sample_patterns: ["sample", "Sample", "SAMPLE"]

subtitle:
  extensions: [".srt", ".ass", ".ssa", ".sub", ...]
  folder_names: ["subtitle", "subtitles", "subs", "字幕"]

processing:
  batch_size: 10
  max_retries: 3
  dry_run: false
```

**Customizable Settings:**
- AI prompts for parsing logic
- Video file extensions to recognize
- Sample file patterns to ignore
- API timeouts and retry limits
- Subtitle file handling rules

## Troubleshooting

### Common Issues

**1. AI Connection Errors (`Connection reset by peer`)**

This usually means the AI server URL is incorrect or the server is not accessible.

```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Test AI generation
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen2.5:7b","prompt":"test","stream":false}'
```

**Solutions:**
- Verify `LOCAL_AI_URL` in `.env` file matches your Ollama server
- For local Ollama: `LOCAL_AI_URL=http://localhost:11434`
- For remote Ollama: `LOCAL_AI_URL=http://your-server-ip:11434`
- Ensure Ollama is running: `ollama serve`
- Check if model is available: `ollama list`
- If using a custom domain or proxy, verify the URL is accessible

**2. AI Parsing Errors**
- Ensure the correct model is pulled: `ollama pull qwen2.5:7b`
- Check model name in `config/settings.yaml` matches installed model
- Increase timeout in `config/settings.yaml` if model is slow
- Try with `--verbose` flag to see detailed AI responses

**3. TMDB API Errors**
- Verify `TMDB_API_KEY` in `.env` is correct
- Get your key from: https://www.themoviedb.org/settings/api
- Check internet connection
- Ensure API key has proper permissions (read access required)

**4. File Permission Errors**
- Ensure write permissions to target directories
- Run with appropriate user permissions
- Check if files are in use by other applications

**5. Configuration Not Taking Effect**

Remember the priority order:
1. `.env` file overrides everything
2. `config/settings.yaml` is the default

If your changes aren't working:
- Check if `.env` file exists and has the correct values
- Verify `.env` file is in the project root directory
- Restart the application after changing `.env`
- Use `--verbose` to see which configuration is being used

### Logs

Check logs for detailed information:
```bash
# Main application log
tail -f logs/media_organizer.log

# AI responses and parsing details
tail -f logs/ai_responses.log

# Scan session results (JSON format)
cat logs/scan_session_*.json | jq
```

## CLI Options

```
Usage: main.py [OPTIONS] PATH

Arguments:
  PATH                    Directory path to scan for media files

Options:
  --dry-run              Preview mode, do not actually move files
  --type [movie|tv]      Media type to process  [required]
  --country-folder       Organize movies into country-based folders (e.g., US_United_States, CN_China)
  -v, --verbose          Enable verbose output with detailed logging
  --version              Show the version and exit
  --help                 Show this message and exit

Examples:
  # Dry run to preview changes
  python main.py /media/movies --type movie --dry-run --verbose
  
  # Organize movies with country folders
  python main.py /media/movies --type movie --country-folder
  
  # Organize TV shows
  python main.py /media/tv-shows --type tv --verbose
```

## Safety Features

- **Idempotent**: Safe to run multiple times - already organized content is automatically skipped
- **Non-Destructive**: Original files are moved, not copied or deleted
- **Organized Folder Detection**: Automatically detects and skips already organized content
- **Unmatched Files**: Files that cannot be identified are moved to `Unmatched` folder for manual review
- **Cleanup**: Redundant empty folders are moved to `Unwanted` folder
- **Dry Run Mode**: Preview all changes before applying them with `--dry-run`

## FAQ

### Q: What's the difference between `.env` and `config/settings.yaml`?

**A:** `.env` is for environment-specific settings (like API keys and server URLs) and has the highest priority. `config/settings.yaml` contains default application settings. Any value in `.env` will override the corresponding value in `config/settings.yaml`.

### Q: Do I need to set `LOCAL_AI_URL` in `.env`?

**A:** No, it's optional. If you don't set it in `.env`, the application will use the value from `config/settings.yaml`. Only set it in `.env` if you need to override the default.

### Q: Can I run this on a remote server?

**A:** Yes! You can run the organizer on one machine and connect to an Ollama server on another machine. Just set `LOCAL_AI_URL` in `.env` to point to your remote server (e.g., `http://192.168.1.100:11434`).

### Q: What happens to files that can't be identified?

**A:** Files that cannot be parsed by AI or matched with TMDB are moved to an `Unmatched` folder in the same directory. You can manually review and organize these files later.

### Q: Is it safe to run multiple times on the same directory?

**A:** Yes! The tool is idempotent - it automatically detects already organized content and skips it. You can safely run it multiple times.

### Q: Which AI model should I use?

**A:** 
- `qwen2.5:7b` - Fast, good for most cases (recommended for testing)
- `qwen2.5:32b` - Better accuracy, slower (recommended for production)
- `qwen2.5:72b` - Best accuracy, requires more resources

### Q: Can I organize both movies and TV shows in the same directory?

**A:** It's recommended to organize them separately by running the tool twice with different `--type` options. The tool processes one media type at a time.

### Q: What video formats are supported?

**A:** The tool supports all common video formats including: `.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.rmvb`, `.m4v`, `.ts`, `.mts`, `.m2ts`, and more. See `config/settings.yaml` for the full list.

### Q: How do I test without making changes?

**A:** Use the `--dry-run` flag to preview all changes without actually moving any files:
```bash
python main.py /path/to/movies --type movie --dry-run --verbose
```

### Q: What if I want to change the folder naming format?

**A:** The folder naming format is defined in the code (`src/organizer.py`). You can modify the `_generate_folder_name()` and `_generate_filename()` methods to customize the naming convention.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read the contributing guidelines and submit pull requests.

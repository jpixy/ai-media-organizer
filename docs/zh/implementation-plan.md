# AI媒体管理器实施计划

## 总体目标

实现一个能够自动整理电影和TV剧集文件的CLI工具，使用本地AI解析文件名，通过TMDB获取元数据，按照规定格式重新组织文件结构。

## 核心功能要求

### 电影处理
- AI解析文件名获取电影名称和年份
- TMDB API获取详细信息
- 按格式重命名：`[${originalTitle}]-[${title}]-${year}-${imdb}-${tmdb}`
- 生成.nfo文件和下载海报

### TV剧集处理  
- AI解析文件夹名获取剧集名称和年份
- TMDB API获取剧集和季度信息
- 剧集文件夹：`[${showOriginalTitle}]-[${showTitle}]-${showImdb}-${showTmdb}`
- 季度文件夹：`S${seasonNr2}-${showYear}`
- 剧集文件批量重命名（不使用AI，直接解析S01E01格式）
- 生成季度级别.nfo文件和海报

### 异常处理
- **Unmatched文件夹**：存放AI解析失败或TMDB无法匹配的视频文件
- **Unwanted文件夹**：存放整理完成后剩余的冗余文件夹和文件

## 实施步骤

### 第1步：项目基础搭建 (1天)
```bash
# 创建项目结构
mkdir -p src config tests
touch main.py requirements.txt config/settings.yaml
```

**依赖安装：**
```python
# requirements.txt
click>=8.0.0
requests>=2.28.0  
pyyaml>=6.0
python-dotenv>=0.19.0
ffmpeg-python>=0.2.0
tmdbv3api>=1.7.0
```

**基本配置：**
```yaml
# config/settings.yaml
api:
  tmdb_base_url: "https://api.themoviedb.org/3"
  local_ai_url: "http://localhost:8080"
  timeout: 30

video:
  extensions: [".mp4", ".mkv", ".avi", ".mov", ".wmv"]
  sample_patterns: ["sample", "Sample", "SAMPLE"]
```

### 第2步：核心类框架 (1天)

**创建三个核心文件：**
```python
# src/scanner.py
class MediaScanner:
    def scan_directory(self, path: str) -> List[MediaFile]
    def parse_with_ai(self, name: str, media_type: str) -> ParsedInfo
    def analyze_video(self, file_path: str) -> VideoInfo

# src/matcher.py  
class TMDBMatcher:
    def search_movie(self, title: str, year: int) -> MovieInfo
    def search_tv_show(self, title: str, year: int) -> TVShowInfo
    def get_season_info(self, show_id: str, season: int) -> SeasonInfo

# src/organizer.py
class FileOrganizer:
    def organize_movie(self, movie_info: MovieInfo, source: str)
    def organize_tv_show(self, show_info: TVShowInfo, source: str)
    def generate_nfo(self, info: MediaInfo, path: str)
    def move_to_unmatched(self, file_path: str)
    def cleanup_unwanted(self, source_dir: str)
```

### 第3步：文件扫描功能 (1天)

**实现目录扫描：**
- 递归扫描视频文件
- 过滤Sample文件
- 区分电影文件和TV剧集文件夹结构

**关键代码逻辑：**
```python
def scan_directory(self, path):
    video_files = []
    for root, dirs, files in os.walk(path):
        # 过滤sample文件夹
        dirs[:] = [d for d in dirs if not any(s in d.lower() for s in SAMPLE_PATTERNS)]
        
        for file in files:
            if self._is_video_file(file):
                video_files.append(os.path.join(root, file))
    return video_files
```

### 第4步：本地AI集成 (2天)

**AI解析实现：**
```python
def parse_with_ai(self, name, media_type):
    if media_type == "movie":
        prompt = f"解析电影文件名：{name}，返回JSON: {{\"title\":\"中文名\", \"original_title\":\"英文名\", \"year\":年份}}"
    else:
        prompt = f"解析TV剧集文件夹名：{name}，返回JSON: {{\"title\":\"中文名\", \"original_title\":\"英文名\", \"year\":年份}}"
    
    response = requests.post(LOCAL_AI_URL, json={"prompt": prompt})
    return json.loads(response.json()["content"])
```

**测试数据：**
- 电影：`阿凡达.Avatar.2009.1080p.BluRay.x264.mkv`
- TV剧集文件夹：`权力的游戏.Game.of.Thrones/`

### 第5步：TMDB API集成 (2天)

**API调用实现：**
```python
def search_movie(self, title, year):
    # 先用英文名搜索
    results = tmdb.search().movie(query=title, year=year)
    if not results:
        # 再用中文名搜索
        results = tmdb.search().movie(query=title, year=year)
    return results[0] if results else None

def get_season_info(self, show_id, season_num):
    season = tmdb.TV_Seasons(show_id, season_num)
    return {
        "air_date": season.air_date,
        "poster_path": season.poster_path,
        "overview": season.overview
    }
```

### 第6步：文件重组功能 (2天)

**电影重组：**
```python
def organize_movie(self, movie_info, source_path):
    folder_name = f"[{movie_info.original_title}]-[{movie_info.title}]-{movie_info.year}-{movie_info.imdb_id}-{movie_info.tmdb_id}"
    # 创建文件夹并移动文件
```

**TV剧集重组：**
```python
def organize_tv_show(self, show_info, source_path):
    # 1. 创建剧集主文件夹
    show_folder = f"[{show_info.original_name}]-[{show_info.name}]-{show_info.imdb_id}-{show_info.tmdb_id}"
    
    # 2. 扫描季度文件夹，批量重命名剧集
    for season_files in self._group_by_season(source_path):
        season_info = self.tmdb.get_season_info(show_info.id, season_files.season)
        season_folder = f"S{season_files.season:02d}-{season_info.air_date.year}"
        self._batch_rename_episodes(season_files.files, season_folder)
```

**剧集文件重命名（不使用AI）：**
```python
def _extract_episode_info(self, filename):
    # 使用正则表达式提取S01E01信息
    pattern = r'[sS](\d{1,2})[eE](\d{1,2})'
    match = re.search(pattern, filename)
    return (int(match.group(1)), int(match.group(2))) if match else None
```

### 第7步：元数据生成 (2天)

**电影.nfo文件：**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{title}</title>
    <originaltitle>{original_title}</originaltitle>
    <year>{year}</year>
    <plot>{overview}</plot>
    <director>{director}</director>
    <tmdbid>{tmdb_id}</tmdbid>
    <imdbid>{imdb_id}</imdbid>
</movie>
```

**TV季度.nfo文件：**
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<season>
    <seasonnumber>{season_number}</seasonnumber>
    <year>{air_date.year}</year>
    <plot>{overview}</plot>
    <poster>season-poster.jpg</poster>
</season>
```

### 第8步：海报下载 (1天)

**下载逻辑：**
```python
def download_poster(self, poster_path, output_path):
    if poster_path:
        url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        response = requests.get(url)
        with open(output_path, 'wb') as f:
            f.write(response.content)
```

### 第9步：CLI接口和异常处理 (1天)

**命令行实现：**
```python
@click.command()
@click.argument('path')
@click.option('--dry-run', is_flag=True, help='预览模式，不实际操作')
@click.option('--type', type=click.Choice(['movie', 'tv', 'auto']), default='auto')
def organize(path, dry_run, type):
    scanner = MediaScanner()
    matcher = TMDBMatcher()
    organizer = FileOrganizer()
    
    # 扫描文件
    media_files = scanner.scan_directory(path)
    unmatched_files = []
    
    # 处理每个文件
    for media_file in media_files:
        try:
            # AI解析 -> TMDB匹配 -> 文件重组
            parsed = scanner.parse_with_ai(media_file.name, media_file.type)
            tmdb_info = matcher.search(parsed.title, parsed.year, media_file.type)
            
            if tmdb_info:
                if not dry_run:
                    organizer.organize(tmdb_info, media_file.path)
                else:
                    click.echo(f"将处理: {media_file.path}")
            else:
                # TMDB无法匹配
                unmatched_files.append(media_file.path)
                
        except Exception as e:
            # AI解析失败或其他错误
            click.echo(f"处理失败: {media_file.path}, 错误: {e}")
            unmatched_files.append(media_file.path)
    
    # 处理无法匹配的文件
    if unmatched_files:
        for file_path in unmatched_files:
            if not dry_run:
                organizer.move_to_unmatched(file_path)
            else:
                click.echo(f"将移动到Unmatched: {file_path}")
    
    # 清理剩余文件
    if not dry_run:
        organizer.cleanup_unwanted(path)
    else:
        click.echo("将清理冗余文件到Unwanted文件夹")
```

**异常处理逻辑：**
```python
def move_to_unmatched(self, file_path):
    """移动无法匹配的文件到Unmatched文件夹"""
    unmatched_dir = os.path.join(os.path.dirname(file_path), "Unmatched")
    os.makedirs(unmatched_dir, exist_ok=True)
    shutil.move(file_path, os.path.join(unmatched_dir, os.path.basename(file_path)))

def cleanup_unwanted(self, source_dir):
    """清理剩余的冗余文件和文件夹到Unwanted"""
    unwanted_dir = os.path.join(source_dir, "Unwanted")
    os.makedirs(unwanted_dir, exist_ok=True)
    
    for item in os.listdir(source_dir):
        item_path = os.path.join(source_dir, item)
        # 跳过已整理的文件夹和Unmatched/Unwanted文件夹
        if item in ["Unmatched", "Unwanted"] or self._is_organized_folder(item):
            continue
            
        # 移动剩余的文件和文件夹
        shutil.move(item_path, os.path.join(unwanted_dir, item))
```

## 验收标准

### 基本功能验收
- [ ] 能正确扫描指定目录的视频文件
- [ ] AI解析准确率 > 80%
- [ ] TMDB匹配成功率 > 85%  
- [ ] 能按格式重组文件结构
- [ ] 生成正确的.nfo文件
- [ ] 下载对应的海报文件
- [ ] 支持干运行模式
- [ ] **无法匹配的文件移动到Unmatched文件夹**
- [ ] **剩余冗余文件移动到Unwanted文件夹**

### 测试用例
```python
# 电影测试
test_movies = [
    "阿凡达.Avatar.2009.1080p.BluRay.x264.mkv",
    "复仇者联盟4.Avengers.Endgame.2019.4K.HDR.mp4"
]

# TV剧集测试  
test_tv_structure = [
    "权力的游戏.Game.of.Thrones/S01/Game.of.Thrones.S01E01.1080p.mkv",
    "庆余年.Joy.of.Life/第一季/庆余年.S01E01.1080p.mp4"
]

# 异常处理测试
test_unmatched = [
    "无法解析的文件名.1080p.mkv",  # AI解析失败
    "不存在的电影.NonExistent.Movie.2025.mkv"  # TMDB无匹配
]

test_unwanted = [
    "空文件夹/",
    "README.txt",  # 非视频文件
    "旧的文件夹结构/"  # 整理后剩余的文件夹
]
```

## 风险控制

### 主要风险
1. **AI解析失败** - 自动移动到Unmatched文件夹
2. **TMDB API限流** - 添加请求频率控制  
3. **文件操作失败** - 强制使用干运行模式验证
4. **冗余文件处理** - 确保不误删重要文件，移动到Unwanted而非删除

### 错误处理
```python
def safe_process_file(file_path):
    try:
        return process_file(file_path)
    except Exception as e:
        logger.error(f"处理失败: {file_path}, 错误: {e}")
        # 移动到Unmatched文件夹而不是丢弃
        move_to_unmatched(file_path)
        return None

def process_with_fallback(media_files, organizer):
    """处理文件并处理失败情况"""
    for media_file in media_files:
        try:
            # 正常处理流程
            result = process_media_file(media_file)
            if result:
                organizer.organize(result, media_file.path)
            else:
                # TMDB无匹配，移动到Unmatched
                organizer.move_to_unmatched(media_file.path)
        except Exception as e:
            # AI解析失败或其他错误，移动到Unmatched
            logger.error(f"处理失败: {media_file.path}, 错误: {e}")
            organizer.move_to_unmatched(media_file.path)
```

## 时间安排

**总计：12天**
- 项目搭建：1天
- 核心框架：1天  
- 文件扫描：1天
- AI集成：2天
- TMDB集成：2天
- 文件重组：2天
- 元数据生成：2天
- CLI接口：1天

**里程碑：**
- 第5天：基本功能跑通
- 第10天：完整功能测试
- 第12天：验收完成
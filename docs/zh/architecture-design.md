# AI媒体管理器架构设计

## 设计理念

### 务实优于完美
- 简单 > 完美
- 可工作 > 可扩展
- 快速迭代 > 预先设计
- 解决实际问题 > 追求架构完美

### 避免过度设计
- 不预先优化
- 不过度抽象
- 不为未来需求设计
- 基于实际痛点重构

## 核心架构

### 渐进式单体架构

```
ai-media-organizer/
├── main.py              # CLI入口点
├── src/
│   ├── scanner.py       # 媒体扫描器
│   ├── matcher.py       # TMDB匹配器  
│   ├── organizer.py     # 文件组织器
│   └── utils.py         # 工具函数
├── config/
│   └── settings.yaml    # 配置文件
├── docs/zh/            # 中文文档
└── requirements.txt    # 依赖管理
```

### 三个核心类设计

#### 1. MediaScanner (媒体扫描器)
**职责：**
- 递归扫描目录，发现视频文件
- 过滤Sample文件夹和文件
- 使用本地AI解析文件名
- 分析视频技术参数

**核心方法：**
```python
class MediaScanner:
    def scan_directory(self, path: str) -> List[MediaFile]
    def parse_filename_with_ai(self, filename: str) -> ParsedInfo
    def analyze_video_properties(self, file_path: str) -> VideoInfo
    def filter_sample_files(self, files: List[str]) -> List[str]
```

#### 2. TMDBMatcher (TMDB匹配器)
**职责：**
- 连接TMDB API获取媒体信息
- 智能匹配AI解析结果与TMDB数据
- 处理中英文搜索和fallback机制
- 下载海报和元数据
- 获取TV剧集每个季度的详细信息

**核心方法：**
```python
class TMDBMatcher:
    def search_movie(self, title: str, year: int) -> MovieInfo
    def search_tv_show(self, title: str, year: int) -> TVShowInfo
    def get_season_info(self, show_id: str, season_number: int) -> SeasonInfo
    def download_poster(self, tmdb_id: str, output_path: str, poster_type: str = "movie")
    def download_season_poster(self, show_id: str, season_number: int, output_path: str)
    def get_detailed_info(self, tmdb_id: str) -> DetailedInfo
```

#### 3. FileOrganizer (文件组织器)
**职责：**
- 根据模板生成新的文件夹结构
- 执行文件移动和重命名操作
- 生成KODI兼容的.nfo文件
- 支持干运行模式和回滚
- 处理TV剧集的季度级别文件组织

**核心方法：**
```python
class FileOrganizer:
    def organize_movie(self, movie_info: MovieInfo, source_path: str)
    def organize_tv_show(self, show_info: TVShowInfo, source_path: str)
    def organize_tv_season(self, season_info: SeasonInfo, source_files: List[str])
    def batch_rename_episodes(self, episode_files: List[str], season_info: SeasonInfo)
    def generate_nfo_file(self, media_info: MediaInfo, output_path: str)
    def generate_season_nfo(self, season_info: SeasonInfo, output_path: str)
    def execute_dry_run(self, operations: List[FileOperation])
```

## AI解析策略

### 纯AI解析方案
**决策依据：**
- 正则表达式无法处理复杂多变的文件名
- AI模型能理解中英文混合命名
- 避免维护大量规则的复杂度
- 随着AI模型改进自动提升准确率

### 本地AI集成
**技术实现：**
- 通过HTTP API调用本地AI服务
- 设计专门的prompt模板
- 支持批量请求优化性能
- 错误重试和降级机制

### Prompt设计原则

#### 电影文件名解析
```python
movie_prompt_template = """
分析以下视频文件名，提取电影信息：
文件名: {filename}

请返回JSON格式：
{{
    "type": "movie",
    "title": "中文标题",
    "original_title": "英文标题", 
    "year": 年份,
    "confidence": 0.0-1.0
}}
"""
```

#### TV剧集文件夹解析
```python
tv_show_prompt_template = """
分析以下文件夹名，提取TV剧集信息：
文件夹名: {folder_name}

请返回JSON格式：
{{
    "type": "tv_show",
    "title": "中文标题",
    "original_title": "英文标题", 
    "year": 年份,
    "confidence": 0.0-1.0
}}

注意：这是剧集的总体信息，不是单集信息。
"""
```

#### 剧集文件批量重命名
```python
# 不使用AI，直接基于正则表达式提取季集信息
episode_pattern = r'[sS](\d{1,2})[eE](\d{1,2})'
season_pattern = r'[sS](\d{1,2})'
```

## 文件命名规范

### 电影格式
```
文件夹: [${originalTitle}]-[${title}](${edition})-${year}-${imdb}-${tmdb}
文件名: [${originalTitle}]-[${title}](${edition})-${year}-${videoResolution}-${videoFormat}-${videoCodec}-${videoBitDepth}bit-${audioCodec}-${audioChannels}
```

### TV剧集格式
```
剧集文件夹: [${showOriginalTitle}]-[${showTitle}]-${showImdb}-${showTmdb}
季文件夹: S${seasonNr2}-${showYear}
剧集文件: [${showOriginalTitle}]-S${seasonNr2}E${episodeNr2}-[${originalTitle}]-[${title}]-${videoFormat}-${videoCodec}-${videoBitDepth}bit-${audioCodec}-${audioChannels}
```

### TV剧集处理策略
**分层处理逻辑：**
1. **剧集级别解析**: 使用AI解析顶层文件夹名，获取剧集基本信息
2. **季度信息获取**: 从TMDB获取每个季度的详细信息和年份
3. **剧集文件批量重命名**: 不使用AI，直接基于文件名模式重命名

**季度元数据管理：**
- 每个季度文件夹包含该季度专属的海报
- 生成季度级别的.nfo文件
- 包含该季度的演员表、剧情简介等信息

## 配置管理

### 安全配置原则
- 敏感信息通过环境变量传递
- 配置文件不包含明文密钥
- 支持多环境配置

### 配置结构
```yaml
# settings.yaml
api:
  tmdb_base_url: "https://api.themoviedb.org/3"
  local_ai_url: "http://localhost:8080"
  timeout: 30

processing:
  batch_size: 10
  max_retries: 3
  dry_run: false

paths:
  temp_dir: "./temp"
  log_dir: "./logs"
```

## 错误处理策略

### 简单但有效的错误处理
```python
# 文件级别错误处理
try:
    result = process_file(file)
    log_success(result)
except Exception as e:
    log_error(file, e)
    continue  # 继续处理下一个文件

# 批量处理错误汇总
errors = []
for file in files:
    try:
        process_file(file)
    except Exception as e:
        errors.append((file, e))

if errors:
    generate_error_report(errors)
```

### 日志管理
- 使用标准logging模块
- 分级别记录（INFO, WARNING, ERROR）
- 支持文件和控制台输出
- 错误文件单独记录便于排查

## 性能考虑

### 优化策略
1. **并发处理**: 文件扫描和AI解析支持并发
2. **缓存机制**: TMDB API结果本地缓存
3. **批量操作**: 文件操作尽量批量执行
4. **内存管理**: 大文件分批处理，避免内存溢出

### 性能监控
- 记录处理时间
- 监控API调用频率
- 统计成功率和错误率

## 扩展性设计

### 插件化考虑
虽然初期采用单体架构，但保留扩展接口：
- 解析器接口（未来支持多种AI模型）
- 元数据源接口（未来支持多个数据源）
- 文件操作接口（未来支持云存储）

### 未来重构方向
基于实际使用痛点：
- 如果AI解析成为瓶颈 → 独立AI服务模块
- 如果API限流频繁 → 独立缓存和队列管理
- 如果文件操作出错多 → 独立事务管理模块

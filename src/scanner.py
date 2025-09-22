"""
Media file scanner and AI parser
"""

import os
import logging
import json
import requests
import re
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from .models import MediaFile, MediaType, ParsedInfo

logger = logging.getLogger(__name__)

class MediaScanner:
    """Scans directories for media files and parses them using AI"""
    
    def __init__(self, config: dict):
        self.config = config
        self.video_extensions = config['video']['extensions']
        self.sample_patterns = config['video']['sample_patterns']
        self.local_ai_url = config['api']['local_ai_url']
        self.timeout = config['api']['timeout']
        
        # Create logs directory if needed
        os.makedirs('logs', exist_ok=True)
        
        # Initialize scan session data
        self.scan_session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "scan_results": [],
            "summary": {
                "total_files": 0,
                "successful_parses": 0,
                "failed_parses": 0,
                "movies": 0,
                "tv_shows": 0
            }
        }
    
    def scan_directory(self, path: str) -> List[MediaFile]:
        """Scan directory for media files, excluding already organized content"""
        logger.info(f"Scanning directory: {path}")
        media_files = []
        
        for root, dirs, files in os.walk(path):
            # Filter out sample directories
            dirs[:] = [d for d in dirs if not self._is_sample_directory(d)]
            
            # Skip already organized folders (check if folder follows our naming pattern)
            if self._is_organized_folder(os.path.basename(root)):
                logger.info(f"Skipping already organized folder: {root}")
                dirs.clear()  # Don't recurse into organized folders
                continue
            
            for file in files:
                if self._is_video_file(file) and not self._is_sample_file(file):
                    file_path = os.path.join(root, file)
                    media_type = self._detect_media_type(file_path)
                    media_files.append(MediaFile(
                        path=file_path,
                        name=file,
                        media_type=media_type
                    ))
        
        logger.info(f"Found {len(media_files)} media files")
        return media_files
    
    def parse_with_ai(self, name: str, media_type: MediaType, folder_context: str = None) -> Optional[ParsedInfo]:
        """Parse filename/folder name using local AI"""
        timestamp = datetime.now().isoformat()
        
        try:
            if media_type == MediaType.MOVIE:
                prompt = self._get_movie_prompt(name, folder_context)
            else:
                prompt = self._get_tv_show_prompt(name, folder_context)
            
            logger.info(f"Starting AI parsing for: {name} (type: {media_type.value})")
            
            response = self._call_local_ai(prompt)
            
            # Prepare scan result data (simplified)
            scan_result = {
                "filename": name,
                "media_type": media_type.value,
                "folder_context": folder_context,
                "parsed_result": None
            }
            
            if response:
                parsed_result = self._parse_ai_response(response, media_type)
                if parsed_result:
                    scan_result["parsed_result"] = {
                        "chinese_title": parsed_result.title,
                        "english_title": parsed_result.original_title,
                        "year": parsed_result.year,
                        "confidence": parsed_result.confidence
                    }
                else:
                    scan_result["parsed_result"] = "parsing_failed"
                
                # Update session summary
                if parsed_result:
                    self.scan_session["summary"]["successful_parses"] += 1
                    if media_type == MediaType.MOVIE:
                        self.scan_session["summary"]["movies"] += 1
                    else:
                        self.scan_session["summary"]["tv_shows"] += 1
                    logger.info(f"AI parsing successful for {name}: {parsed_result.title} ({parsed_result.year})")
                else:
                    self.scan_session["summary"]["failed_parses"] += 1
                    logger.warning(f"AI response parsing failed for {name}")
                
                # Add to session results
                self.scan_session["scan_results"].append(scan_result)
                return parsed_result
            else:
                logger.error(f"AI API call failed for {name}")
                self.scan_session["summary"]["failed_parses"] += 1
                scan_result["parsed_result"] = "ai_api_failed"
                self.scan_session["scan_results"].append(scan_result)
            
        except Exception as e:
            logger.error(f"AI parsing failed for {name}: {e}")
            self.scan_session["summary"]["failed_parses"] += 1
            scan_result = {
                "filename": name,
                "media_type": media_type.value,
                "folder_context": folder_context,
                "parsed_result": f"error: {str(e)}"
            }
            self.scan_session["scan_results"].append(scan_result)
        
        return None
    
    
    def _is_video_file(self, filename: str) -> bool:
        """Check if file is a video file"""
        return any(filename.lower().endswith(ext) for ext in self.video_extensions)
    
    def _is_sample_file(self, filename: str) -> bool:
        """Check if file is a sample file"""
        return any(pattern in filename for pattern in self.sample_patterns)
    
    def _is_sample_directory(self, dirname: str) -> bool:
        """Check if directory is a sample directory"""
        return any(pattern in dirname for pattern in self.sample_patterns)
    
    def _detect_media_type(self, file_path: str) -> MediaType:
        """Detect if file is movie or TV show based on path structure"""
        # Simple heuristic: if path contains season/episode patterns, it's TV
        path_str = str(file_path).lower()
        if re.search(r's\d{1,2}e\d{1,2}|season|episode', path_str):
            return MediaType.TV_SHOW
        return MediaType.MOVIE
    
    def _get_movie_prompt(self, filename: str, folder_context: str = None) -> str:
        """Generate AI prompt for movie parsing"""
        if folder_context:
            # Enhanced prompt with folder context
            return f"""分析以下电影文件信息，提取电影信息：
文件名: {filename}
文件夹: {folder_context}

请综合文件名和文件夹信息进行分析。文件夹名称通常包含更完整的电影信息。

请返回JSON格式：
{{
    "type": "movie",
    "title": "中文标题",
    "original_title": "英文标题", 
    "year": 年份,
    "confidence": 0.0-1.0
}}

解析说明：
- 优先从文件夹名提取完整信息
- 文件名如"Kill.Command.2016"应识别为"Kill Command"(英文) + 2016年
- 文件名如"aaf-ninja.1080p"结合文件夹"Ninja.2009"应识别为"Ninja"(英文) + 2009年
- 文件名如"Warfare.2025"结合文件夹"Z_战争.2025"应识别为"战争"(中文) + "Warfare"(英文) + 2025年
- 如果无法确定某个字段，请设为null。confidence表示解析的置信度。"""
        else:
            return self.config['prompts']['movie'].format(filename=filename)
    
    def _get_tv_show_prompt(self, folder_name: str, parent_context: str = None) -> str:
        """Generate AI prompt for TV show parsing"""
        if parent_context:
            return f"""分析以下TV剧集文件夹信息，提取剧集信息：
文件夹名: {folder_name}
上级文件夹: {parent_context}

请综合所有可用信息进行分析。

请返回JSON格式：
{{
    "type": "tv_show",
    "title": "中文标题",
    "original_title": "英文标题", 
    "year": 年份,
    "confidence": 0.0-1.0
}}

重要说明：
- title: 中文标题（如：权力的游戏、庆余年等中文名称）
- original_title: 英文标题（如：Game of Thrones、Avatar等英文名称）  
- 文件夹名可能包含中英文混合，请准确区分
- 这是剧集的总体信息，不是单集信息
- 如果无法确定某个字段，请设为null"""
        else:
            return self.config['prompts']['tv_show'].format(filename=folder_name)
    
    def _call_local_ai(self, prompt: str) -> Optional[str]:
        """Call local AI API (Ollama)"""
        try:
            # Use Ollama API directly
            payload = {
                "model": "qwen2.5:7b", 
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(
                f"{self.local_ai_url.replace(':8080', ':11434')}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json().get("response")
            logger.debug(f"AI API response received, length: {len(result) if result else 0}")
            return result
        except Exception as e:
            logger.error(f"Local AI API call failed: {e}")
            return None
    
    def _parse_ai_response(self, response: str, media_type: MediaType) -> Optional[ParsedInfo]:
        """Parse AI response into ParsedInfo"""
        try:
            # Extract JSON from markdown code block if present
            json_text = self._extract_json_from_response(response)
            if not json_text:
                logger.error("No JSON found in AI response")
                return None
            
            data = json.loads(json_text)
            return ParsedInfo(
                title=data.get("title"),
                original_title=data.get("original_title"),
                year=data.get("year"),
                media_type=media_type,
                confidence=data.get("confidence", 0.0),
                season=data.get("season"),
                episode=data.get("episode")
            )
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"Raw AI response that failed to parse: {response[:200]}...")
            return None
    
    def _extract_json_from_response(self, response: str) -> Optional[str]:
        """Extract JSON content from AI response, handling markdown code blocks"""
        try:
            # First, try to parse as direct JSON
            json.loads(response)
            return response
        except:
            pass
        
        # Look for JSON in markdown code blocks
        import re
        
        # Pattern to match ```json ... ``` blocks
        json_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_pattern, response, re.DOTALL | re.IGNORECASE)
        
        if matches:
            # Return the first JSON block found
            json_text = matches[0].strip()
            logger.debug(f"Extracted JSON from markdown: {json_text[:100]}...")
            return json_text
        
        # Look for JSON-like content between { and }
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, response, re.DOTALL)
        
        if matches:
            # Try to parse each match as JSON
            for match in matches:
                try:
                    json.loads(match)
                    logger.debug(f"Found valid JSON in braces: {match[:100]}...")
                    return match
                except:
                    continue
        
        logger.warning("No valid JSON found in AI response")
        return None
    
    def save_scan_session(self) -> None:
        """Save complete scan session to JSON file for debugging"""
        try:
            # Update total files count
            self.scan_session["summary"]["total_files"] = len(self.scan_session["scan_results"])
            
            filename = f"logs/scan_session_{self.scan_session['session_id']}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.scan_session, f, ensure_ascii=False, indent=2)
            logger.info(f"Scan session saved to {filename}")
            logger.info(f"Session summary: {self.scan_session['summary']}")
        except Exception as e:
            logger.error(f"Failed to save scan session JSON: {e}")
    
    def _is_organized_folder(self, folder_name: str) -> bool:
        """Check if folder follows our organized naming pattern"""
        import re
        patterns = [
            r'^\[.*\]-\[.*\]-\d{4}-(tt\d+|unknown)-\d+$',    # Full movie pattern with IMDB
            r'^\[.*\]-\d{4}-(tt\d+|unknown)-\d+$',           # Single title movie pattern
            r'^\[.*\]-\[.*\]-(tt\d+|unknown)-\d+$',          # TV show pattern
        ]
        return any(re.match(pattern, folder_name) for pattern in patterns)

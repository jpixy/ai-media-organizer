"""
File organizer for movies and TV shows
"""

import os
import shutil
import logging
import re
from typing import List, Optional
from pathlib import Path

from .models import MovieInfo, TVShowInfo, SeasonInfo, FileOperation, MediaFile

logger = logging.getLogger(__name__)

class FileOrganizer:
    """Organizes media files according to naming conventions"""
    
    def __init__(self, config: dict):
        self.config = config
        self.dry_run = config['processing']['dry_run']
        self.operations: List[FileOperation] = []
    
    def organize_movie(self, movie_info: MovieInfo, source_path: str, root_dir: str, ai_parsed_info=None) -> bool:
        """Organize movie file"""
        try:
            # Generate folder name
            folder_name = self._generate_movie_folder_name(movie_info, ai_parsed_info)
            # Always place organized folders in the root scan directory
            dest_dir = os.path.join(root_dir, folder_name)
            
            # Generate file name (need video info for full name)
            file_name = self._generate_movie_file_name(movie_info, source_path, ai_parsed_info)
            dest_path = os.path.join(dest_dir, file_name)
            
            # Add operation
            operation = FileOperation(
                operation_type="move",
                source=source_path,
                destination=dest_path,
                description=f"Organize movie: {movie_info.title}"
            )
            
            if self.dry_run:
                self.operations.append(operation)
                logger.info(f"DRY RUN: Would move {source_path} -> {dest_path}")
                # Also check for related files in dry run
                related_files = self._find_related_files(source_path)
                for related_file in related_files:
                    related_dest = os.path.join(dest_dir, os.path.basename(related_file))
                    related_op = FileOperation(
                        operation_type="move",
                        source=related_file,
                        destination=related_dest,
                        description=f"Move related file: {os.path.basename(related_file)}"
                    )
                    self.operations.append(related_op)
                    logger.info(f"DRY RUN: Would move related file {related_file} -> {related_dest}")
            else:
                # Move the video file first
                self._execute_move(operation)
                # Move related files
                self._move_related_files(source_path, dest_dir)
                
                # Generate NFO and poster files with simplified naming (only if they don't exist)
                nfo_path = os.path.join(dest_dir, 'media_info.nfo')
                if not os.path.exists(nfo_path):
                    self.generate_nfo(movie_info, nfo_path)
                else:
                    logger.info(f"NFO file already exists: {nfo_path}")
                
                # Download poster (only if it doesn't exist)
                if movie_info.poster_path:
                    poster_path = os.path.join(dest_dir, 'poster.jpg')
                    if not os.path.exists(poster_path):
                        self._download_poster(movie_info.poster_path, poster_path)
                    else:
                        logger.info(f"Poster file already exists: {poster_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to organize movie {source_path}: {e}")
            return False
    
    def organize_tv_show(self, show_info: TVShowInfo, source_path: str, root_dir: str) -> bool:
        """Organize TV show files"""
        try:
            # Generate show folder name
            show_folder = self._generate_tv_folder_name(show_info)
            # Always place organized folders in the root scan directory
            show_dir = os.path.join(root_dir, show_folder)
            
            # Group files by season
            season_files = self._group_files_by_season(source_path)
            
            for season_num, files in season_files.items():
                # TODO: Get season info from TMDB
                season_year = 2020  # Placeholder
                season_folder = f"S{season_num:02d}-{season_year}"
                season_dir = os.path.join(show_dir, season_folder)
                
                # Batch rename episodes
                self._batch_rename_episodes(files, season_dir, show_info, season_num)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to organize TV show {source_path}: {e}")
            return False
    
    def move_to_unmatched(self, file_path: str) -> bool:
        """Move unmatched file to Unmatched folder"""
        try:
            unmatched_dir = os.path.join(os.path.dirname(file_path), "Unmatched")
            dest_path = os.path.join(unmatched_dir, os.path.basename(file_path))
            
            operation = FileOperation(
                operation_type="move",
                source=file_path,
                destination=dest_path,
                description="Move to Unmatched folder"
            )
            
            if self.dry_run:
                self.operations.append(operation)
                logger.info(f"DRY RUN: Would move to Unmatched: {file_path}")
            else:
                os.makedirs(unmatched_dir, exist_ok=True)
                self._execute_move(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to move to Unmatched {file_path}: {e}")
            return False
    
    def cleanup_unwanted(self, source_dir: str) -> bool:
        """Clean up remaining files to Unwanted folder"""
        try:
            unwanted_dir = os.path.join(source_dir, "Unwanted")
            
            for item in os.listdir(source_dir):
                if item in ["Unmatched", "Unwanted"]:
                    continue
                
                item_path = os.path.join(source_dir, item)
                
                # Skip organized folders (check naming pattern)
                if self._is_organized_folder(item):
                    continue
                
                dest_path = os.path.join(unwanted_dir, item)
                operation = FileOperation(
                    operation_type="move",
                    source=item_path,
                    destination=dest_path,
                    description="Move to Unwanted folder"
                )
                
                if self.dry_run:
                    self.operations.append(operation)
                    logger.info(f"DRY RUN: Would move to Unwanted: {item_path}")
                else:
                    os.makedirs(unwanted_dir, exist_ok=True)
                    self._execute_move(operation)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup unwanted files: {e}")
            return False
    
    def generate_nfo(self, movie_info: MovieInfo, output_path: str) -> bool:
        """Generate KODI-compatible NFO file"""
        try:
            nfo_content = self._generate_movie_nfo_content(movie_info)
            
            if self.dry_run:
                logger.info(f"DRY RUN: Would generate NFO: {output_path}")
                return True
            else:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(nfo_content)
                logger.info(f"Generated NFO file: {output_path}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to generate NFO file {output_path}: {e}")
            return False
    
    def _generate_movie_nfo_content(self, movie_info: MovieInfo) -> str:
        """Generate KODI-compatible movie NFO content"""
        # Get additional details from TMDB
        additional_info = self._get_additional_movie_info(movie_info.id)
        
        nfo_lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>', '<movie>']
        
        # Basic information
        nfo_lines.append(f'  <title>{self._escape_xml(movie_info.title or "")}</title>')
        nfo_lines.append(f'  <originaltitle>{self._escape_xml(movie_info.original_title or "")}</originaltitle>')
        nfo_lines.append(f'  <year>{movie_info.year or ""}</year>')
        
        # Plot/Overview
        if movie_info.overview:
            nfo_lines.append(f'  <plot>{self._escape_xml(movie_info.overview)}</plot>')
            nfo_lines.append(f'  <outline>{self._escape_xml(movie_info.overview[:200] + "..." if len(movie_info.overview) > 200 else movie_info.overview)}</outline>')
        
        # IDs
        if movie_info.imdb_id:
            nfo_lines.append(f'  <id>{movie_info.imdb_id}</id>')
            nfo_lines.append(f'  <imdb>{movie_info.imdb_id}</imdb>')
        if movie_info.tmdb_id:
            nfo_lines.append(f'  <tmdbid>{movie_info.tmdb_id}</tmdbid>')
        
        # Additional info from TMDB
        if additional_info:
            # Runtime
            if additional_info.get('runtime'):
                nfo_lines.append(f'  <runtime>{additional_info["runtime"]}</runtime>')
            
            # Rating
            if additional_info.get('vote_average'):
                nfo_lines.append(f'  <rating>{additional_info["vote_average"]}</rating>')
                nfo_lines.append(f'  <votes>{additional_info.get("vote_count", 0)}</votes>')
            
            # Release date
            if additional_info.get('release_date'):
                nfo_lines.append(f'  <premiered>{additional_info["release_date"]}</premiered>')
                nfo_lines.append(f'  <releasedate>{additional_info["release_date"]}</releasedate>')
            
            # Genres
            if additional_info.get('genres'):
                for genre in additional_info['genres']:
                    nfo_lines.append(f'  <genre>{self._escape_xml(genre["name"])}</genre>')
            
            # Production companies
            if additional_info.get('production_companies'):
                for company in additional_info['production_companies']:
                    nfo_lines.append(f'  <studio>{self._escape_xml(company["name"])}</studio>')
            
            # Production countries
            if additional_info.get('production_countries'):
                countries = [country['name'] for country in additional_info['production_countries']]
                nfo_lines.append(f'  <country>{self._escape_xml(", ".join(countries))}</country>')
            
            # Cast and crew
            credits = self._get_movie_credits(movie_info.id)
            if credits:
                # Director
                directors = [person for person in credits.get('crew', []) if person['job'] == 'Director']
                for director in directors:
                    nfo_lines.append(f'  <director>{self._escape_xml(director["name"])}</director>')
                
                # Cast
                for actor in credits.get('cast', [])[:20]:  # Limit to top 20 actors
                    nfo_lines.append('  <actor>')
                    nfo_lines.append(f'    <name>{self._escape_xml(actor["name"])}</name>')
                    nfo_lines.append(f'    <role>{self._escape_xml(actor.get("character", ""))}</role>')
                    if actor.get('profile_path'):
                        nfo_lines.append(f'    <thumb>https://image.tmdb.org/t/p/w500{actor["profile_path"]}</thumb>')
                    nfo_lines.append('  </actor>')
        
        # Poster
        if movie_info.poster_path:
            nfo_lines.append(f'  <thumb>https://image.tmdb.org/t/p/w500{movie_info.poster_path}</thumb>')
            nfo_lines.append(f'  <fanart>')
            nfo_lines.append(f'    <thumb>https://image.tmdb.org/t/p/original{movie_info.poster_path}</thumb>')
            nfo_lines.append(f'  </fanart>')
        
        nfo_lines.append('</movie>')
        return '\n'.join(nfo_lines)
    
    def _escape_xml(self, text: str) -> str:
        """Escape XML special characters"""
        if not text:
            return ""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
    
    def _get_additional_movie_info(self, tmdb_id: int) -> Optional[dict]:
        """Get additional movie information from TMDB"""
        try:
            import requests
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            params = {"api_key": os.getenv('TMDB_API_KEY')}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.warning(f"Failed to get additional movie info: {e}")
            return None
    
    def _get_movie_credits(self, tmdb_id: int) -> Optional[dict]:
        """Get movie credits (cast and crew) from TMDB"""
        try:
            import requests
            url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/credits"
            params = {"api_key": os.getenv('TMDB_API_KEY')}
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.warning(f"Failed to get movie credits: {e}")
            return None
    
    def _download_poster(self, poster_path: str, output_path: str) -> bool:
        """Download movie poster from TMDB"""
        try:
            if self.dry_run:
                logger.info(f"DRY RUN: Would download poster: {output_path}")
                return True
            
            import requests
            # Use high quality poster
            poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            
            response = requests.get(poster_url, timeout=30)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded poster: {output_path}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to download poster {poster_path}: {e}")
            return False
    
    def get_operations(self) -> List[FileOperation]:
        """Get list of operations for dry run"""
        return self.operations
    
    def _generate_movie_folder_name(self, movie_info: MovieInfo, ai_parsed_info=None) -> str:
        """Generate movie folder name with proper Chinese/English title handling"""
        # Format: [original_title]-[translated_title]-year-imdb-tmdb
        
        original_title = movie_info.original_title or ""
        tmdb_title = movie_info.title or ""
        
        # Determine what should be in the second position based on original title language
        second_title = ""
        
        if self._is_chinese_text(original_title):
            # Original is Chinese, need English title in second position
            # Try to find English title from TMDB data
            if tmdb_title and not self._is_chinese_text(tmdb_title):
                second_title = tmdb_title
            # Could also check AI parsed info for English title
            elif ai_parsed_info and ai_parsed_info.original_title and not self._is_chinese_text(ai_parsed_info.original_title):
                second_title = ai_parsed_info.original_title
        else:
            # Original is English/other language, need Chinese title in second position
            # Try AI parsed Chinese title first
            if ai_parsed_info and ai_parsed_info.title and self._is_chinese_text(ai_parsed_info.title):
                second_title = ai_parsed_info.title
            # If no Chinese from AI, check TMDB title
            elif tmdb_title and tmdb_title != original_title and self._is_chinese_text(tmdb_title):
                second_title = tmdb_title
        
        # Generate folder name
        if second_title:
            return f"[{original_title}]-[{second_title}]-{movie_info.year}-{movie_info.imdb_id or 'unknown'}-{movie_info.tmdb_id}"
        else:
            # No appropriate second title found, just use original title
            return f"[{original_title}]-{movie_info.year}-{movie_info.imdb_id or 'unknown'}-{movie_info.tmdb_id}"
    
    def _is_chinese_text(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        if not text:
            return False
        # Check for Chinese Unicode ranges
        for char in text:
            if '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
                return True
        return False
    
    def _generate_movie_file_name(self, movie_info: MovieInfo, source_path: str, ai_parsed_info=None) -> str:
        """Generate movie file name with video info extracted from original filename"""
        ext = os.path.splitext(source_path)[1]
        original_filename = os.path.basename(source_path)
        base_name = self._generate_movie_folder_name(movie_info, ai_parsed_info)
        
        # Extract video info from original filename
        video_info = self._extract_video_info_from_filename(original_filename)
        
        # Generate unique filename with extracted info
        return f"{base_name}-{video_info}{ext}"
    
    def _extract_video_info_from_filename(self, filename: str) -> str:
        """Extract video quality, format, codec info from filename"""
        import re
        
        # Common patterns for video info
        resolution_patterns = [
            r'(\d{3,4}p)',  # 720p, 1080p, 2160p, 4K
            r'(4K)',
            r'(HD)',
            r'(UHD)',
            r'(2160p)',
            r'(1440p)',
            r'(1080p)',
            r'(720p)',
            r'(480p)'
        ]
        
        format_patterns = [
            r'(BluRay|Blu-ray|BD)',
            r'(WEB-DL|WEBDL|WEB)',
            r'(DVDRip|DVD)',
            r'(BRRip|BDRip)',
            r'(HDRip)',
            r'(CAM|TS|TC)'
        ]
        
        codec_patterns = [
            r'(x264|x265|h264|h265|HEVC|AVC)',
            r'(DivX|XviD)',
            r'(VP9|AV1)'
        ]
        
        audio_patterns = [
            r'(DTS|AC3|AAC|MP3|FLAC|DD5\.1|DDP5\.1)',
            r'(5\.1|7\.1|2\.0)',
            r'(Atmos)'
        ]
        
        # Extract information
        resolution = self._extract_first_match(filename, resolution_patterns) or "1080p"
        format_info = self._extract_first_match(filename, format_patterns) or "WEB-DL"
        codec = self._extract_first_match(filename, codec_patterns) or "x264"
        audio = self._extract_first_match(filename, audio_patterns) or "AAC"
        
        # Handle special cases
        if '4K' in filename.upper() or '2160p' in filename:
            resolution = "2160p"
        
        # Determine bit depth
        bit_depth = "10bit" if any(x in filename for x in ["10bit", "10-bit", "x265", "HEVC"]) else "8bit"
        
        # Generate video info string
        return f"{resolution}-{format_info}-{codec}-{bit_depth}-{audio}"
    
    def _extract_first_match(self, text: str, patterns: list) -> str:
        """Extract first matching pattern from text"""
        import re
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _get_resolution_priority(self, resolution: str) -> int:
        """Get resolution priority for comparison (higher number = higher resolution)"""
        resolution_map = {
            '480p': 1,
            '720p': 2,
            'HD': 2,
            '1080p': 3,
            '1080P': 3,
            '1440p': 4,
            '2160p': 5,
            '4K': 5,
            'UHD': 5
        }
        return resolution_map.get(resolution, 0)
    
    def _remove_old_metadata_files(self, dest_dir: str):
        """Remove old NFO and poster files with simplified naming"""
        import os
        
        try:
            # Remove standard NFO file
            nfo_file = os.path.join(dest_dir, 'media_info.nfo')
            if os.path.exists(nfo_file):
                os.remove(nfo_file)
                logger.info(f"Removed old NFO file: {nfo_file}")
            
            # Remove standard poster file
            poster_file = os.path.join(dest_dir, 'poster.jpg')
            if os.path.exists(poster_file):
                os.remove(poster_file)
                logger.info(f"Removed old poster file: {poster_file}")
                
        except Exception as e:
            logger.warning(f"Failed to remove old metadata files: {e}")
    
    def _generate_tv_folder_name(self, show_info: TVShowInfo) -> str:
        """Generate TV show folder name"""
        if show_info.original_name == show_info.name:
            return f"[{show_info.name}]-{show_info.imdb_id or 'unknown'}-{show_info.tmdb_id}"
        else:
            return f"[{show_info.original_name}]-[{show_info.name}]-{show_info.imdb_id or 'unknown'}-{show_info.tmdb_id}"
    
    def _group_files_by_season(self, source_path: str) -> dict:
        """Group episode files by season number"""
        # TODO: Implement season grouping logic
        # For now, return a simple example
        return {1: [source_path]}
    
    def _batch_rename_episodes(self, files: List[str], season_dir: str, show_info: TVShowInfo, season_num: int):
        """Batch rename episode files"""
        for file_path in files:
            # Extract episode info from filename
            episode_info = self._extract_episode_info(os.path.basename(file_path))
            if episode_info:
                episode_num = episode_info[1]
                
                # Generate episode file name
                ext = os.path.splitext(file_path)[1]
                episode_name = f"[{show_info.original_name}]-S{season_num:02d}E{episode_num:02d}-[{show_info.original_name}]-[{show_info.name}]-x264-8bit-AAC-5.1{ext}"
                
                dest_path = os.path.join(season_dir, episode_name)
                operation = FileOperation(
                    operation_type="move",
                    source=file_path,
                    destination=dest_path,
                    description=f"Rename episode S{season_num:02d}E{episode_num:02d}"
                )
                
                if self.dry_run:
                    self.operations.append(operation)
                else:
                    os.makedirs(season_dir, exist_ok=True)
                    self._execute_move(operation)
    
    def _extract_episode_info(self, filename: str) -> Optional[tuple]:
        """Extract season and episode info from filename"""
        pattern = r'[sS](\d{1,2})[eE](\d{1,2})'
        match = re.search(pattern, filename)
        return (int(match.group(1)), int(match.group(2))) if match else None
    
    def _is_organized_folder(self, folder_name: str) -> bool:
        """Check if folder follows organized naming pattern"""
        # Check for organized movie/TV patterns - be more comprehensive
        patterns = [
            r'^\[.*\]-\[.*\]-\d{4}-(tt\d+|unknown)-\d+$',    # Full movie pattern with IMDB
            r'^\[.*\]-\d{4}-(tt\d+|unknown)-\d+$',           # Single title movie pattern
            r'^\[.*\]-\[.*\]-(tt\d+|unknown)-\d+$',          # TV show pattern
        ]
        return any(re.match(pattern, folder_name) for pattern in patterns)
    
    def _find_related_files(self, video_path: str) -> List[str]:
        """Find related files (subtitles, etc.) for a video file"""
        related_files = []
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # Get subtitle extensions from config
        subtitle_exts = self.config.get('subtitle', {}).get('extensions', [])
        subtitle_folders = self.config.get('subtitle', {}).get('folder_names', [])
        
        # 1. Look for subtitle files with same name
        for ext in subtitle_exts:
            subtitle_file = os.path.join(video_dir, f"{video_name}{ext}")
            if os.path.exists(subtitle_file):
                related_files.append(subtitle_file)
        
        # 2. Look for subtitle folders
        for folder_name in subtitle_folders:
            subtitle_dir = os.path.join(video_dir, folder_name)
            if os.path.isdir(subtitle_dir):
                # Add all files in subtitle folder
                for file in os.listdir(subtitle_dir):
                    file_path = os.path.join(subtitle_dir, file)
                    if os.path.isfile(file_path):
                        related_files.append(file_path)
        
        # 3. Look for other subtitle files in same directory
        if os.path.isdir(video_dir):
            for file in os.listdir(video_dir):
                file_path = os.path.join(video_dir, file)
                if os.path.isfile(file_path):
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in subtitle_exts:
                        # Check if subtitle file name is related to video name
                        if self._is_related_subtitle(video_name, os.path.splitext(file)[0]):
                            if file_path not in related_files:  # Avoid duplicates
                                related_files.append(file_path)
        
        return related_files
    
    def _is_related_subtitle(self, video_name: str, subtitle_name: str) -> bool:
        """Check if subtitle file is related to video file"""
        video_name_clean = self._clean_filename(video_name.lower())
        subtitle_name_clean = self._clean_filename(subtitle_name.lower())
        
        # Simple heuristic: if subtitle name contains main part of video name
        return (video_name_clean in subtitle_name_clean or 
                subtitle_name_clean in video_name_clean or
                len(set(video_name_clean.split()) & set(subtitle_name_clean.split())) >= 2)
    
    def _clean_filename(self, filename: str) -> str:
        """Clean filename for comparison"""
        # Remove common video quality indicators and separators
        filename = re.sub(r'\b(1080p|720p|480p|4k|2160p|bluray|webrip|hdtv|x264|x265|h264|h265)\b', '', filename, flags=re.IGNORECASE)
        filename = re.sub(r'[.\-_\[\]()]', ' ', filename)
        return ' '.join(filename.split())
    
    def _move_related_files(self, video_path: str, dest_dir: str):
        """Move related files to destination directory"""
        related_files = self._find_related_files(video_path)
        
        for related_file in related_files:
            try:
                # Determine destination path
                if os.path.basename(os.path.dirname(related_file)) in self.config.get('subtitle', {}).get('folder_names', []):
                    # If file is in a subtitle folder, maintain folder structure
                    subtitle_dir = os.path.join(dest_dir, os.path.basename(os.path.dirname(related_file)))
                    os.makedirs(subtitle_dir, exist_ok=True)
                    dest_path = os.path.join(subtitle_dir, os.path.basename(related_file))
                else:
                    # Direct file, move to destination directory
                    dest_path = os.path.join(dest_dir, os.path.basename(related_file))
                
                # Execute move
                shutil.move(related_file, dest_path)
                logger.info(f"Moved related file: {related_file} -> {dest_path}")
                
            except Exception as e:
                logger.warning(f"Failed to move related file {related_file}: {e}")
    
    def _execute_move(self, operation: FileOperation) -> bool:
        """Execute file move operation, handling file conflicts"""
        try:
            dest_dir = os.path.dirname(operation.destination)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Check if destination already exists
            final_destination = operation.destination
            if os.path.exists(final_destination):
                # Generate unique filename by adding counter
                base_name, ext = os.path.splitext(final_destination)
                counter = 1
                while os.path.exists(final_destination):
                    final_destination = f"{base_name}-{counter:02d}{ext}"
                    counter += 1
                logger.info(f"Destination exists, using: {final_destination}")
            
            shutil.move(operation.source, final_destination)
            logger.info(f"Moved: {operation.source} -> {final_destination}")
            return True
        except Exception as e:
            logger.error(f"Move failed: {e}")
            return False

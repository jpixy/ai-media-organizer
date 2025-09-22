"""
TMDB API matcher for movie and TV show information
"""

import logging
import requests
import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import MovieInfo, TVShowInfo, SeasonInfo

logger = logging.getLogger(__name__)

class TMDBMatcher:
    """TMDB API client for matching and retrieving media information"""
    
    def __init__(self, config: dict):
        self.config = config
        self.api_key = os.getenv('TMDB_API_KEY')
        self.base_url = config['api']['tmdb_base_url']
        self.timeout = config['api']['timeout']
        
        if not self.api_key:
            raise ValueError("TMDB_API_KEY environment variable is required")
    
    def search_movie(self, title: str, year: int, original_title: str = None) -> Optional[MovieInfo]:
        """Search for movie information with improved strategy"""
        logger.info(f"Searching movie: {title} ({year}), original_title: {original_title}")
        
        movie_data = None
        search_attempts = []
        
        # Strategy 1: Use both titles + year if available
        if original_title and title != original_title and year:
            search_attempts.append((f"{original_title} {title}", year, "combined titles + year"))
        
        # Strategy 2: English title + year
        if original_title and year:
            search_attempts.append((original_title, year, "original title + year"))
        
        # Strategy 3: Chinese title + year  
        if title and year:
            search_attempts.append((title, year, "title + year"))
        
        # Strategy 4: English title only
        if original_title:
            search_attempts.append((original_title, None, "original title only"))
        
        # Strategy 5: Chinese title only
        if title and title != original_title:
            search_attempts.append((title, None, "title only"))
        
        # Try each search strategy
        for search_term, search_year, strategy in search_attempts:
            logger.info(f"Trying search strategy: {strategy} - '{search_term}' ({search_year})")
            movie_data = self._search_movie_api(search_term, search_year)
            if movie_data:
                logger.info(f"Found match using strategy: {strategy}")
                break
        
        if movie_data:
            movie_info = self._parse_movie_data(movie_data)
            # Get detailed info including IMDB ID and alternative titles
            detailed_info = self._get_movie_details(movie_info.id)
            if detailed_info:
                # Set IMDB ID
                imdb_id = detailed_info.get('imdb_id')
                if imdb_id and imdb_id.strip():  # Ensure IMDB ID is not empty
                    movie_info.imdb_id = imdb_id
                else:
                    logger.warning(f"No IMDB ID found for movie {movie_info.title} (TMDB ID: {movie_info.id})")
                
                # Enhance movie info with alternative titles
                self._enhance_movie_with_alternative_titles(movie_info, detailed_info)
            return movie_info
        
        logger.warning(f"No TMDB match found for movie: {title} ({year}) with original_title: {original_title}")
        return None
    
    def search_tv_show(self, title: str, year: int) -> Optional[TVShowInfo]:
        """Search for TV show information"""
        logger.info(f"Searching TV show: {title} ({year})")
        
        # Try English title first
        show_data = self._search_tv_api(title, year)
        
        # If no results, try Chinese title
        if not show_data:
            show_data = self._search_tv_api(title, year)
        
        if show_data:
            show_info = self._parse_tv_data(show_data)
            # Get detailed info including IMDB ID
            detailed_info = self._get_tv_details(show_info.id)
            if detailed_info:
                imdb_id = detailed_info.get('external_ids', {}).get('imdb_id')
                if imdb_id and imdb_id.strip():  # Ensure IMDB ID is not empty
                    show_info.imdb_id = imdb_id
                else:
                    logger.warning(f"No IMDB ID found for TV show {show_info.name} (TMDB ID: {show_info.id})")
            return show_info
        
        logger.warning(f"No TMDB match found for TV show: {title} ({year})")
        return None
    
    def get_season_info(self, show_id: int, season_number: int) -> Optional[SeasonInfo]:
        """Get detailed season information"""
        logger.debug(f"Getting season info: show_id={show_id}, season={season_number}")
        
        try:
            url = f"{self.base_url}/tv/{show_id}/season/{season_number}"
            params = {"api_key": self.api_key}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return SeasonInfo(
                season_number=data.get('season_number'),
                air_date=data.get('air_date', ''),
                overview=data.get('overview', ''),
                poster_path=data.get('poster_path'),
                episode_count=len(data.get('episodes', []))
            )
            
        except Exception as e:
            logger.error(f"Failed to get season info: {e}")
            return None
    
    def download_poster(self, poster_path: str, output_path: str) -> bool:
        """Download poster image"""
        if not poster_path:
            return False
        
        try:
            url = f"https://image.tmdb.org/t/p/w500{poster_path}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Downloaded poster: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download poster: {e}")
            return False
    
    def _search_movie_api(self, query: str, year: int) -> Optional[Dict[str, Any]]:
        """Search TMDB movie API"""
        try:
            url = f"{self.base_url}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": query,
                "year": year
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Return first result if available
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"TMDB movie search failed: {e}")
            return None
    
    def _search_tv_api(self, query: str, year: int) -> Optional[Dict[str, Any]]:
        """Search TMDB TV API"""
        try:
            url = f"{self.base_url}/search/tv"
            params = {
                "api_key": self.api_key,
                "query": query,
                "first_air_date_year": year
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            # Return first result if available
            return results[0] if results else None
            
        except Exception as e:
            logger.error(f"TMDB TV search failed: {e}")
            return None
    
    def _parse_movie_data(self, data: Dict[str, Any]) -> MovieInfo:
        """Parse TMDB movie data into MovieInfo"""
        # Get release year
        release_date = data.get('release_date', '')
        year = datetime.strptime(release_date, '%Y-%m-%d').year if release_date else 0
        
        return MovieInfo(
            id=data.get('id'),
            title=data.get('title'),
            original_title=data.get('original_title'),
            year=year,
            overview=data.get('overview', ''),
            poster_path=data.get('poster_path'),
            imdb_id=None,  # Need separate API call for IMDB ID
            tmdb_id=str(data.get('id')),
            director=None,  # Need separate API call for credits
            cast=[]  # Need separate API call for credits
        )
    
    def _parse_tv_data(self, data: Dict[str, Any]) -> TVShowInfo:
        """Parse TMDB TV data into TVShowInfo"""
        return TVShowInfo(
            id=data.get('id'),
            name=data.get('name'),
            original_name=data.get('original_name'),
            first_air_date=data.get('first_air_date', ''),
            overview=data.get('overview', ''),
            poster_path=data.get('poster_path'),
            imdb_id=None,  # Will be filled by detailed API call
            tmdb_id=str(data.get('id')),
            created_by=[]  # Need separate API call for creators
        )
    
    def _get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed movie information including IMDB ID and alternative titles"""
        try:
            url = f"{self.base_url}/movie/{movie_id}"
            params = {
                "api_key": self.api_key,
                "append_to_response": "alternative_titles,translations"
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get movie details: {e}")
            return None
    
    def _get_tv_details(self, tv_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed TV show information including external IDs"""
        try:
            url = f"{self.base_url}/tv/{tv_id}"
            params = {"api_key": self.api_key, "append_to_response": "external_ids"}
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get TV details: {e}")
            return None
    
    def _enhance_movie_with_alternative_titles(self, movie_info: MovieInfo, detailed_info: Dict[str, Any]):
        """Enhance movie info with alternative titles from TMDB"""
        try:
            # Store original values
            original_title = movie_info.original_title
            current_title = movie_info.title
            
            # Check alternative titles
            alt_titles = detailed_info.get('alternative_titles', {}).get('titles', [])
            
            # If original title is Chinese, look for English alternative title
            if self._is_chinese_text(original_title):
                # Look for English title in alternatives
                for alt in alt_titles:
                    if alt.get('iso_3166_1') in ['US', 'GB'] and not self._is_chinese_text(alt.get('title', '')):
                        movie_info.title = alt['title']
                        logger.info(f"Found English alternative title: {alt['title']}")
                        break
            else:
                # Original title is not Chinese, look for Chinese alternative title
                for alt in alt_titles:
                    if alt.get('iso_3166_1') in ['CN', 'TW', 'HK'] and self._is_chinese_text(alt.get('title', '')):
                        movie_info.title = alt['title']
                        logger.info(f"Found Chinese alternative title: {alt['title']}")
                        break
                
                # Also check translations for Chinese title
                translations = detailed_info.get('translations', {}).get('translations', [])
                for trans in translations:
                    if trans.get('iso_3166_1') in ['CN', 'TW', 'HK']:
                        trans_data = trans.get('data', {})
                        trans_title = trans_data.get('title')
                        if trans_title and self._is_chinese_text(trans_title):
                            movie_info.title = trans_title
                            logger.info(f"Found Chinese translated title: {trans_title}")
                            break
            
        except Exception as e:
            logger.warning(f"Failed to enhance movie with alternative titles: {e}")
    
    def _is_chinese_text(self, text: str) -> bool:
        """Check if text contains Chinese characters"""
        if not text:
            return False
        # Check for Chinese Unicode ranges
        for char in text:
            if '\u4e00' <= char <= '\u9fff' or '\u3400' <= char <= '\u4dbf':
                return True
        return False

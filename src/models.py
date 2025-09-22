"""
Data models for media organizer
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class MediaType(Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"

@dataclass
class ParsedInfo:
    """AI parsed information from filename"""
    title: str
    original_title: str
    year: int
    media_type: MediaType
    confidence: float
    season: Optional[int] = None
    episode: Optional[int] = None

@dataclass
class MediaFile:
    """Media file information"""
    path: str
    name: str
    media_type: MediaType
    parsed_info: Optional[ParsedInfo] = None

@dataclass
class MovieInfo:
    """Movie information from TMDB"""
    id: int
    title: str
    original_title: str
    year: int
    overview: str
    poster_path: Optional[str]
    imdb_id: Optional[str]
    tmdb_id: str
    director: Optional[str] = None
    cast: List[str] = None
    production_countries: List[Dict[str, str]] = None

@dataclass
class TVShowInfo:
    """TV Show information from TMDB"""
    id: int
    name: str
    original_name: str
    first_air_date: str
    overview: str
    poster_path: Optional[str]
    imdb_id: Optional[str]
    tmdb_id: str
    created_by: List[str] = None

@dataclass
class SeasonInfo:
    """Season information from TMDB"""
    id: int
    name: str
    season_number: int
    air_date: str
    overview: str
    poster_path: Optional[str]
    episode_count: int

@dataclass
class FileOperation:
    """File operation for dry run mode"""
    operation_type: str  # move, rename, create
    source: str
    destination: str
    description: str

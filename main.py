#!/usr/bin/env python3
"""
AI Media Organizer
Automatically organize movie and TV show files using local AI and TMDB API.
"""

import click
import logging
import os
from dotenv import load_dotenv

from src.utils import load_config, setup_logging
from src.scanner import MediaScanner
from src.matcher import TMDBMatcher
from src.organizer import FileOrganizer
from src.models import MediaType

# Load environment variables
load_dotenv()

@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--dry-run', is_flag=True, help='Preview mode, do not actually move files')
@click.option('--type', type=click.Choice(['movie', 'tv']), required=True, help='Media type to process')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.version_option(version='1.0.0')
def main(path, dry_run, type, verbose):
    """Organize media files in the specified directory"""
    try:
        # Setup logging
        setup_logging(verbose)
        logger = logging.getLogger(__name__)
        
        # Load configuration
        config = load_config()
        config['processing']['dry_run'] = dry_run
        
        click.echo(f"Starting media organization for: {path}")
        click.echo(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        click.echo(f"Type: {type}")
        
        # Initialize components
        scanner = MediaScanner(config)
        matcher = TMDBMatcher(config)
        organizer = FileOrganizer(config)
        
        # Scan for media files
        media_files = scanner.scan_directory(path)
        click.echo(f"Found {len(media_files)} media files")
        
        if not media_files:
            click.echo("No media files found!")
            return
        
        # Process files differently for movies vs TV shows
        unmatched_files = []
        processed_count = 0
        
        if type == 'movie':
            # Process movies individually
            for media_file in media_files:
                try:
                    click.echo(f"Processing: {media_file.name}")
                    
                    # Get folder context for better parsing
                    folder_context = None
                    file_dir = os.path.dirname(media_file.path)
                    if file_dir != path:  # If file is in a subfolder
                        folder_context = os.path.basename(file_dir)
                    
                    # Parse with AI
                    parsed_info = scanner.parse_with_ai(media_file.name, MediaType.MOVIE, folder_context)
                    if not parsed_info:
                        unmatched_files.append(media_file.path)
                        continue
                    
                    # Match with TMDB using improved search strategy
                    tmdb_info = matcher.search_movie(
                        title=parsed_info.title, 
                        year=parsed_info.year, 
                        original_title=parsed_info.original_title
                    )
                    if tmdb_info:
                        success = organizer.organize_movie(tmdb_info, media_file.path, path, parsed_info)
                        if success:
                            processed_count += 1
                        else:
                            unmatched_files.append(media_file.path)
                    else:
                        unmatched_files.append(media_file.path)
                        
                except Exception as e:
                    logger.error(f"Error processing {media_file.path}: {e}")
                    unmatched_files.append(media_file.path)
        
        else:
            # Process TV shows by folder
            tv_folders = {}
            for media_file in media_files:
                folder_path = os.path.dirname(media_file.path)
                folder_name = os.path.basename(folder_path)
                if folder_name not in tv_folders:
                    tv_folders[folder_name] = []
                tv_folders[folder_name].append(media_file.path)
            
            for folder_name, file_paths in tv_folders.items():
                try:
                    click.echo(f"Processing TV show folder: {folder_name}")
                    
                    # Parse folder name with AI
                    parsed_info = scanner.parse_with_ai(folder_name, MediaType.TV_SHOW)
                    if not parsed_info:
                        unmatched_files.extend(file_paths)
                        continue
                    
                    # Match with TMDB
                    tmdb_info = matcher.search_tv_show(parsed_info.title, parsed_info.year)
                    if tmdb_info:
                        success = organizer.organize_tv_show(tmdb_info, file_paths[0], path)  # Pass first file as reference
                        if success:
                            processed_count += len(file_paths)
                        else:
                            unmatched_files.extend(file_paths)
                    else:
                        unmatched_files.extend(file_paths)
                        
                except Exception as e:
                    logger.error(f"Error processing TV folder {folder_name}: {e}")
                    unmatched_files.extend(file_paths)
        
        # Handle unmatched files
        if unmatched_files:
            click.echo(f"Moving {len(unmatched_files)} unmatched files to Unmatched folder")
            for file_path in unmatched_files:
                organizer.move_to_unmatched(file_path)
        
        # Cleanup unwanted files
        if not dry_run:
            organizer.cleanup_unwanted(path)
        
        # Save scan session results
        scanner.save_scan_session()
        
        # Show results
        click.echo(f"\nResults:")
        click.echo(f"  Processed: {processed_count}")
        click.echo(f"  Unmatched: {len(unmatched_files)}")
        
        if dry_run:
            operations = organizer.get_operations()
            click.echo(f"  Planned operations: {len(operations)}")
            for op in operations[:5]:  # Show first 5 operations
                click.echo(f"    {op.operation_type}: {op.source} -> {op.destination}")
            if len(operations) > 5:
                click.echo(f"    ... and {len(operations) - 5} more operations")
        
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()

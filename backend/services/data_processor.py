# backend/services/data_processor.py
import pandas as pd
import os
from datetime import datetime
from typing import Dict, List, Optional
from models.database import get_db_engine
from utils.platform_mappers import PlatformMapper
from utils.data_validators import DataValidator
from utils.file_handlers import FileHandler

class MusicDataProcessor:
    """Modularized music data processing service"""
    
    def __init__(self, environment: str = 'dev'):
        self.environment = environment
        self.engine = get_db_engine()
        self.platform_mapper = PlatformMapper()
        self.validator = DataValidator()
        self.file_handler = FileHandler()
        
        self.stats = {
            'files_processed': 0,
            'records_inserted': 0,
            'errors': []
        }
    
    def process_folder(self, folder_path: str) -> Dict:
        """Process all files in a folder"""
        print(f"🚀 Processing folder: {folder_path}")
        
        files = self.file_handler.discover_files(folder_path)
        print(f"📁 Found {len(files)} files to process")
        
        for file_path in files:
            try:
                self.process_file(file_path)
            except Exception as e:
                self.stats['errors'].append({
                    'file': file_path,
                    'error': str(e)
                })
        
        return self.generate_processing_summary()
    
    def process_file(self, file_path: str) -> None:
        """Process a single data file"""
        file_info = self.file_handler.analyze_file(file_path)
        
        print(f"📄 Processing: {file_info['name']}")
        print(f"  Platform: {file_info['platform']}, Type: {file_info['type']}")
        
        # Read and validate data
        df = self.file_handler.read_file(file_path)
        if df is None or df.empty:
            print("  ⚠️ Could not read file or empty")
            return
        
        # Process based on file type
        if file_info['type'] == 'metadata':
            self.process_metadata(df, file_info)
        elif file_info['type'] == 'usage':
            self.process_usage_data(df, file_info)
        elif file_info['type'] == 'apple_streaming':
            self.process_apple_streaming(df, file_info)
        
        self.stats['files_processed'] += 1
    
    def process_metadata(self, df: pd.DataFrame, file_info: Dict) -> None:
        """Process metadata files (artist, track, album info)"""
        print("  📚 Processing metadata file")
        
        # Standardize columns
        df_clean = self.validator.clean_metadata(df)
        
        # Extract artists and tracks
        artists_data = self.extract_artists(df_clean, file_info)
        tracks_data = self.extract_tracks(df_clean, file_info)
        
        # Insert to database
        self.insert_artists(artists_data)
        self.insert_tracks(tracks_data)
        
        print(f"  ✅ Added {len(artists_data)} artists, {len(tracks_data)} tracks")
    
    def process_usage_data(self, df: pd.DataFrame, file_info: Dict) -> None:
        """Process usage/metrics data (streams, plays, etc.)"""
        print("  📊 Processing usage data")
        
        # Standardize usage data
        df_clean = self.validator.clean_usage_data(df, file_info['platform'])
        
        if df_clean is None or df_clean.empty:
            print("  ⚠️ No valid usage data found")
            return
        
        # Add metadata
        df_clean['platform_id'] = file_info['platform']
        df_clean['source_file'] = file_info['name']
        df_clean['environment'] = self.environment
        df_clean['processing_date'] = datetime.now()
        
        # Insert metrics
        self.insert_metrics(df_clean)
        print(f"  ✅ Inserted {len(df_clean)} metric records")
    
    def process_apple_streaming(self, df: pd.DataFrame, file_info: Dict) -> None:
        """Process Apple Music streaming data"""
        print("  🍎 Processing Apple streaming data")
        
        # Apple-specific column mapping
        column_map = {
            'Apple Identifier': 'apple_id',
            'Storefront Name': 'country',
            'Streams': 'metric_value',
            'Subscription Type': 'product_type'
        }
        
        df_mapped = df.rename(columns=column_map)
        df_clean = self.validator.clean_apple_data(df_mapped)
        
        # Map Apple IDs to ISRCs if possible
        df_clean = self.map_apple_identifiers(df_clean)
        
        # Insert streaming data
        self.insert_metrics(df_clean)
        print(f"  ✅ Processed {len(df_clean)} Apple streaming records")
    
    def extract_artists(self, df: pd.DataFrame, file_info: Dict) -> List[Dict]:
        """Extract artist data from metadata"""
        artists = []
        seen_artists = set()
        
        for _, row in df.iterrows():
            artist_name = row.get('artist_name')
            if not artist_name or artist_name in seen_artists:
                continue
                
            artist_id = self.generate_artist_id(artist_name, file_info['platform'])
            artists.append({
                'artist_id': artist_id,
                'artist_name': artist_name,
                'source_platform': file_info['platform'],
                'created_at': datetime.now()
            })
            seen_artists.add(artist_name)
        
        return artists
    
    def extract_tracks(self, df: pd.DataFrame, file_info: Dict) -> List[Dict]:
        """Extract track data from metadata"""
        tracks = []
        
        for _, row in df.iterrows():
            isrc = row.get('isrc')
            if not isrc:
                continue
                
            tracks.append({
                'isrc': isrc,
                'track_name': row.get('track_name'),
                'artist_id': self.generate_artist_id(row.get('artist_name'), file_info['platform']),
                'album_name': row.get('album_name'),
                'duration_seconds': row.get('duration'),
                'genre': row.get('genre'),
                'created_at': datetime.now()
            })
        
        return tracks
    
    def insert_artists(self, artists_data: List[Dict]) -> None:
        """Insert artist data to database"""
        if not artists_data:
            return
            
        df = pd.DataFrame(artists_data)
        df.to_sql('dim_artists', self.engine, if_exists='append', index=False)
    
    def insert_tracks(self, tracks_data: List[Dict]) -> None:
        """Insert track data to database"""
        if not tracks_data:
            return
            
        df = pd.DataFrame(tracks_data)
        df.to_sql('dim_tracks', self.engine, if_exists='append', index=False)
    
    def insert_metrics(self, metrics_df: pd.DataFrame) -> None:
        """Insert metrics data to database"""
        if metrics_df.empty:
            return
            
        # Ensure required columns
        required_cols = ['isrc', 'platform_id', 'metric_value', 'metric_type']
        for col in required_cols:
            if col not in metrics_df.columns:
                metrics_df[col] = None
        
        records_before = self.get_metrics_count()
        metrics_df.to_sql('fact_music_metrics', self.engine, if_exists='append', index=False)
        records_after = self.get_metrics_count()
        
        self.stats['records_inserted'] += (records_after - records_before)
    
    def generate_artist_id(self, artist_name: str, platform: str) -> str:
        """Generate consistent artist ID"""
        import hashlib
        if not artist_name:
            return None
        
        name_hash = hashlib.md5(artist_name.encode()).hexdigest()[:12].upper()
        return f"{platform.upper()}_{name_hash}"
    
    def map_apple_identifiers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Map Apple identifiers to ISRCs"""
        # Try to get existing mappings from database
        try:
            mapping_query = "SELECT apple_identifier, isrc FROM apple_identifier_mapping"
            mapping_df = pd.read_sql(mapping_query, self.engine)
            mapping_dict = dict(zip(mapping_df['apple_identifier'], mapping_df['isrc']))
            
            df['isrc'] = df['apple_id'].map(mapping_dict)
            
            # For unmapped items, use Apple ID as pseudo-ISRC
            unmapped_mask = df['isrc'].isna()
            df.loc[unmapped_mask, 'isrc'] = 'APPLE_' + df.loc[unmapped_mask, 'apple_id'].astype(str)
        except:
            # If no mapping table, use Apple ID as ISRC
            df['isrc'] = 'APPLE_' + df['apple_id'].astype(str)
        
        return df
    
    def get_metrics_count(self) -> int:
        """Get current metrics count"""
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT COUNT(*) FROM fact_music_metrics")).fetchone()
                return result[0]
        except:
            return 0
    
    def generate_processing_summary(self) -> Dict:
        """Generate processing summary"""
        return {
            'files_processed': self.stats['files_processed'],
            'records_inserted': self.stats['records_inserted'],
            'errors': self.stats['errors'],
            'success_rate': (self.stats['files_processed'] - len(self.stats['errors'])) / max(1, self.stats['files_processed']),
            'timestamp': datetime.now().isoformat()
        }
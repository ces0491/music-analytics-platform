# backend/utils/config.py
import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Config:
    """Application configuration management"""
    
    # Flask Configuration
    SECRET_KEY: str = os.environ.get('API_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG: bool = os.environ.get('FLASK_ENV', 'production') == 'development'
    
    # Database Configuration
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite:///data/music_analytics.db')
    DATABASE_POOL_SIZE: int = int(os.environ.get('DATABASE_POOL_SIZE', '10'))
    
    # Cache Configuration
    CACHE_TYPE: str = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT: int = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Email Configuration
    SMTP_SERVER: str = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USERNAME: str = os.environ.get('SMTP_USERNAME', '')
    SMTP_PASSWORD: str = os.environ.get('SMTP_PASSWORD', '')
    FROM_EMAIL: str = os.environ.get('FROM_EMAIL', '')
    FROM_NAME: str = os.environ.get('FROM_NAME', 'Prism Analytics')
    
    # File Processing Configuration
    MAX_FILE_SIZE_MB: int = int(os.environ.get('MAX_FILE_SIZE_MB', '100'))
    ALLOWED_EXTENSIONS: list = ['.csv', '.xlsx', '.xls', '.txt', '.tsv']
    UPLOAD_FOLDER: str = os.environ.get('UPLOAD_FOLDER', 'data/raw')
    
    # Report Configuration
    REPORTS_FOLDER: str = os.environ.get('REPORTS_FOLDER', 'reports/generated')
    PDF_TIMEOUT_SECONDS: int = int(os.environ.get('PDF_TIMEOUT_SECONDS', '30'))
    
    # API Rate Limiting
    RATE_LIMIT_PER_DAY: int = int(os.environ.get('RATE_LIMIT_PER_DAY', '1000'))
    RATE_LIMIT_PER_HOUR: int = int(os.environ.get('RATE_LIMIT_PER_HOUR', '100'))
    
    # Brand Configuration
    BRAND_COLORS: Dict[str, str] = {
        'primary': '#1A1A1A',
        'accent': '#E50914',
        'secondary': '#333333',
        'background': '#FFFFFF'
    }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        warnings = []
        
        # Check required email settings for production
        if not cls.DEBUG and not cls.SMTP_USERNAME:
            warnings.append("SMTP_USERNAME not set - email functionality disabled")
        
        # Check database path
        if cls.DATABASE_URL.startswith('sqlite:///'):
            db_path = cls.DATABASE_URL.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create database directory: {e}")
        
        # Check required directories
        for folder in [cls.UPLOAD_FOLDER, cls.REPORTS_FOLDER]:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create folder {folder}: {e}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings
        }

# Sample data generator for development and testing
import pandas as pd
import random
from datetime import datetime, timedelta
from models.database import get_db_engine
from sqlalchemy import text

class SampleDataGenerator:
    """Generate realistic sample data for development and testing"""
    
    def __init__(self):
        self.engine = get_db_engine()
        
        # Sample artists with different genres and popularity levels
        self.sample_artists = [
            {'name': 'Taylor Swift', 'genre': 'Pop', 'popularity': 'mega'},
            {'name': 'Bad Bunny', 'genre': 'Reggaeton', 'popularity': 'mega'},
            {'name': 'Drake', 'genre': 'Hip-Hop', 'popularity': 'mega'},
            {'name': 'Olivia Rodrigo', 'genre': 'Pop', 'popularity': 'high'},
            {'name': 'The Weeknd', 'genre': 'R&B', 'popularity': 'high'},
            {'name': 'Billie Eilish', 'genre': 'Alternative', 'popularity': 'high'},
            {'name': 'Ed Sheeran', 'genre': 'Pop', 'popularity': 'high'},
            {'name': 'Dua Lipa', 'genre': 'Pop', 'popularity': 'high'},
            {'name': 'Post Malone', 'genre': 'Hip-Hop', 'popularity': 'high'},
            {'name': 'Ariana Grande', 'genre': 'Pop', 'popularity': 'high'},
            {'name': 'The Chainsmokers', 'genre': 'Electronic', 'popularity': 'medium'},
            {'name': 'Imagine Dragons', 'genre': 'Rock', 'popularity': 'medium'},
            {'name': 'Coldplay', 'genre': 'Rock', 'popularity': 'medium'},
            {'name': 'Maroon 5', 'genre': 'Pop', 'popularity': 'medium'},
            {'name': 'OneRepublic', 'genre': 'Pop', 'popularity': 'medium'},
            {'name': 'Indie Artist Alpha', 'genre': 'Indie', 'popularity': 'emerging'},
            {'name': 'Rising Star Beta', 'genre': 'Pop', 'popularity': 'emerging'},
            {'name': 'New Wave Gamma', 'genre': 'Electronic', 'popularity': 'emerging'}
        ]
        
        # Sample track templates
        self.track_templates = [
            'Blinding Lights', 'Watermelon Sugar', 'Levitating', 'Good 4 U',
            'Save Your Tears', 'Peaches', 'Montero', 'Industry Baby',
            'Heat Waves', 'Ghost', 'As It Was', 'Anti-Hero',
            'Unholy', 'I\'m Good', 'Flowers', 'Miracle',
            'New Rules', 'Don\'t Start Now', 'Physical', 'Love Again',
            'Circles', 'Sunflower', 'Better Now', 'Rockstar'
        ]
        
        # Platform distribution (realistic market share)
        self.platform_weights = {
            'spo-spotify': 0.35,
            'apl-apple-music': 0.25,
            'ytb-youtube': 0.20,
            'amz-amazon': 0.08,
            'dzr-deezer': 0.05,
            'tdl-tidal': 0.03,
            'pnd-pandora': 0.02,
            'scu-soundcloud': 0.02
        }
        
        # Country distribution
        self.country_weights = {
            'US': 0.25, 'GB': 0.12, 'CA': 0.08, 'AU': 0.06, 'DE': 0.06,
            'FR': 0.05, 'JP': 0.05, 'BR': 0.05, 'MX': 0.04, 'IN': 0.04,
            'KR': 0.03, 'ES': 0.03, 'IT': 0.03, 'NL': 0.02, 'SE': 0.02,
            'NO': 0.02, 'DK': 0.02, 'FI': 0.02, 'CH': 0.01, 'AT': 0.01
        }
    
    def generate_complete_dataset(self, months_back: int = 12, 
                                total_records: int = 50000) -> Dict:
        """Generate a complete realistic dataset"""
        print(f"🎵 Generating sample dataset with {total_records:,} records over {months_back} months...")
        
        # Generate artists
        artists_created = self.generate_artists()
        
        # Generate tracks for each artist
        tracks_created = self.generate_tracks()
        
        # Generate metrics data
        metrics_created = self.generate_metrics(months_back, total_records)
        
        # Generate some processing history
        history_created = self.generate_processing_history()
        
        return {
            'artists_created': artists_created,
            'tracks_created': tracks_created,
            'metrics_created': metrics_created,
            'history_created': history_created,
            'total_records': artists_created + tracks_created + metrics_created
        }
    
    def generate_artists(self) -> int:
        """Generate artist records"""
        artists_data = []
        
        for i, artist in enumerate(self.sample_artists):
            artist_id = f"SAMPLE_{artist['name'].replace(' ', '_').upper()}_{i:03d}"
            
            artists_data.append({
                'artist_id': artist_id,
                'artist_name': artist['name'],
                'artist_name_normalized': artist['name'].lower(),
                'source_platform': 'spo-spotify',
                'is_auto_generated': 0,
                'total_tracks': random.randint(5, 50),
                'total_streams': random.randint(1000000, 500000000)
            })
        
        # Insert artists
        df_artists = pd.DataFrame(artists_data)
        df_artists.to_sql('dim_artists', self.engine, if_exists='append', index=False)
        
        print(f"✅ Generated {len(artists_data)} artist records")
        return len(artists_data)
    
    def generate_tracks(self) -> int:
        """Generate track records"""
        tracks_data = []
        
        # Get artist IDs
        with self.engine.connect() as conn:
            result = conn.execute(text("SELECT artist_id, artist_name FROM dim_artists"))
            artists = [{'id': row[0], 'name': row[1]} for row in result]
        
        track_counter = 1
        for artist in artists:
            num_tracks = random.randint(3, 15)  # Each artist has 3-15 tracks
            
            for i in range(num_tracks):
                track_name = random.choice(self.track_templates)
                if i > 0:
                    # Add variations for additional tracks
                    variations = [
                        f"{track_name} (Remix)",
                        f"{track_name} (Acoustic)",
                        f"{track_name} (Live)",
                        f"{track_name} 2.0",
                        f"New {track_name}"
                    ]
                    track_name = random.choice(variations)
                
                isrc = f"SAMPLE{track_counter:06d}"
                
                tracks_data.append({
                    'isrc': isrc,
                    'track_name': track_name,
                    'artist_id': artist['id'],
                    'album_name': f"{artist['name']} Album {random.randint(1, 5)}",
                    'label': random.choice(['Universal Music', 'Sony Music', 'Warner Music', 'Independent']),
                    'duration_seconds': random.randint(120, 300),
                    'genre': random.choice(['Pop', 'Hip-Hop', 'Rock', 'Electronic', 'R&B', 'Indie']),
                    'release_date': self.random_date_in_range(days_back=365*3),
                    'total_streams': random.randint(10000, 10000000)
                })
                
                track_counter += 1
        
        # Insert tracks
        df_tracks = pd.DataFrame(tracks_data)
        df_tracks.to_sql('dim_tracks', self.engine, if_exists='append', index=False)
        
        print(f"✅ Generated {len(tracks_data)} track records")
        return len(tracks_data)
    
    def generate_metrics(self, months_back: int, total_records: int) -> int:
        """Generate realistic metrics data"""
        metrics_data = []
        
        # Get tracks and artists
        tracks_query = """
        SELECT t.isrc, t.track_name, t.artist_id, a.artist_name
        FROM dim_tracks t
        JOIN dim_artists a ON t.artist_id = a.artist_id
        """
        tracks_df = pd.read_sql(tracks_query, self.engine)
        
        # Generate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months_back * 30)
        
        platforms = list(self.platform_weights.keys())
        countries = list(self.country_weights.keys())
        
        for i in range(total_records):
            # Select random track (weighted by popularity)
            track = tracks_df.sample(1).iloc[0]
            
            # Generate random date
            random_date = self.random_date_between(start_date, end_date)
            date_id = int(random_date.strftime('%Y%m%d'))
            
            # Select platform (weighted)
            platform = random.choices(platforms, weights=list(self.platform_weights.values()))[0]
            
            # Select country (weighted)
            country = random.choices(countries, weights=list(self.country_weights.values()))[0]
            
            # Generate realistic metric value based on platform and track popularity
            base_streams = random.randint(10, 10000)
            
            # Adjust for platform
            platform_multiplier = {
                'spo-spotify': 1.0,
                'apl-apple-music': 0.8,
                'ytb-youtube': 1.5,
                'amz-amazon': 0.6,
                'dzr-deezer': 0.4,
                'tdl-tidal': 0.3,
                'pnd-pandora': 0.5,
                'scu-soundcloud': 0.7
            }.get(platform, 1.0)
            
            metric_value = int(base_streams * platform_multiplier * random.uniform(0.5, 2.0))
            
            metrics_data.append({
                'isrc': track['isrc'],
                'platform_id': platform,
                'country_code': country,
                'date_id': date_id,
                'metric_value': metric_value,
                'metric_type': 'streams',
                'product_type': random.choice(['premium', 'free', 'family']),
                'user_type': random.choice(['subscriber', 'free_user']),
                'source_file': f'sample_data_batch_{i//1000 + 1}.csv',
                'batch_id': f'SAMPLE_BATCH_{i//1000 + 1:03d}',
                'environment': 'dev',
                'data_quality_score': random.uniform(0.85, 1.0)
            })
            
            # Progress indicator
            if i % 5000 == 0:
                print(f"📊 Generated {i:,} metrics records...")
        
        # Insert metrics in batches
        batch_size = 5000
        total_inserted = 0
        
        for i in range(0, len(metrics_data), batch_size):
            batch = metrics_data[i:i + batch_size]
            df_batch = pd.DataFrame(batch)
            df_batch.to_sql('fact_music_metrics', self.engine, if_exists='append', index=False)
            total_inserted += len(batch)
            print(f"✅ Inserted batch: {total_inserted:,}/{len(metrics_data):,} metrics records")
        
        return len(metrics_data)
    
    def generate_processing_history(self) -> int:
        """Generate processing history records"""
        history_data = []
        
        for i in range(20):  # Generate 20 processing records
            start_time = self.random_date_in_range(days_back=30)
            end_time = start_time + timedelta(minutes=random.randint(5, 60))
            
            records_processed = random.randint(1000, 50000)
            success_rate = random.uniform(0.85, 1.0)
            records_inserted = int(records_processed * success_rate)
            
            history_data.append({
                'batch_id': f'SAMPLE_BATCH_{i+1:03d}',
                'file_path': f'/data/sample/batch_{i+1}_data.csv',
                'file_name': f'batch_{i+1}_data.csv',
                'platform_id': random.choice(['spo-spotify', 'apl-apple-music', 'ytb-youtube']),
                'start_time': start_time,
                'end_time': end_time,
                'records_processed': records_processed,
                'records_inserted': records_inserted,
                'records_updated': random.randint(0, 100),
                'records_rejected': records_processed - records_inserted,
                'file_size_bytes': random.randint(100000, 10000000),
                'processing_status': 'completed' if success_rate > 0.9 else 'completed_with_warnings',
                'processing_duration_seconds': (end_time - start_time).total_seconds(),
                'processed_by': 'sample_data_generator'
            })
        
        # Insert processing history
        df_history = pd.DataFrame(history_data)
        df_history.to_sql('processing_history', self.engine, if_exists='append', index=False)
        
        print(f"✅ Generated {len(history_data)} processing history records")
        return len(history_data)
    
    def random_date_in_range(self, days_back: int) -> datetime:
        """Generate random date within specified range"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return self.random_date_between(start_date, end_date)
    
    def random_date_between(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate random date between two dates"""
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
    
    def cleanup_sample_data(self):
        """Remove all sample data"""
        with self.engine.connect() as conn:
            # Delete in reverse order of dependencies
            tables_to_clean = [
                'fact_music_metrics',
                'processing_history', 
                'dim_tracks',
                'dim_artists'
            ]
            
            for table in tables_to_clean:
                try:
                    result = conn.execute(text(f"DELETE FROM {table} WHERE batch_id LIKE 'SAMPLE_%' OR artist_id LIKE 'SAMPLE_%' OR isrc LIKE 'SAMPLE%'"))
                    print(f"🧹 Cleaned {result.rowcount} records from {table}")
                except Exception as e:
                    print(f"⚠️ Error cleaning {table}: {e}")
            
            conn.commit()

# Command line interface for data generation
if __name__ == "__main__":
    import sys
    
    generator = SampleDataGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'generate':
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            records = int(sys.argv[3]) if len(sys.argv) > 3 else 50000
            
            result = generator.generate_complete_dataset(months, records)
            print(f"\n🎉 Sample data generation complete!")
            print(f"📊 Total records created: {result['total_records']:,}")
            
        elif command == 'cleanup':
            generator.cleanup_sample_data()
            print("🧹 Sample data cleanup complete!")
            
        elif command == 'validate':
            config_status = Config.validate_config()
            print(f"Configuration Status: {'✅ Valid' if config_status['valid'] else '❌ Invalid'}")
            
            if config_status['issues']:
                print("Issues:")
                for issue in config_status['issues']:
                    print(f"  ❌ {issue}")
            
            if config_status['warnings']:
                print("Warnings:")
                for warning in config_status['warnings']:
                    print(f"  ⚠️ {warning}")
    else:
        print("Usage:")
        print("  python config.py generate [months] [records] - Generate sample data")
        print("  python config.py cleanup                     - Remove sample data")  
        print("  python config.py validate                    - Validate configuration")
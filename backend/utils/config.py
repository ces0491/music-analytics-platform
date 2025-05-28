# backend/utils/config.py
import os
from dataclasses import dataclass, field
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
    UPLOAD_FOLDER: str = os.environ.get('UPLOAD_FOLDER', 'data/raw')
    
    # Report Configuration
    REPORTS_FOLDER: str = os.environ.get('REPORTS_FOLDER', 'reports/generated')
    PDF_TIMEOUT_SECONDS: int = int(os.environ.get('PDF_TIMEOUT_SECONDS', '30'))
    
    # API Rate Limiting
    RATE_LIMIT_PER_DAY: int = int(os.environ.get('RATE_LIMIT_PER_DAY', '1000'))
    RATE_LIMIT_PER_HOUR: int = int(os.environ.get('RATE_LIMIT_PER_HOUR', '100'))
    
    # File extensions (using default_factory to avoid mutable default error)
    ALLOWED_EXTENSIONS: list = field(default_factory=lambda: ['.csv', '.xlsx', '.xls', '.txt', '.tsv'])
    
    # Brand configuration (using default_factory for mutable dict)
    BRAND_COLORS: Dict[str, str] = field(default_factory=lambda: {
        'primary': '#1A1A1A',
        'accent': '#E50914',
        'secondary': '#333333',
        'background': '#FFFFFF'
    })
    
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

class SampleDataGenerator:
    """Generate realistic sample data for development and testing"""
    
    def __init__(self):
        try:
            from models.database import get_db_engine
            self.engine = get_db_engine()
        except ImportError:
            print("Database module not available - sample data generation disabled")
            self.engine = None
        
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
            'KR': 0.03, 'ES': 0.03, 'IT': 0.03, 'NL': 0.02, 'SE': 0.02
        }
    
    def generate_complete_dataset(self, months_back: int = 12, 
                                total_records: int = 10000) -> Dict:
        """Generate a complete realistic dataset"""
        if not self.engine:
            return {'error': 'Database engine not available'}
        
        print(f"🎵 Generating sample dataset with {total_records:,} records over {months_back} months...")
        
        try:
            # Generate artists
            artists_created = self.generate_artists()
            
            # Generate tracks for each artist
            tracks_created = self.generate_tracks()
            
            # Generate metrics data
            metrics_created = self.generate_metrics(months_back, total_records)
            
            return {
                'artists_created': artists_created,
                'tracks_created': tracks_created,
                'metrics_created': metrics_created,
                'total_records': artists_created + tracks_created + metrics_created
            }
        except Exception as e:
            return {'error': str(e)}
    
    def generate_artists(self) -> int:
        """Generate artist records"""
        if not self.engine:
            return 0
        
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
        try:
            df_artists = pd.DataFrame(artists_data)
            df_artists.to_sql('dim_artists', self.engine, if_exists='append', index=False)
            print(f"✅ Generated {len(artists_data)} artist records")
            return len(artists_data)
        except Exception as e:
            print(f"Error generating artists: {e}")
            return 0
    
    def generate_tracks(self) -> int:
        """Generate track records"""
        if not self.engine:
            return 0
        
        # Simplified track generation for now
        print("✅ Track generation placeholder")
        return 0
    
    def generate_metrics(self, months_back: int, total_records: int) -> int:
        """Generate metrics data"""
        if not self.engine:
            return 0
        
        # Simplified metrics generation for now
        print("✅ Metrics generation placeholder")
        return 0
    
    def random_date_in_range(self, days_back: int) -> datetime:
        """Generate random date within specified range"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))

# Command line interface for data generation
if __name__ == "__main__":
    import sys
    
    generator = SampleDataGenerator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'generate':
            months = int(sys.argv[2]) if len(sys.argv) > 2 else 12
            records = int(sys.argv[3]) if len(sys.argv) > 3 else 10000
            
            result = generator.generate_complete_dataset(months, records)
            print(f"\n🎉 Sample data generation complete!")
            print(f"📊 Result: {result}")
            
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
        print("  python config.py validate                    - Validate configuration")
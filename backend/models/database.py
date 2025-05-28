# backend/models/database.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

def get_db_engine():
    """Get database engine with connection pooling"""
    db_path = os.environ.get('DATABASE_URL', 'sqlite:///data/music_analytics.db')
    
    # Create directory if it doesn't exist for SQLite
    if db_path.startswith('sqlite:///'):
        db_file_path = db_path.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_file_path), exist_ok=True)
    
    engine = create_engine(
        db_path,
        echo=False,
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

def get_session():
    """Get database session"""
    engine = get_db_engine()
    Session = sessionmaker(bind=engine)
    return Session()

def init_database():
    """Initialize complete database schema"""
    engine = get_db_engine()
    
    with engine.connect() as conn:
        # Artists dimension table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_artists (
                artist_id TEXT PRIMARY KEY,
                artist_name TEXT NOT NULL,
                artist_name_normalized TEXT,
                source_platform TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_auto_generated INTEGER DEFAULT 0,
                total_tracks INTEGER DEFAULT 0,
                total_streams INTEGER DEFAULT 0
            )
        """))
        
        # Tracks dimension table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_tracks (
                isrc TEXT PRIMARY KEY,
                track_name TEXT,
                artist_id TEXT,
                album_name TEXT,
                label TEXT,
                duration_seconds INTEGER,
                release_date DATE,
                genre TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_streams INTEGER DEFAULT 0,
                FOREIGN KEY (artist_id) REFERENCES dim_artists(artist_id)
            )
        """))
        
        # Platforms dimension table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_platforms (
                platform_id TEXT PRIMARY KEY,
                platform_name TEXT NOT NULL,
                platform_category TEXT,
                metric_type TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Countries dimension table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_countries (
                country_code TEXT PRIMARY KEY,
                country_name TEXT,
                country_region TEXT,
                continent TEXT,
                population INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Dates dimension table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS dim_dates (
                date_id INTEGER PRIMARY KEY,
                full_date DATE UNIQUE NOT NULL,
                year INTEGER,
                month INTEGER,
                month_name TEXT,
                quarter INTEGER,
                day_of_week INTEGER,
                day_name TEXT,
                is_weekend INTEGER DEFAULT 0,
                is_holiday INTEGER DEFAULT 0
            )
        """))
        
        # Main fact table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fact_music_metrics (
                metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                isrc TEXT,
                platform_id TEXT NOT NULL,
                country_code TEXT,
                date_id INTEGER,
                metric_value REAL NOT NULL,
                metric_type TEXT,
                product_type TEXT,
                user_type TEXT,
                age_group TEXT,
                gender TEXT,
                source_file TEXT,
                batch_id TEXT,
                processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                environment TEXT DEFAULT 'prod',
                data_quality_score REAL DEFAULT 1.0,
                FOREIGN KEY (isrc) REFERENCES dim_tracks(isrc),
                FOREIGN KEY (platform_id) REFERENCES dim_platforms(platform_id),
                FOREIGN KEY (country_code) REFERENCES dim_countries(country_code),
                FOREIGN KEY (date_id) REFERENCES dim_dates(date_id)
            )
        """))
        
        # Processing history table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS processing_history (
                processing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT UNIQUE,
                file_path TEXT,
                file_name TEXT,
                platform_id TEXT,
                processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                records_processed INTEGER,
                records_inserted INTEGER,
                records_updated INTEGER,
                records_rejected INTEGER,
                file_size_bytes INTEGER,
                file_checksum TEXT,
                processing_status TEXT,
                error_message TEXT,
                processing_duration_seconds REAL,
                processed_by TEXT
            )
        """))
        
        # Apple identifier mapping
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS apple_identifier_mapping (
                apple_identifier TEXT PRIMARY KEY,
                isrc TEXT,
                track_name TEXT,
                artist_name TEXT,
                confidence_score REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                verified_by TEXT,
                is_active INTEGER DEFAULT 1
            )
        """))
        
        # User management (for future multi-tenancy)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                full_name TEXT,
                role TEXT DEFAULT 'viewer',
                api_key TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT
            )
        """))
        
        # Report generation history
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS report_history (
                report_id TEXT PRIMARY KEY,
                artist_id TEXT,
                report_type TEXT,
                report_period TEXT,
                generated_by TEXT,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT,
                file_size_bytes INTEGER,
                email_sent_to TEXT,
                email_sent_at TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                last_downloaded_at TIMESTAMP,
                is_public INTEGER DEFAULT 0,
                expiry_date DATE
            )
        """))
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_metrics_platform ON fact_music_metrics(platform_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_date ON fact_music_metrics(date_id)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_country ON fact_music_metrics(country_code)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_isrc ON fact_music_metrics(isrc)",
            "CREATE INDEX IF NOT EXISTS idx_metrics_value ON fact_music_metrics(metric_value)",
            "CREATE INDEX IF NOT EXISTS idx_tracks_artist ON dim_tracks(artist_id)",
            "CREATE INDEX IF NOT EXISTS idx_artists_name ON dim_artists(artist_name_normalized)",
            "CREATE INDEX IF NOT EXISTS idx_dates_full ON dim_dates(full_date)",
            "CREATE INDEX IF NOT EXISTS idx_processing_status ON processing_history(processing_status)",
            "CREATE INDEX IF NOT EXISTS idx_processing_date ON processing_history(processing_date)"
        ]
        
        for index in indexes:
            try:
                conn.execute(text(index))
            except:
                pass  # Index might already exist
        
        conn.commit()
        
        # Insert initial platform data
        platforms = [
            ('spo-spotify', 'Spotify', 'streaming', 'streams'),
            ('apl-apple-music', 'Apple Music', 'streaming', 'streams'),
            ('apl-itunes', 'iTunes', 'sales', 'sales'),
            ('amz-amazon', 'Amazon Music', 'streaming', 'streams'),
            ('dzr-deezer', 'Deezer', 'streaming', 'streams'),
            ('tdl-tidal', 'Tidal', 'streaming', 'streams'),
            ('pnd-pandora', 'Pandora', 'streaming', 'streams'),
            ('scu-soundcloud', 'SoundCloud', 'streaming', 'plays'),
            ('ytb-youtube', 'YouTube', 'video', 'views'),
            ('vvo-vevo', 'Vevo', 'video', 'views'),
            ('fbk-facebook', 'Facebook', 'social', 'events'),
            ('ins-instagram', 'Instagram', 'social', 'events'),
            ('ttk-tiktok', 'TikTok', 'social', 'views'),
            ('awa-awa', 'AWA', 'streaming', 'streams'),
            ('boo-boomplay', 'Boomplay', 'streaming', 'streams'),
            ('jio-jiosaavn', 'JioSaavn', 'streaming', 'streams'),
            ('gna-gaana', 'Gaana', 'streaming', 'streams'),
            ('ang-anghami', 'Anghami', 'streaming', 'streams')
        ]
        
        for platform in platforms:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_platforms 
                    (platform_id, platform_name, platform_category, metric_type)
                    VALUES (?, ?, ?, ?)
                """), platform)
            except:
                pass
        
        # Insert common countries
        countries = [
            ('US', 'United States', 'North America', 'Americas'),
            ('GB', 'United Kingdom', 'Europe', 'Europe'),
            ('CA', 'Canada', 'North America', 'Americas'),
            ('AU', 'Australia', 'Oceania', 'Oceania'),
            ('DE', 'Germany', 'Europe', 'Europe'),
            ('FR', 'France', 'Europe', 'Europe'),
            ('JP', 'Japan', 'Asia', 'Asia'),
            ('BR', 'Brazil', 'South America', 'Americas'),
            ('MX', 'Mexico', 'North America', 'Americas'),
            ('IN', 'India', 'Asia', 'Asia'),
            ('KR', 'South Korea', 'Asia', 'Asia'),
            ('ES', 'Spain', 'Europe', 'Europe'),
            ('IT', 'Italy', 'Europe', 'Europe'),
            ('NL', 'Netherlands', 'Europe', 'Europe'),
            ('SE', 'Sweden', 'Europe', 'Europe'),
            ('NO', 'Norway', 'Europe', 'Europe'),
            ('DK', 'Denmark', 'Europe', 'Europe'),
            ('FI', 'Finland', 'Europe', 'Europe'),
            ('CH', 'Switzerland', 'Europe', 'Europe'),
            ('AT', 'Austria', 'Europe', 'Europe')
        ]
        
        for country in countries:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_countries 
                    (country_code, country_name, country_region, continent)
                    VALUES (?, ?, ?, ?)
                """), country)
            except:
                pass
        
        conn.commit()
        
    print("✅ Database schema initialized successfully")

def create_sample_data():
    """Create sample data for development and testing"""
    engine = get_db_engine()
    
    # Sample artists
    sample_artists = [
        ('SAMPLE_TAYLOR', 'Taylor Swift', 'taylor swift', 'spo-spotify', 0),
        ('SAMPLE_DRAKE', 'Drake', 'drake', 'spo-spotify', 0),
        ('SAMPLE_BUNNY', 'Bad Bunny', 'bad bunny', 'spo-spotify', 0),
        ('SAMPLE_OLIVIA', 'Olivia Rodrigo', 'olivia rodrigo', 'spo-spotify', 0),
        ('SAMPLE_WEEKND', 'The Weeknd', 'the weeknd', 'spo-spotify', 0)
    ]
    
    # Sample tracks
    sample_tracks = [
        ('SAMPLE001', 'Anti-Hero', 'SAMPLE_TAYLOR', 'Midnights', 'Republic Records', 200, '2022-10-21', 'Pop'),
        ('SAMPLE002', 'God Is A Woman', 'SAMPLE_DRAKE', 'Certified Lover Boy', 'OVO Sound', 234, '2021-09-03', 'Hip-Hop'),
        ('SAMPLE003', 'Me Porto Bonito', 'SAMPLE_BUNNY', 'Un Verano Sin Ti', 'Rimas Entertainment', 167, '2022-05-06', 'Reggaeton'),
        ('SAMPLE004', 'Good 4 U', 'SAMPLE_OLIVIA', 'SOUR', 'Geffen Records', 178, '2021-05-14', 'Pop'),
        ('SAMPLE005', 'Blinding Lights', 'SAMPLE_WEEKND', 'After Hours', 'XO/Republic', 200, '2019-11-29', 'Synthpop')
    ]
    
    with engine.connect() as conn:
        # Insert sample artists
        for artist in sample_artists:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_artists 
                    (artist_id, artist_name, artist_name_normalized, source_platform, is_auto_generated)
                    VALUES (?, ?, ?, ?, ?)
                """), artist)
            except:
                pass
        
        # Insert sample tracks
        for track in sample_tracks:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_tracks 
                    (isrc, track_name, artist_id, album_name, label, duration_seconds, release_date, genre)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), track)
            except:
                pass
        
        # Generate sample metrics data
        import random
        from datetime import datetime, timedelta
        
        platforms = ['spo-spotify', 'apl-apple-music', 'ytb-youtube']
        countries = ['US', 'GB', 'CA', 'AU', 'DE']
        tracks = ['SAMPLE001', 'SAMPLE002', 'SAMPLE003', 'SAMPLE004', 'SAMPLE005']
        
        # Generate data for last 12 months
        start_date = datetime.now() - timedelta(days=365)
        
        sample_metrics = []
        for i in range(5000):  # Generate 5000 sample records
            date = start_date + timedelta(days=random.randint(0, 365))
            date_id = int(date.strftime('%Y%m%d'))
            
            metric = (
                random.choice(tracks),
                random.choice(platforms),
                random.choice(countries),
                date_id,
                random.randint(100, 50000),  # metric_value
                'streams',
                'premium' if random.random() > 0.3 else 'free',
                f'sample_batch_{i//1000}',
                'dev'
            )
            sample_metrics.append(metric)
        
        # Insert sample metrics
        for metric in sample_metrics:
            try:
                conn.execute(text("""
                    INSERT INTO fact_music_metrics 
                    (isrc, platform_id, country_code, date_id, metric_value, metric_type, product_type, batch_id, environment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """), metric)
            except:
                pass
        
        conn.commit()
    
    print("✅ Sample data created successfully")

if __name__ == "__main__":
    init_database()
    create_sample_data()
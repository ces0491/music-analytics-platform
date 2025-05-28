# generate-sample-data.py - Simple sample data generator
import random
from datetime import datetime, timedelta
from models.database import get_db_engine
from sqlalchemy import text

def generate_sample_data():
    """Generate sample music analytics data"""
    print("🎵 Generating sample music data...")
    
    engine = get_db_engine()
    
    with engine.connect() as conn:
        # Sample artists
        print("Adding sample artists...")
        sample_artists = [
            ("SAMPLE_TAYLOR_SWIFT_001", "Taylor Swift", "taylor swift", "spo-spotify", 0),
            ("SAMPLE_DRAKE_002", "Drake", "drake", "spo-spotify", 0),
            ("SAMPLE_BAD_BUNNY_003", "Bad Bunny", "bad bunny", "spo-spotify", 0),
            ("SAMPLE_OLIVIA_004", "Olivia Rodrigo", "olivia rodrigo", "spo-spotify", 0),
            ("SAMPLE_WEEKND_005", "The Weeknd", "the weeknd", "spo-spotify", 0)
        ]
        
        for artist in sample_artists:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_artists 
                    (artist_id, artist_name, artist_name_normalized, source_platform, is_auto_generated)
                    VALUES (?, ?, ?, ?, ?)
                """), artist)
            except Exception as e:
                print(f"Error adding artist {artist[1]}: {e}")
        
        print("✅ Sample artists added")
        
        # Sample tracks
        print("Adding sample tracks...")
        sample_tracks = [
            ("SAMPLE001", "Anti-Hero", "SAMPLE_TAYLOR_SWIFT_001", "Midnights", "Republic Records"),
            ("SAMPLE002", "God Is A Woman", "SAMPLE_DRAKE_002", "Certified Lover Boy", "OVO Sound"),
            ("SAMPLE003", "Me Porto Bonito", "SAMPLE_BAD_BUNNY_003", "Un Verano Sin Ti", "Rimas Entertainment"),
            ("SAMPLE004", "Good 4 U", "SAMPLE_OLIVIA_004", "SOUR", "Geffen Records"),
            ("SAMPLE005", "Blinding Lights", "SAMPLE_WEEKND_005", "After Hours", "XO/Republic")
        ]
        
        for track in sample_tracks:
            try:
                conn.execute(text("""
                    INSERT OR IGNORE INTO dim_tracks 
                    (isrc, track_name, artist_id, album_name, label)
                    VALUES (?, ?, ?, ?, ?)
                """), track)
            except Exception as e:
                print(f"Error adding track {track[1]}: {e}")
        
        print("✅ Sample tracks added")
        
        # Sample streaming data
        print("Adding sample streaming data...")
        platforms = ["spo-spotify", "apl-apple-music", "ytb-youtube"]
        countries = ["US", "GB", "CA", "AU", "DE"]
        tracks = ["SAMPLE001", "SAMPLE002", "SAMPLE003", "SAMPLE004", "SAMPLE005"]
        
        metrics_added = 0
        for i in range(2000):  # Generate 2000 sample records
            date_id = 20240100 + random.randint(1, 365)  # Random date in 2024
            try:
                conn.execute(text("""
                    INSERT INTO fact_music_metrics 
                    (isrc, platform_id, country_code, date_id, metric_value, metric_type, batch_id, environment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """), (
                    random.choice(tracks),
                    random.choice(platforms), 
                    random.choice(countries),
                    date_id,
                    random.randint(1000, 100000),  # Random streams between 1K-100K
                    "streams",
                    "sample_batch",
                    "dev"
                ))
                metrics_added += 1
            except Exception as e:
                continue  # Skip errors and continue
        
        conn.commit()
        print(f"✅ {metrics_added} streaming records added")
        
        # Verify data was added
        total_streams = conn.execute(text("SELECT SUM(metric_value) FROM fact_music_metrics")).scalar() or 0
        total_artists = conn.execute(text("SELECT COUNT(*) FROM dim_artists")).scalar() or 0
        total_tracks = conn.execute(text("SELECT COUNT(*) FROM dim_tracks")).scalar() or 0
        
        print(f"📊 Data Summary:")
        print(f"   Artists: {total_artists}")
        print(f"   Tracks: {total_tracks}")
        print(f"   Total Streams: {total_streams:,}")
        
        if total_streams > 0:
            print("🎉 Sample data generation successful!")
            return True
        else:
            print("⚠️ No streaming data was added")
            return False

if __name__ == "__main__":
    try:
        generate_sample_data()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
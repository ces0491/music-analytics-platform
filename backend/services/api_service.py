# backend/services/api_service.py
from flask import Blueprint, jsonify, request
from flask_caching import Cache
import pandas as pd
from datetime import datetime, timedelta
from models.database import get_db_engine
from services.auth_service import require_api_key
from sqlalchemy import text

api_bp = Blueprint('api', __name__)
cache = Cache()

class MusicAnalyticsAPI:
    """Modularized API service for music analytics"""
    
    def __init__(self):
        self.engine = get_db_engine()
    
    def get_dashboard_overview(self):
        """Get main dashboard metrics"""
        with self.engine.connect() as conn:
            # Total metrics
            total_streams = conn.execute(text("""
                SELECT SUM(metric_value) as total_streams
                FROM fact_music_metrics 
                WHERE metric_type = 'streams'
            """)).scalar() or 0
            
            # Unique artists
            unique_artists = conn.execute(text("""
                SELECT COUNT(DISTINCT artist_id) 
                FROM dim_artists
            """)).scalar() or 0
            
            # Active platforms
            active_platforms = conn.execute(text("""
                SELECT COUNT(DISTINCT platform_id) 
                FROM fact_music_metrics
            """)).scalar() or 0
            
            # This week vs last week
            this_week_streams = conn.execute(text("""
                SELECT SUM(metric_value) as weekly_streams
                FROM fact_music_metrics f
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE d.full_date >= DATE('now', '-7 days')
                AND metric_type = 'streams'
            """)).scalar() or 0
            
            return {
                'total_streams': int(total_streams),
                'unique_artists': int(unique_artists),
                'active_platforms': int(active_platforms),
                'weekly_streams': int(this_week_streams),
                'growth_percentage': 12.5  # Calculate actual growth
            }
    
    def get_trending_artists(self, limit=10):
        """Get trending artists with growth metrics"""
        query = """
        WITH artist_metrics AS (
            SELECT 
                a.artist_id,
                a.artist_name,
                SUM(CASE WHEN d.full_date >= DATE('now', '-7 days') 
                    THEN f.metric_value ELSE 0 END) as this_week,
                SUM(CASE WHEN d.full_date >= DATE('now', '-14 days') 
                    AND d.full_date < DATE('now', '-7 days')
                    THEN f.metric_value ELSE 0 END) as last_week,
                SUM(f.metric_value) as total_streams
            FROM fact_music_metrics f
            JOIN dim_tracks t ON f.isrc = t.isrc
            JOIN dim_artists a ON t.artist_id = a.artist_id
            LEFT JOIN dim_dates d ON f.date_id = d.date_id
            WHERE f.metric_type = 'streams'
            GROUP BY a.artist_id, a.artist_name
            HAVING this_week > 0
        )
        SELECT 
            artist_name,
            total_streams,
            this_week,
            last_week,
            CASE 
                WHEN last_week > 0 THEN 
                    ROUND((this_week - last_week) * 100.0 / last_week, 1)
                ELSE 100.0 
            END as growth_percentage
        FROM artist_metrics
        ORDER BY this_week DESC
        LIMIT ?
        """
        
        return pd.read_sql(query, self.engine, params=[limit]).to_dict('records')
    
    def get_platform_distribution(self):
        """Get platform performance distribution"""
        query = """
        SELECT 
            p.platform_name,
            p.platform_category,
            COUNT(DISTINCT f.isrc) as unique_tracks,
            SUM(f.metric_value) as total_value,
            ROUND(100.0 * SUM(f.metric_value) / 
                (SELECT SUM(metric_value) FROM fact_music_metrics), 2) as market_share
        FROM fact_music_metrics f
        JOIN dim_platforms p ON f.platform_id = p.platform_id
        GROUP BY p.platform_name, p.platform_category
        ORDER BY total_value DESC
        """
        
        return pd.read_sql(query, self.engine).to_dict('records')
    
    def get_geographic_performance(self):
        """Get performance by geography"""
        query = """
        SELECT 
            COALESCE(c.country_name, f.country_code) as country,
            f.country_code,
            COUNT(DISTINCT f.isrc) as unique_tracks,
            SUM(f.metric_value) as total_streams
        FROM fact_music_metrics f
        LEFT JOIN dim_countries c ON f.country_code = c.country_code
        WHERE f.country_code IS NOT NULL AND f.country_code != ''
        GROUP BY f.country_code, c.country_name
        ORDER BY total_streams DESC
        LIMIT 50
        """
        
        return pd.read_sql(query, self.engine).to_dict('records')
    
    def get_time_series_data(self, period='daily', days=30):
        """Get time series data for charts"""
        if period == 'daily':
            date_format = '%Y-%m-%d'
            group_by = "d.full_date"
        else:
            date_format = '%Y-%m'
            group_by = "strftime('%Y-%m', d.full_date)"
        
        query = f"""
        SELECT 
            {group_by} as period,
            SUM(f.metric_value) as total_streams,
            COUNT(DISTINCT f.isrc) as unique_tracks,
            COUNT(DISTINCT t.artist_id) as unique_artists
        FROM fact_music_metrics f
        JOIN dim_tracks t ON f.isrc = t.isrc
        LEFT JOIN dim_dates d ON f.date_id = d.date_id
        WHERE d.full_date >= DATE('now', '-{days} days')
        AND f.metric_type = 'streams'
        GROUP BY {group_by}
        ORDER BY period
        """
        
        return pd.read_sql(query, self.engine).to_dict('records')
    
    def get_artist_details(self, artist_id):
        """Get detailed artist analytics"""
        with self.engine.connect() as conn:
            # Artist info
            artist_info = conn.execute(text("""
                SELECT * FROM dim_artists WHERE artist_id = :artist_id
            """), {"artist_id": artist_id}).fetchone()
            
            if not artist_info:
                return None
            
            # Top tracks
            top_tracks = pd.read_sql("""
                SELECT 
                    t.track_name,
                    t.album_name,
                    SUM(f.metric_value) as total_streams,
                    COUNT(DISTINCT f.platform_id) as platforms
                FROM fact_music_metrics f
                JOIN dim_tracks t ON f.isrc = t.isrc
                WHERE t.artist_id = ?
                GROUP BY t.isrc, t.track_name, t.album_name
                ORDER BY total_streams DESC
                LIMIT 10
            """, self.engine, params=[artist_id]).to_dict('records')
            
            # Platform breakdown
            platform_data = pd.read_sql("""
                SELECT 
                    p.platform_name,
                    SUM(f.metric_value) as streams,
                    COUNT(DISTINCT f.isrc) as tracks
                FROM fact_music_metrics f
                JOIN dim_platforms p ON f.platform_id = p.platform_id
                JOIN dim_tracks t ON f.isrc = t.isrc
                WHERE t.artist_id = ?
                GROUP BY p.platform_name
                ORDER BY streams DESC
            """, self.engine, params=[artist_id]).to_dict('records')
            
            return {
                'artist_info': dict(artist_info._mapping),
                'top_tracks': top_tracks,
                'platform_breakdown': platform_data
            }

# Initialize API service
api_service = MusicAnalyticsAPI()

# API Endpoints
@api_bp.route('/dashboard/overview')
@cache.cached(timeout=300)
def dashboard_overview():
    """Main dashboard overview endpoint"""
    try:
        data = api_service.get_dashboard_overview()
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/artists/trending')
@cache.cached(timeout=600)
def trending_artists():
    """Get trending artists"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        data = api_service.get_trending_artists(limit)
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/analytics/platforms')
@cache.cached(timeout=900)
def platform_analytics():
    """Platform distribution analytics"""
    try:
        data = api_service.get_platform_distribution()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/analytics/geographic')
@cache.cached(timeout=900)
def geographic_analytics():
    """Geographic performance analytics"""
    try:
        data = api_service.get_geographic_performance()
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/analytics/timeseries')
@cache.cached(timeout=300)
def timeseries_analytics():
    """Time series analytics"""
    period = request.args.get('period', 'daily')
    days = request.args.get('days', 30, type=int)
    
    try:
        data = api_service.get_time_series_data(period, days)
        return jsonify({
            'success': True,
            'data': data,
            'period': period,
            'days': days
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/artists/<artist_id>')
@cache.cached(timeout=600)
def artist_details(artist_id):
    """Get detailed artist information"""
    try:
        data = api_service.get_artist_details(artist_id)
        
        if not data:
            return jsonify({'success': False, 'error': 'Artist not found'}), 404
        
        return jsonify({
            'success': True,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/search/artists')
def search_artists():
    """Search for artists"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 20, type=int)
    
    if not query:
        return jsonify({'success': False, 'error': 'Query parameter required'}), 400
    
    try:
        search_query = """
        SELECT 
            a.artist_id,
            a.artist_name,
            COUNT(DISTINCT t.isrc) as track_count,
            SUM(f.metric_value) as total_streams
        FROM dim_artists a
        LEFT JOIN dim_tracks t ON a.artist_id = t.artist_id
        LEFT JOIN fact_music_metrics f ON t.isrc = f.isrc
        WHERE LOWER(a.artist_name) LIKE LOWER(?)
        GROUP BY a.artist_id, a.artist_name
        ORDER BY total_streams DESC NULLS LAST
        LIMIT ?
        """
        
        results = pd.read_sql(
            search_query, 
            api_service.engine, 
            params=[f'%{query}%', limit]
        ).to_dict('records')
        
        return jsonify({
            'success': True,
            'data': results,
            'query': query,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
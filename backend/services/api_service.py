# backend/services/api_service.py
from flask import Blueprint, jsonify, request, current_app
import pandas as pd
from datetime import datetime, timedelta
from models.database import get_db_engine
from services.auth_service import require_api_key
from sqlalchemy import text

api_bp = Blueprint('api', __name__)

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
        
        return pd.read_sql(query, self.engine, params=(limit,)).to_dict('records')
    
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
            """, self.engine, params=(artist_id,)).to_dict('records')
            
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
            """, self.engine, params=(artist_id,)).to_dict('records')
            
            return {
                'artist_info': dict(artist_info._mapping),
                'top_tracks': top_tracks,
                'platform_breakdown': platform_data
            }

# Initialize API service
api_service = MusicAnalyticsAPI()

# Simple caching decorator that doesn't require Flask-Caching
def simple_cache(timeout=300):
    """Simple in-memory cache decorator"""
    cache_store = {}
    
    def decorator(func):
        from functools import wraps
        
        @wraps(func)  # This preserves the original function name and metadata
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args))}_{hash(str(kwargs))}"
            
            # Check if we have cached result and it's not expired
            if cache_key in cache_store:
                cached_data, timestamp = cache_store[cache_key]
                if (datetime.now() - timestamp).seconds < timeout:
                    return cached_data
            
            # Get fresh data and cache it
            result = func(*args, **kwargs)
            cache_store[cache_key] = (result, datetime.now())
            return result
        
        return wrapper
    return decorator

# API Endpoints
@api_bp.route('/dashboard/overview')
@simple_cache(timeout=300)
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

@api_bp.route('/')
def api_root():
    """API root endpoint"""
    return jsonify({
        'service': 'Prism Analytics API',
        'version': '1.0.0',
        'status': 'running',
        'message': 'Welcome to Prism Analytics Music Data Intelligence Platform',
        'endpoints': {
            'health': '/health',
            'documentation': '/api/v1/docs',
            'dashboard': '/api/v1/dashboard/overview',
            'trending_artists': '/api/v1/artists/trending',
            'platform_analytics': '/api/v1/analytics/platforms',
            'geographic_analytics': '/api/v1/analytics/geographic',
            'time_series': '/api/v1/analytics/timeseries',
            'artist_search': '/api/v1/search/artists',
            'reports': '/reports/generate/wrapped'
        },
        'frontend': 'http://localhost:3000',
        'timestamp': datetime.now().isoformat()
    })

@api_bp.route('/docs')
def api_documentation():
    """API Documentation endpoint"""
    
    docs_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prism Analytics API Documentation</title>
        <style>
            body { 
                font-family: 'Inter', sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
                background: #f8f9fa;
            }
            .header { 
                background: linear-gradient(135deg, #1A1A1A 0%, #E50914 100%); 
                color: white; 
                padding: 30px; 
                border-radius: 12px; 
                margin-bottom: 30px;
                text-align: center;
            }
            .endpoint { 
                background: white; 
                padding: 20px; 
                margin: 20px 0; 
                border-radius: 8px; 
                border-left: 4px solid #E50914;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .method { 
                background: #E50914; 
                color: white; 
                padding: 4px 8px; 
                border-radius: 4px; 
                font-size: 12px; 
                font-weight: bold;
                margin-right: 10px;
            }
            .method.post { background: #28a745; }
            .url { 
                font-family: monospace; 
                background: #f1f3f4; 
                padding: 8px 12px; 
                border-radius: 4px; 
                margin: 10px 0;
                border: 1px solid #dadce0;
                font-weight: bold;
            }
            .description { color: #666; margin-top: 10px; }
            .example { 
                background: #f8f9fa; 
                padding: 15px; 
                border-radius: 6px; 
                font-family: monospace; 
                font-size: 12px;
                border: 1px solid #e9ecef;
                margin-top: 10px;
                overflow-x: auto;
            }
            .section { margin: 30px 0; }
            .logo { font-size: 24px; font-weight: 800; letter-spacing: 2px; }
            .test-links { background: #e8f5e8; padding: 15px; border-radius: 8px; }
            .test-links a { 
                color: #E50914; 
                text-decoration: none; 
                margin-right: 20px; 
                font-weight: 500;
            }
            .test-links a:hover { text-decoration: underline; }
            h2 { color: #1A1A1A; border-bottom: 2px solid #E50914; padding-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="logo">PRISM ANALYTICS</div>
            <h1>API Documentation</h1>
            <p>Music Data Intelligence Platform API</p>
        </div>

        <div class="section">
            <h2>🏥 Health & Status</h2>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> Health Check</h3>
                <div class="url">/health</div>
                <div class="description">Check if the API is running and healthy</div>
                <div class="example">{"status": "healthy", "service": "music-analytics-api"}</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> API Root</h3>
                <div class="url">/api/v1/</div>
                <div class="description">Get API information and available endpoints</div>
                <div class="example">{
  "service": "Prism Analytics API",
  "version": "1.0.0",
  "status": "running",
  "endpoints": { ... }
}</div>
            </div>
        </div>

        <div class="section">
            <h2>📊 Dashboard Analytics</h2>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> Dashboard Overview</h3>
                <div class="url">/api/v1/dashboard/overview</div>
                <div class="description">Get main dashboard metrics including total streams, artists, platforms, and growth</div>
                <div class="example">{
  "success": true,
  "data": {
    "total_streams": 5455967,
    "unique_artists": 3,
    "active_platforms": 3,
    "weekly_streams": 12345,
    "growth_percentage": 12.5
  }
}</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> Trending Artists</h3>
                <div class="url">/api/v1/artists/trending?limit=10</div>
                <div class="description">Get trending artists with growth metrics</div>
                <div class="example">{
  "success": true,
  "data": [
    {
      "artist_name": "Taylor Swift",
      "total_streams": 2500000,
      "this_week": 50000,
      "growth_percentage": 15.2
    }
  ]
}</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Analytics Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> Platform Analytics</h3>
                <div class="url">/api/v1/analytics/platforms</div>
                <div class="description">Get performance distribution across streaming platforms (Spotify, Apple Music, YouTube, etc.)</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> Geographic Analytics</h3>
                <div class="url">/api/v1/analytics/geographic</div>
                <div class="description">Get performance by country/region with streaming data</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> Time Series Data</h3>
                <div class="url">/api/v1/analytics/timeseries?period=daily&days=30</div>
                <div class="description">Get time series data for charts and trend analysis</div>
                <div class="example">Parameters:
- period: "daily" or "monthly"
- days: number of days to include (default: 30)</div>
            </div>
        </div>

        <div class="section">
            <h2>🎵 Artist Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> Artist Details</h3>
                <div class="url">/api/v1/artists/{artist_id}</div>
                <div class="description">Get detailed information about a specific artist including top tracks and platform breakdown</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> Search Artists</h3>
                <div class="url">/api/v1/search/artists?q=taylor&limit=20</div>
                <div class="description">Search for artists by name</div>
                <div class="example">Parameters:
- q: search query (required)
- limit: max results (default: 20)</div>
            </div>
        </div>

        <div class="section">
            <h2>📄 Report Generation</h2>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span> Generate Wrapped Report</h3>
                <div class="url">/reports/generate/wrapped</div>
                <div class="description">Generate Spotify Wrapped-style annual report</div>
                <div class="example">POST Body:
{
  "artist_id": "SAMPLE_TAYLOR_001",
  "year": 2024,
  "email": "artist@example.com"
}</div>
            </div>

            <div class="endpoint">
                <h3><span class="method post">POST</span> Generate Monthly Report</h3>
                <div class="url">/reports/generate/monthly</div>
                <div class="description">Generate monthly performance report</div>
                <div class="example">POST Body:
{
  "artist_id": "SAMPLE_TAYLOR_001",
  "year": 2024,
  "month": 12
}</div>
            </div>

            <div class="endpoint">
                <h3><span class="method">GET</span> Download Report</h3>
                <div class="url">/reports/download/{filename}</div>
                <div class="description">Download generated report PDF</div>
            </div>

            <div class="endpoint">
                <h3><span class="method post">POST</span> Preview Wrapped Report</h3>
                <div class="url">/reports/preview/wrapped</div>
                <div class="description">Preview Wrapped report data without generating PDF</div>
            </div>
        </div>

        <div class="section test-links">
            <h2>🔗 Quick Test Links</h2>
            <p>Click these links to test the API endpoints directly:</p>
            <div style="margin-top: 15px;">
                <a href="/health" target="_blank">Health Check</a>
                <a href="/api/v1/" target="_blank">API Root</a>
                <a href="/api/v1/dashboard/overview" target="_blank">Dashboard Overview</a>
                <a href="/api/v1/artists/trending?limit=5" target="_blank">Top 5 Trending Artists</a>
                <a href="/api/v1/analytics/platforms" target="_blank">Platform Analytics</a>
                <a href="/api/v1/analytics/geographic" target="_blank">Geographic Analytics</a>
                <a href="/api/v1/search/artists?q=taylor" target="_blank">Search for "Taylor"</a>
            </div>
        </div>

        <div class="section">
            <h2>📝 Standard Response Format</h2>
            <p>All API responses follow this standard format:</p>
            <div class="example">{
  "success": true,
  "data": { ... },
  "timestamp": "2025-05-28T12:41:27.474258"
}

// Error responses:
{
  "success": false,
  "error": "Error message description"
}</div>
        </div>

        <div class="section">
            <h2>🚀 Getting Started</h2>
            <p><strong>1. Frontend Dashboard:</strong> <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></p>
            <p><strong>2. Test API Health:</strong> <a href="/health" target="_blank">/health</a></p>
            <p><strong>3. View Dashboard Data:</strong> <a href="/api/v1/dashboard/overview" target="_blank">/api/v1/dashboard/overview</a></p>
            <p><strong>4. Search Artists:</strong> <a href="/api/v1/search/artists?q=taylor" target="_blank">/api/v1/search/artists?q=taylor</a></p>
        </div>

        <footer style="text-align: center; margin-top: 50px; color: #666; border-top: 1px solid #eee; padding-top: 20px;">
            <p>🎵 <strong>Prism Analytics API</strong> - Music Data Intelligence Platform</p>
            <p>Built with Flask • Powered by Music Data • Version 1.0.0</p>
            <p style="font-size: 12px; margin-top: 10px;">
                📧 Email Reports • 📊 Streaming Analytics • 📱 Multi-Platform Support
            </p>
        </footer>
    </body>
    </html>
    """
    
    return docs_html

@api_bp.route('/artists/trending')
@simple_cache(timeout=600)
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
@simple_cache(timeout=900)
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
@simple_cache(timeout=900)
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
@simple_cache(timeout=300)
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
@simple_cache(timeout=600)
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
            params=(f'%{query}%', limit)
        ).to_dict('records')
        
        return jsonify({
            'success': True,
            'data': results,
            'query': query,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
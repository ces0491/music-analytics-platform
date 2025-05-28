# backend/services/report_generator.py
from flask import Blueprint, jsonify, request, send_file
import pandas as pd
from datetime import datetime, timedelta
import os
from jinja2 import Environment, FileSystemLoader
import pdfkit
from models.database import get_db_engine
from services.email_service import EmailService
import tempfile
import json

reports_bp = Blueprint('reports', __name__)

class ReportGenerator:
    """Generate Spotify Wrapped-style PDF reports"""
    
    def __init__(self):
        self.engine = get_db_engine()
        self.email_service = EmailService()
        
        # Setup Jinja2 templates
        template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        
        # PDF options
        self.pdf_options = {
            'page-size': 'A4',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'no-outline': None,
            'enable-local-file-access': None
        }
    
    def generate_wrapped_report(self, artist_id, year=None):
        """Generate Spotify Wrapped-style annual report"""
        if not year:
            year = datetime.now().year - 1
        
        print(f"🎵 Generating Wrapped report for artist {artist_id}, year {year}")
        
        # Collect artist data
        artist_data = self.get_artist_wrapped_data(artist_id, year)
        
        if not artist_data:
            raise ValueError(f"No data found for artist {artist_id} in {year}")
        
        # Generate HTML from template
        template = self.jinja_env.get_template('wrapped_report.html')
        html_content = template.render(
            artist_data=artist_data,
            year=year,
            generated_date=datetime.now().strftime('%B %d, %Y'),
            brand_colors={
                'primary': '#1A1A1A',
                'accent': '#E50914',
                'secondary': '#333333',
                'background': '#FFFFFF'
            }
        )
        
        # Convert to PDF
        pdf_path = self.html_to_pdf(html_content, f"wrapped_{artist_id}_{year}.pdf")
        
        return {
            'pdf_path': pdf_path,
            'artist_name': artist_data['artist_name'],
            'year': year,
            'summary': artist_data['summary']
        }
    
    def get_artist_wrapped_data(self, artist_id, year):
        """Collect comprehensive artist data for Wrapped report"""
        with self.engine.connect() as conn:
            from sqlalchemy import text
            
            # Artist basic info
            artist_info = conn.execute(text("""
                SELECT * FROM dim_artists WHERE artist_id = :artist_id
            """), {"artist_id": artist_id}).fetchone()
            
            if not artist_info:
                return None
            
            # Total streams for the year
            total_streams = conn.execute(text("""
                SELECT SUM(f.metric_value) as total_streams
                FROM fact_music_metrics f
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = :artist_id
                AND d.year = :year
                AND f.metric_type = 'streams'
            """), {"artist_id": artist_id, "year": year}).scalar() or 0
            
            # Top tracks of the year
            top_tracks = pd.read_sql("""
                SELECT 
                    t.track_name,
                    t.album_name,
                    SUM(f.metric_value) as streams,
                    COUNT(DISTINCT f.country_code) as countries,
                    COUNT(DISTINCT f.platform_id) as platforms
                FROM fact_music_metrics f
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = ? AND d.year = ?
                AND f.metric_type = 'streams'
                GROUP BY t.isrc, t.track_name, t.album_name
                ORDER BY streams DESC
                LIMIT 10
            """, self.engine, params=[artist_id, year]).to_dict('records')
            
            # Monthly growth trend
            monthly_data = pd.read_sql("""
                SELECT 
                    d.month,
                    d.month_name,
                    SUM(f.metric_value) as streams
                FROM fact_music_metrics f
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = ? AND d.year = ?
                AND f.metric_type = 'streams'
                GROUP BY d.month, d.month_name
                ORDER BY d.month
            """, self.engine, params=[artist_id, year]).to_dict('records')
            
            # Platform breakdown
            platform_data = pd.read_sql("""
                SELECT 
                    p.platform_name,
                    SUM(f.metric_value) as streams,
                    ROUND(100.0 * SUM(f.metric_value) / ?, 1) as percentage
                FROM fact_music_metrics f
                JOIN dim_platforms p ON f.platform_id = p.platform_id
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = ? AND d.year = ?
                AND f.metric_type = 'streams'
                GROUP BY p.platform_name
                ORDER BY streams DESC
            """, self.engine, params=[max(1, total_streams), artist_id, year]).to_dict('records')
            
            # Top countries
            country_data = pd.read_sql("""
                SELECT 
                    COALESCE(c.country_name, f.country_code) as country,
                    SUM(f.metric_value) as streams,
                    ROUND(100.0 * SUM(f.metric_value) / ?, 1) as percentage
                FROM fact_music_metrics f
                LEFT JOIN dim_countries c ON f.country_code = c.country_code
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = ? AND d.year = ?
                AND f.metric_type = 'streams'
                AND f.country_code IS NOT NULL
                GROUP BY f.country_code, c.country_name
                ORDER BY streams DESC
                LIMIT 10
            """, self.engine, params=[max(1, total_streams), artist_id, year]).to_dict('records')
            
            # Calculate insights
            peak_month = max(monthly_data, key=lambda x: x['streams']) if monthly_data else None
            top_platform = platform_data[0] if platform_data else None
            
            return {
                'artist_id': artist_id,
                'artist_name': dict(artist_info._mapping)['artist_name'],
                'total_streams': int(total_streams),
                'total_streams_formatted': self.format_number(total_streams),
                'top_tracks': top_tracks,
                'monthly_data': monthly_data,
                'platform_data': platform_data,
                'country_data': country_data,
                'peak_month': peak_month,
                'top_platform': top_platform,
                'unique_countries': len(country_data),
                'summary': {
                    'total_tracks': len(top_tracks),
                    'best_month': peak_month['month_name'] if peak_month else 'N/A',
                    'best_platform': top_platform['platform_name'] if top_platform else 'N/A',
                    'global_reach': len(country_data)
                }
            }
    
    def generate_monthly_report(self, artist_id, year, month):
        """Generate monthly performance report"""
        print(f"📅 Generating monthly report for {artist_id} - {year}/{month}")
        
        monthly_data = self.get_monthly_data(artist_id, year, month)
        
        template = self.jinja_env.get_template('monthly_summary.html')
        html_content = template.render(
            monthly_data=monthly_data,
            year=year,
            month=month,
            generated_date=datetime.now().strftime('%B %d, %Y')
        )
        
        pdf_path = self.html_to_pdf(html_content, f"monthly_{artist_id}_{year}_{month:02d}.pdf")
        
        return {
            'pdf_path': pdf_path,
            'artist_name': monthly_data['artist_name'],
            'period': f"{year}-{month:02d}"
        }
    
    def get_monthly_data(self, artist_id, year, month):
        """Get monthly performance data"""
        # Simplified monthly data collection
        with self.engine.connect() as conn:
            from sqlalchemy import text
            
            artist_info = conn.execute(text("""
                SELECT artist_name FROM dim_artists WHERE artist_id = :artist_id
            """), {"artist_id": artist_id}).fetchone()
            
            total_streams = conn.execute(text("""
                SELECT SUM(f.metric_value) as streams
                FROM fact_music_metrics f
                JOIN dim_tracks t ON f.isrc = t.isrc
                JOIN dim_dates d ON f.date_id = d.date_id
                WHERE t.artist_id = :artist_id
                AND d.year = :year AND d.month = :month
                AND f.metric_type = 'streams'
            """), {"artist_id": artist_id, "year": year, "month": month}).scalar() or 0
            
            return {
                'artist_name': dict(artist_info._mapping)['artist_name'] if artist_info else 'Unknown',
                'total_streams': int(total_streams),
                'total_streams_formatted': self.format_number(total_streams)
            }
    
    def html_to_pdf(self, html_content, filename):
        """Convert HTML to PDF"""
        try:
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            # Generate PDF
            reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports', 'generated')
            os.makedirs(reports_dir, exist_ok=True)
            
            pdf_path = os.path.join(reports_dir, filename)
            
            # Use pdfkit to convert HTML to PDF
            pdfkit.from_file(temp_html_path, pdf_path, options=self.pdf_options)
            
            # Clean up temporary file
            os.unlink(temp_html_path)
            
            print(f"✅ PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"❌ PDF generation failed: {e}")
            raise e
    
    def format_number(self, num):
        """Format large numbers (e.g., 1.2M, 5.3K)"""
        if num >= 1_000_000:
            return f"{num/1_000_000:.1f}M"
        elif num >= 1_000:
            return f"{num/1_000:.1f}K"
        else:
            return str(int(num))

# Initialize report generator
report_generator = ReportGenerator()

# API Endpoints
@reports_bp.route('/generate/wrapped', methods=['POST'])
def generate_wrapped():
    """Generate Wrapped-style report"""
    data = request.json
    artist_id = data.get('artist_id')
    year = data.get('year')
    email_to = data.get('email')
    
    if not artist_id:
        return jsonify({'success': False, 'error': 'artist_id required'}), 400
    
    try:
        result = report_generator.generate_wrapped_report(artist_id, year)
        
        # If email requested, send the report
        if email_to:
            report_generator.email_service.send_wrapped_report(
                email_to, 
                result['pdf_path'], 
                result['artist_name'],
                result['year']
            )
            result['email_sent'] = True
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/generate/monthly', methods=['POST'])
def generate_monthly():
    """Generate monthly report"""
    data = request.json
    artist_id = data.get('artist_id')
    year = data.get('year', datetime.now().year)
    month = data.get('month', datetime.now().month)
    
    if not artist_id:
        return jsonify({'success': False, 'error': 'artist_id required'}), 400
    
    try:
        result = report_generator.generate_monthly_report(artist_id, year, month)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_bp.route('/download/<filename>')
def download_report(filename):
    """Download generated report"""
    reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports', 'generated')
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'Report not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@reports_bp.route('/preview/wrapped', methods=['POST'])
def preview_wrapped():
    """Preview Wrapped report data (without generating PDF)"""
    data = request.json
    artist_id = data.get('artist_id')
    year = data.get('year')
    
    if not artist_id:
        return jsonify({'success': False, 'error': 'artist_id required'}), 400
    
    try:
        artist_data = report_generator.get_artist_wrapped_data(artist_id, year)
        
        if not artist_data:
            return jsonify({'success': False, 'error': 'No data found'}), 404
        
        return jsonify({
            'success': True,
            'data': artist_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
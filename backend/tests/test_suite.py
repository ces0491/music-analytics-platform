# backend/tests/test_suite.py
import pytest
import pandas as pd
import os
import tempfile
from datetime import datetime, timedelta
import json

# Import application modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_database, get_db_engine
from services.data_processor import MusicDataProcessor
from services.api_service import MusicAnalyticsAPI
from services.report_generator import ReportGenerator
from services.email_service import EmailService
from utils.file_handlers import FileHandler
from utils.data_validators import DataValidator

class TestMusicAnalyticsPlatform:
    """Comprehensive test suite for the music analytics platform"""
    
    @pytest.fixture(scope="class")
    def setup_database(self):
        """Setup test database"""
        # Create temporary database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{self.test_db_path}'
        
        # Initialize database
        init_database()
        
        yield
        
        # Cleanup
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    @pytest.fixture
    def sample_csv_data(self):
        """Create sample CSV data for testing"""
        data = {
            'ISRC': ['USRC17607839', 'GBUM71507078', 'TEST123456789'],
            'Artist Name': ['Taylor Swift', 'Ed Sheeran', 'Test Artist'],
            'Track Name': ['Anti-Hero', 'Shape of You', 'Test Track'],
            'Country': ['US', 'GB', 'CA'],
            'Streams': ['1234567', '2345678', '345678']
        }
        
        df = pd.DataFrame(data)
        
        # Create temporary CSV file
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    def test_database_initialization(self, setup_database):
        """Test database initialization"""
        engine = get_db_engine()
        
        # Check if tables exist
        with engine.connect() as conn:
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            
            table_names = [table[0] for table in tables]
            
            required_tables = [
                'dim_artists', 'dim_tracks', 'dim_platforms', 
                'dim_countries', 'fact_music_metrics'
            ]
            
            for table in required_tables:
                assert table in table_names, f"Required table {table} not found"
    
    def test_file_handler(self, sample_csv_data):
        """Test file handling capabilities"""
        handler = FileHandler()
        
        # Test file reading
        df = handler.read_file(sample_csv_data)
        assert df is not None
        assert len(df) == 3
        assert 'ISRC' in df.columns
        
        # Test file analysis
        analysis = handler.analyze_file(sample_csv_data)
        assert analysis['extension'] == '.csv'
        assert analysis['size'] > 0
        assert 'checksum' in analysis
        
        # Test validation
        validation = handler.validate_file_structure(df, sample_csv_data)
        assert validation['valid'] is True
        assert validation['row_count'] == 3
    
    def test_data_validator(self):
        """Test data validation utilities"""
        validator = DataValidator()
        
        # Test ISRC validation
        test_isrcs = pd.Series(['USRC17607839', 'GBUM71507078', 'invalid', ''])
        clean_isrcs = validator.validate_and_clean_isrc(test_isrcs)
        
        assert clean_isrcs.iloc[0] == 'USRC17607839'
        assert clean_isrcs.iloc[1] == 'GBUM71507078'
        assert pd.isna(clean_isrcs.iloc[2])
        
        # Test numeric validation
        test_numbers = pd.Series(['1,234,567', '2345678', '-100', 'invalid'])
        clean_numbers = validator.validate_numeric_values(test_numbers)
        
        assert clean_numbers.iloc[0] == 1234567
        assert clean_numbers.iloc[1] == 2345678
        assert clean_numbers.iloc[2] == 0  # Negative values clipped to 0
        assert pd.isna(clean_numbers.iloc[3])
    
    def test_data_processor(self, setup_database, sample_csv_data):
        """Test data processing functionality"""
        processor = MusicDataProcessor(environment='test')
        
        # Test file processing
        processor.process_file(sample_csv_data)
        
        # Verify data was inserted
        engine = get_db_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            
            # Check if artists were created
            artists = conn.execute(
                text("SELECT COUNT(*) FROM dim_artists")
            ).scalar()
            assert artists > 0
            
            # Check if tracks were created
            tracks = conn.execute(
                text("SELECT COUNT(*) FROM dim_tracks")
            ).scalar()
            assert tracks > 0
    
    def test_api_service(self, setup_database):
        """Test API service functionality"""
        api = MusicAnalyticsAPI()
        
        # Test dashboard overview (with empty database)
        overview = api.get_dashboard_overview()
        assert 'total_streams' in overview
        assert 'unique_artists' in overview
        assert isinstance(overview['total_streams'], int)
        
        # Test platform distribution
        platforms = api.get_platform_distribution()
        assert isinstance(platforms, list)
    
    def test_report_generator(self, setup_database):
        """Test report generation"""
        generator = ReportGenerator()
        
        # Test utility functions
        assert generator.format_number(1234567) == "1.2M"
        assert generator.format_number(1234) == "1.2K"
        assert generator.format_number(123) == "123"
    
    def test_email_service(self):
        """Test email service configuration"""
        email_service = EmailService()
        
        # Test configuration validation (won't actually send)
        config_test = email_service.test_email_configuration()
        # This may fail if SMTP is not configured, which is expected in tests
        assert 'success' in config_test
        assert 'smtp_server' in config_test

class TestPerformanceMonitoring:
    """Performance and health monitoring tests"""
    
    def test_database_performance(self, setup_database):
        """Test database query performance"""
        engine = get_db_engine()
        
        # Test query execution time
        start_time = datetime.now()
        
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) FROM dim_artists"))
            count = result.scalar()
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Query should complete in under 1 second for empty database
        assert execution_time < 1.0
        assert isinstance(count, int)
    
    def test_memory_usage(self):
        """Test memory usage of data processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        large_df = pd.DataFrame({
            'col1': range(10000),
            'col2': ['test'] * 10000,
            'col3': [1.5] * 10000
        })
        
        # Process data
        validator = DataValidator()
        validator.validate_data_quality(large_df)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for this test)
        assert memory_increase < 100
    
    def test_file_processing_speed(self):
        """Test file processing speed"""
        # Create large test file
        large_data = {
            'ISRC': [f'TEST{i:010d}' for i in range(1000)],
            'Artist': [f'Artist {i}' for i in range(1000)],
            'Track': [f'Track {i}' for i in range(1000)],
            'Streams': [1000 + i for i in range(1000)]
        }
        
        df = pd.DataFrame(large_data)
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        df.to_csv(temp_file.name, index=False)
        temp_file.close()
        
        try:
            # Test processing speed
            handler = FileHandler()
            start_time = datetime.now()
            
            result_df = handler.read_file(temp_file.name)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Processing 1000 records should take less than 5 seconds
            assert processing_time < 5.0
            assert len(result_df) == 1000
            
        finally:
            os.unlink(temp_file.name)

class TestAPIEndpoints:
    """Test API endpoints functionality"""
    
    @pytest.fixture
    def client(self):
        """Create Flask test client"""
        from app import create_app
        app = create_app()
        app.config['TESTING'] = True
        
        with app.test_client() as client:
            yield client
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] == 'healthy'
    
    def test_dashboard_endpoint(self, client):
        """Test dashboard overview endpoint"""
        response = client.get('/api/v1/dashboard/overview')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'data' in data
    
    def test_platform_analytics_endpoint(self, client):
        """Test platform analytics endpoint"""
        response = client.get('/api/v1/analytics/platforms')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'data' in data
        assert isinstance(data['data'], list)
    
    def test_artist_search_endpoint(self, client):
        """Test artist search endpoint"""
        response = client.get('/api/v1/search/artists?q=test')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'success' in data
        assert 'data' in data

class TestDataQuality:
    """Test data quality and validation"""
    
    def test_data_completeness(self):
        """Test data completeness validation"""
        # Create test data with missing values
        test_data = pd.DataFrame({
            'isrc': ['TEST123456789', None, 'TEST987654321'],
            'artist': ['Artist 1', 'Artist 2', None],
            'streams': [1000, None, 3000]
        })
        
        validator = DataValidator()
        quality_report = validator.validate_data_quality(test_data)
        
        assert 'quality_score' in quality_report
        assert 'missing_data_percentage' in quality_report
        assert quality_report['missing_data_percentage'] > 0
    
    def test_data_consistency(self):
        """Test data consistency validation"""
        # Create test data with inconsistent formats
        test_data = pd.DataFrame({
            'isrc': ['USRC17607839', 'invalid_isrc', 'GBUM71507078'],
            'country': ['US', 'United States', 'XX'],
            'streams': [1000, -500, 2000]  # Negative value
        })
        
        validator = DataValidator()
        
        # Test ISRC validation
        clean_isrcs = validator.validate_and_clean_isrc(test_data['isrc'])
        valid_isrcs = clean_isrcs.notna().sum()
        assert valid_isrcs == 2  # Only 2 valid ISRCs
        
        # Test country validation
        clean_countries = validator.validate_country_code(test_data['country'])
        assert clean_countries.iloc[0] == 'US'
        assert clean_countries.iloc[1] == 'US'  # Mapped from 'United States'
        
        # Test numeric validation
        clean_numbers = validator.validate_numeric_values(test_data['streams'])
        assert clean_numbers.iloc[1] == 0  # Negative value clipped to 0

# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_metric(self, name: str, value: float, unit: str = 'seconds'):
        """Record a performance metric"""
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            'value': value,
            'unit': unit,
            'timestamp': datetime.now()
        })
    
    def get_average(self, name: str) -> float:
        """Get average value for a metric"""
        if name not in self.metrics:
            return 0.0
        
        values = [m['value'] for m in self.metrics[name]]
        return sum(values) / len(values) if values else 0.0
    
    def get_report(self) -> dict:
        """Get performance report"""
        report = {}
        
        for name, measurements in self.metrics.items():
            if measurements:
                values = [m['value'] for m in measurements]
                report[name] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'unit': measurements[0]['unit']
                }
        
        return report

# Health check utilities
class HealthChecker:
    """Application health monitoring"""
    
    def __init__(self):
        self.checks = {}
    
    def check_database(self) -> dict:
        """Check database connectivity"""
        try:
            engine = get_db_engine()
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT 1")).scalar()
                
            return {
                'status': 'healthy',
                'message': 'Database connection successful',
                'response_time_ms': 0  # Could measure actual response time
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}',
                'response_time_ms': None
            }
    
    def check_disk_space(self) -> dict:
        """Check available disk space"""
        try:
            import shutil
            
            # Check data directory
            total, used, free = shutil.disk_usage('/app/data')
            free_gb = free / (1024**3)
            
            status = 'healthy' if free_gb > 1.0 else 'warning' if free_gb > 0.5 else 'critical'
            
            return {
                'status': status,
                'free_space_gb': round(free_gb, 2),
                'message': f'{free_gb:.2f} GB available'
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'Could not check disk space: {str(e)}'
            }
    
    def check_memory_usage(self) -> dict:
        """Check memory usage"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            status = 'healthy' if memory_percent < 80 else 'warning' if memory_percent < 90 else 'critical'
            
            return {
                'status': status,
                'memory_percent': memory_percent,
                'message': f'{memory_percent}% memory used'
            }
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'Could not check memory: {str(e)}'
            }
    
    def full_health_check(self) -> dict:
        """Perform comprehensive health check"""
        checks = {
            'database': self.check_database(),
            'disk_space': self.check_disk_space(),
            'memory': self.check_memory_usage()
        }
        
        # Determine overall status
        statuses = [check['status'] for check in checks.values()]
        
        if 'critical' in statuses:
            overall_status = 'critical'
        elif 'unhealthy' in statuses:
            overall_status = 'unhealthy'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }

# Configuration for pytest
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

# Test execution script
if __name__ == "__main__":
    import pytest
    
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--cov=services",
        "--cov=utils",
        "--cov=models",
        "--cov-report=html",
        "--cov-report=term-missing"
    ])
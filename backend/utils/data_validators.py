# backend/utils/data_validators.py
import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np

class DataValidator:
    """Comprehensive data validation utilities for music analytics"""
    
    def __init__(self):
        # Column mapping for different data types
        self.column_mappings = {
            'isrc': [
                'isrc', 'track_isrc', 'recording_isrc', 'ISRC', 'track isrc', 
                'Track ISRC', 'Recording ISRC', 'isrc_code', 'isrccode'
            ],
            'artist': [
                'artist', 'artist name', 'performer', 'Artist Name', 'artist_name', 
                'artistname', 'main artist', 'primary artist', 'track artist', 'Artist'
            ],
            'track': [
                'title', 'track', 'track name', 'song', 'Track Title', 'track_name', 
                'trackname', 'song title', 'recording', 'Title', 'Track Name'
            ],
            'album': [
                'album', 'album name', 'release', 'Album Title', 'album_name', 
                'albumname', 'release name', 'Album', 'Album Name'
            ],
            'country': [
                'country', 'country_code', 'territory', 'Country', 'country code', 
                'Territory', 'region', 'storefront name', 'storefront', 'Storefront Name'
            ],
            'value': [
                'streams', 'plays', 'views', 'events', 'units', 'sales', 'revenue', 
                'streams30s', 'Streams', 'Events', 'Views', 'Plays', 'Units', 'Sales',
                'stream count', 'play count', 'view count', 'event count', 'Stream Count'
            ],
            'date': [
                'date', 'period', 'month', 'year', 'timestamp', 'Date', 'Period',
                'reporting_date', 'data_date', 'datestamp', 'Datestamp'
            ]
        }
        
        # ISRC validation pattern
        self.isrc_pattern = re.compile(r'^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$')
        
        # Country code mappings
        self.country_mappings = {
            'USA': 'US', 'UNITED STATES': 'US', 'AMERICA': 'US',
            'UK': 'GB', 'UNITED KINGDOM': 'GB', 'BRITAIN': 'GB',
            'BRASIL': 'BR', 'BRAZIL': 'BR',
            'DEUTSCHLAND': 'DE', 'GERMANY': 'DE',
            'ESPANA': 'ES', 'SPAIN': 'ES',
            'FRANCE': 'FR', 'FRANCIA': 'FR',
            'ITALIA': 'IT', 'ITALY': 'IT',
            'JAPAN': 'JP', 'JAPON': 'JP',
            'KOREA': 'KR', 'SOUTH KOREA': 'KR',
            'MEXICO': 'MX', 'MEJICO': 'MX',
            'NEDERLAND': 'NL', 'NETHERLANDS': 'NL',
            'AUSTRALIA': 'AU', 'AUSTRIALIA': 'AU',
            'CANADA': 'CA', 'KANADA': 'CA',
            'INDIA': 'IN', 'BHARAT': 'IN',
            'CHINA': 'CN', 'PEOPLES REPUBLIC OF CHINA': 'CN',
            'RUSSIA': 'RU', 'RUSSIAN FEDERATION': 'RU'
        }
    
    def find_column_by_mapping(self, df: pd.DataFrame, column_type: str) -> Optional[str]:
        """Find column name using flexible mappings"""
        if df is None or df.empty:
            return None
        
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        for target_col in self.column_mappings.get(column_type, []):
            target_lower = target_col.lower().strip()
            
            # Exact match
            if target_lower in df_columns_lower:
                idx = df_columns_lower.index(target_lower)
                return df.columns[idx]
            
            # Partial match for flexibility
            for actual_col in df.columns:
                if target_lower in actual_col.lower():
                    return actual_col
        
        return None
    
    def validate_and_clean_isrc(self, isrc_series: pd.Series) -> pd.Series:
        """Validate and clean ISRC codes"""
        if isrc_series is None:
            return pd.Series()
        
        # Convert to string and clean
        cleaned = isrc_series.astype(str).str.strip().str.upper()
        
        # Remove common prefixes/suffixes
        cleaned = cleaned.str.replace('ISRC:', '').str.replace('ISRC', '')
        cleaned = cleaned.str.strip()
        
        # Remove dashes and spaces
        cleaned = cleaned.str.replace('-', '').str.replace(' ', '')
        
        # Validate format
        valid_mask = cleaned.str.match(self.isrc_pattern, na=False)
        
        # Set invalid ISRCs to None
        cleaned.loc[~valid_mask] = None
        
        return cleaned
    
    def validate_artist_name(self, artist_series: pd.Series) -> pd.Series:
        """Validate and clean artist names"""
        if artist_series is None:
            return pd.Series()
        
        # Convert to string and clean
        cleaned = artist_series.astype(str).str.strip()
        
        # Remove obvious invalid entries
        invalid_patterns = [
            r'^nan$', r'^null$', r'^none$', r'^unknown$', r'^various$',
            r'^va$', r'^v\.a\.$', r'^compilation$', r'^\s*$'
        ]
        
        for pattern in invalid_patterns:
            mask = cleaned.str.match(pattern, case=False, na=False)
            cleaned.loc[mask] = None
        
        # Clean common issues
        cleaned = cleaned.str.replace(r'\s+', ' ', regex=True)  # Multiple spaces
        cleaned = cleaned.str.replace(r'[^\w\s\-\.\(\)\&\']', '', regex=True)  # Invalid chars
        
        return cleaned
    
    def validate_track_name(self, track_series: pd.Series) -> pd.Series:
        """Validate and clean track names"""
        if track_series is None:
            return pd.Series()
        
        # Convert to string and clean
        cleaned = track_series.astype(str).str.strip()
        
        # Remove obvious invalid entries  
        invalid_patterns = [
            r'^nan$', r'^null$', r'^none$', r'^unknown$', r'^untitled$',
            r'^track \d+$', r'^\s*$'
        ]
        
        for pattern in invalid_patterns:
            mask = cleaned.str.match(pattern, case=False, na=False)
            cleaned.loc[mask] = None
        
        # Clean common issues
        cleaned = cleaned.str.replace(r'\s+', ' ', regex=True)
        
        # Remove version info in parentheses if it makes the title too long
        cleaned = cleaned.apply(lambda x: self._clean_track_title(x) if pd.notna(x) else x)
        
        return cleaned
    
    def _clean_track_title(self, title: str) -> str:
        """Clean individual track title"""
        if not title:
            return title
        
        # Remove excessive parenthetical information
        # Keep first parenthetical, remove others if title becomes too long
        parts = re.split(r'(\([^)]*\))', title)
        
        if len(parts) > 1:
            main_title = parts[0].strip()
            first_paren = parts[1] if len(parts) > 1 else ''
            
            if len(main_title) > 10:  # Main title is substantial
                return f"{main_title} {first_paren}".strip()
        
        return title
    
    def validate_country_code(self, country_series: pd.Series) -> pd.Series:
        """Validate and standardize country codes"""
        if country_series is None:
            return pd.Series()
        
        # Convert to string and clean
        cleaned = country_series.astype(str).str.strip().str.upper()
        
        # Apply country mappings
        for full_name, code in self.country_mappings.items():
            mask = cleaned == full_name
            cleaned.loc[mask] = code
        
        # Validate country codes (should be 2 characters)
        valid_mask = cleaned.str.len() == 2
        cleaned.loc[~valid_mask] = 'XX'  # Unknown country
        
        return cleaned
    
    def validate_numeric_values(self, value_series: pd.Series) -> pd.Series:
        """Validate and clean numeric values (streams, plays, etc.)"""
        if value_series is None:
            return pd.Series()
        
        # Convert to string first to handle mixed types
        cleaned = value_series.astype(str).str.strip()
        
        # Remove common formatting
        cleaned = cleaned.str.replace(',', '')  # Thousands separator
        cleaned = cleaned.str.replace('$', '')  # Dollar signs
        cleaned = cleaned.str.replace('€', '')  # Euro signs
        cleaned = cleaned.str.replace('£', '')  # Pound signs
        
        # Convert to numeric
        numeric_values = pd.to_numeric(cleaned, errors='coerce')
        
        # Set negative values to 0
        numeric_values = numeric_values.clip(lower=0)
        
        # Set extremely large values to NaN (likely errors)
        max_reasonable_value = 1e12  # 1 trillion
        numeric_values.loc[numeric_values > max_reasonable_value] = None
        
        return numeric_values
    
    def validate_date_values(self, date_series: pd.Series) -> pd.Series:
        """Validate and standardize date values"""
        if date_series is None:
            return pd.Series()
        
        # Try to parse dates with multiple formats
        date_formats = [
            '%Y-%m-%d', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y-%m', '%Y/%m', '%m/%Y',
            '%Y%m%d', '%Y%m',
            '%d-%m-%Y', '%d.%m.%Y'
        ]
        
        parsed_dates = pd.Series(index=date_series.index, dtype='datetime64[ns]')
        
        for fmt in date_formats:
            unparsed_mask = parsed_dates.isna()
            if not unparsed_mask.any():
                break
                
            try:
                parsed_dates.loc[unparsed_mask] = pd.to_datetime(
                    date_series.loc[unparsed_mask], 
                    format=fmt, 
                    errors='coerce'
                )
            except:
                continue
        
        # If still unparsed, try pandas' flexible parser
        unparsed_mask = parsed_dates.isna()
        if unparsed_mask.any():
            try:
                parsed_dates.loc[unparsed_mask] = pd.to_datetime(
                    date_series.loc[unparsed_mask], 
                    errors='coerce'
                )
            except:
                pass
        
        return parsed_dates
    
    def clean_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean metadata file comprehensively"""
        if df is None or df.empty:
            return df
        
        df_clean = df.copy()
        
        # Standardize column names
        df_clean.columns = [col.strip() for col in df_clean.columns]
        
        # Find and clean key columns
        isrc_col = self.find_column_by_mapping(df_clean, 'isrc')
        if isrc_col:
            df_clean[isrc_col] = self.validate_and_clean_isrc(df_clean[isrc_col])
        
        artist_col = self.find_column_by_mapping(df_clean, 'artist')
        if artist_col:
            df_clean[artist_col] = self.validate_artist_name(df_clean[artist_col])
        
        track_col = self.find_column_by_mapping(df_clean, 'track')
        if track_col:
            df_clean[track_col] = self.validate_track_name(df_clean[track_col])
        
        country_col = self.find_column_by_mapping(df_clean, 'country')
        if country_col:
            df_clean[country_col] = self.validate_country_code(df_clean[country_col])
        
        # Clean numeric columns
        for col in df_clean.select_dtypes(include=[np.number]).columns:
            df_clean[col] = self.validate_numeric_values(df_clean[col])
        
        return df_clean
    
    def clean_usage_data(self, df: pd.DataFrame, platform_id: str) -> pd.DataFrame:
        """Clean usage/metrics data"""
        if df is None or df.empty:
            return df
        
        df_clean = df.copy()
        
        # Find and clean ISRC
        isrc_col = self.find_column_by_mapping(df_clean, 'isrc')
        if isrc_col:
            df_clean['isrc'] = self.validate_and_clean_isrc(df_clean[isrc_col])
        
        # Find and clean country
        country_col = self.find_column_by_mapping(df_clean, 'country')
        if country_col:
            df_clean['country'] = self.validate_country_code(df_clean[country_col])
        
        # Find and clean metric value
        value_col = self.find_column_by_mapping(df_clean, 'value')
        if value_col:
            df_clean['metric_value'] = self.validate_numeric_values(df_clean[value_col])
        
        # Determine metric type based on platform
        df_clean['metric_type'] = self.determine_metric_type(platform_id, df_clean.columns)
        
        # Remove rows with invalid core data
        if 'metric_value' in df_clean.columns:
            df_clean = df_clean.dropna(subset=['metric_value'])
            df_clean = df_clean[df_clean['metric_value'] > 0]
        
        return df_clean
    
    def clean_apple_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean Apple Music specific data"""
        if df is None or df.empty:
            return df
        
        df_clean = df.copy()
        
        # Clean Apple identifier
        if 'apple_id' in df_clean.columns:
            df_clean['apple_id'] = df_clean['apple_id'].astype(str).str.strip()
            # Remove invalid Apple IDs
            df_clean = df_clean[df_clean['apple_id'] != 'nan']
            df_clean = df_clean[df_clean['apple_id'].str.len() > 0]
        
        # Clean country (storefront)
        if 'country' in df_clean.columns:
            df_clean['country'] = self.validate_country_code(df_clean['country'])
        
        # Clean metric value
        if 'metric_value' in df_clean.columns:
            df_clean['metric_value'] = self.validate_numeric_values(df_clean['metric_value'])
            df_clean = df_clean.dropna(subset=['metric_value'])
            df_clean = df_clean[df_clean['metric_value'] > 0]
        
        # Set platform-specific values
        df_clean['platform_id'] = 'apl-apple-music'
        df_clean['metric_type'] = 'streams'
        
        return df_clean
    
    def determine_metric_type(self, platform_id: str, columns: List[str]) -> str:
        """Determine metric type based on platform and columns"""
        col_text = ' '.join([str(col).lower() for col in columns])
        
        # Check column names for hints
        if any(word in col_text for word in ['stream', 'listening']):
            return 'streams'
        elif any(word in col_text for word in ['view', 'watch']):
            return 'views'
        elif any(word in col_text for word in ['event', 'interaction', 'engagement']):
            return 'events'
        elif any(word in col_text for word in ['sale', 'unit', 'purchase']):
            return 'sales'
        elif any(word in col_text for word in ['play', 'listen']):
            return 'plays'
        
        # Use platform defaults
        platform_defaults = {
            'spo-spotify': 'streams',
            'apl-apple-music': 'streams', 
            'apl-itunes': 'sales',
            'amz-amazon': 'streams',
            'dzr-deezer': 'streams',
            'tdl-tidal': 'streams',
            'pnd-pandora': 'streams',
            'scu-soundcloud': 'plays',
            'ytb-youtube': 'views',
            'vvo-vevo': 'views',
            'fbk-facebook': 'events',
            'ins-instagram': 'events',
            'ttk-tiktok': 'views',
            'awa-awa': 'streams',
            'boo-boomplay': 'streams',
            'jio-jiosaavn': 'streams',
            'gna-gaana': 'streams',
            'ang-anghami': 'streams'
        }
        
        return platform_defaults.get(platform_id, 'streams')
    
    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive data quality assessment"""
        if df is None or df.empty:
            return {'quality_score': 0, 'issues': ['Dataset is empty']}
        
        quality_metrics = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_data_percentage': 0,
            'duplicate_rows': 0,
            'invalid_isrcs': 0,
            'invalid_countries': 0,
            'negative_values': 0,
            'quality_score': 0,
            'issues': [],
            'warnings': []
        }
        
        # Check missing data
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        quality_metrics['missing_data_percentage'] = (missing_cells / total_cells) * 100
        
        # Check duplicates
        quality_metrics['duplicate_rows'] = df.duplicated().sum()
        
        # Check ISRC quality
        isrc_col = self.find_column_by_mapping(df, 'isrc')
        if isrc_col:
            isrc_series = df[isrc_col].astype(str).str.strip().str.upper()
            valid_isrcs = isrc_series.str.match(self.isrc_pattern, na=False)
            quality_metrics['invalid_isrcs'] = (~valid_isrcs).sum()
        
        # Check country codes
        country_col = self.find_column_by_mapping(df, 'country')
        if country_col:
            country_series = df[country_col].astype(str).str.strip()
            valid_countries = country_series.str.len() == 2
            quality_metrics['invalid_countries'] = (~valid_countries).sum()
        
        # Check for negative values in numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            negative_count = (df[col] < 0).sum()
            quality_metrics['negative_values'] += negative_count
        
        # Calculate overall quality score (0-100)
        score = 100
        
        # Deduct points for issues
        if quality_metrics['missing_data_percentage'] > 10:
            score -= min(20, quality_metrics['missing_data_percentage'])
            quality_metrics['issues'].append(f"High missing data: {quality_metrics['missing_data_percentage']:.1f}%")
        
        if quality_metrics['duplicate_rows'] > 0:
            dup_pct = (quality_metrics['duplicate_rows'] / len(df)) * 100
            score -= min(10, dup_pct)
            quality_metrics['warnings'].append(f"Duplicate rows: {quality_metrics['duplicate_rows']}")
        
        if quality_metrics['invalid_isrcs'] > 0:
            invalid_pct = (quality_metrics['invalid_isrcs'] / len(df)) * 100
            score -= min(15, invalid_pct)
            quality_metrics['issues'].append(f"Invalid ISRCs: {quality_metrics['invalid_isrcs']}")
        
        if quality_metrics['invalid_countries'] > 0:
            invalid_pct = (quality_metrics['invalid_countries'] / len(df)) * 100
            score -= min(10, invalid_pct)
            quality_metrics['warnings'].append(f"Invalid countries: {quality_metrics['invalid_countries']}")
        
        if quality_metrics['negative_values'] > 0:
            score -= 5
            quality_metrics['warnings'].append(f"Negative values: {quality_metrics['negative_values']}")
        
        quality_metrics['quality_score'] = max(0, score)
        
        return quality_metrics

# Example usage and testing
if __name__ == "__main__":
    validator = DataValidator()
    
    # Test with sample data
    sample_data = {
        'ISRC': ['USRC17607839', 'GBUM71507078', 'invalid_isrc', 'FR-AB1-23-45678'],
        'Artist Name': ['Taylor Swift', 'Ed Sheeran', '', 'Various Artists'],
        'Track Name': ['Anti-Hero', 'Shape of You', 'Unknown', 'Track 1'],
        'Country': ['US', 'United Kingdom', 'Deutschland', 'XX'],
        'Streams': ['1,234,567', '2345678', '-100', '99999999999999']
    }
    
    df = pd.DataFrame(sample_data)
    print("Original data:")
    print(df)
    
    # Test validation
    quality_report = validator.validate_data_quality(df)
    print(f"\nQuality Score: {quality_report['quality_score']}")
    print(f"Issues: {quality_report['issues']}")
    print(f"Warnings: {quality_report['warnings']}")
    
    # Test cleaning
    df_clean = validator.clean_metadata(df)
    print("\nCleaned data:")
    print(df_clean)
# backend/utils/file_handlers.py
import pandas as pd
import os
import re
from typing import Dict, List, Optional, Union
import chardet
from pathlib import Path
import hashlib
from datetime import datetime

class FileHandler:
    """Comprehensive file handling utilities for music data processing"""
    
    def __init__(self):
        self.supported_extensions = ['.csv', '.txt', '.tsv', '.xlsx', '.xls']
        self.encoding_priority = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
        
    def discover_files(self, folder_path: str) -> List[str]:
        """Discover all supported data files in folder and subfolders"""
        files = []
        
        if not os.path.exists(folder_path):
            print(f"❌ Folder not found: {folder_path}")
            return files
        
        for root, dirs, filenames in os.walk(folder_path):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in self.supported_extensions):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        
        print(f"📁 Discovered {len(files)} supported files")
        return sorted(files)
    
    def analyze_file(self, file_path: str) -> Dict:
        """Analyze file and extract metadata"""
        file_info = {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)),
            'checksum': self.calculate_checksum(file_path),
            'platform': self.detect_platform_from_path(file_path),
            'type': None,
            'date_folder': self.extract_date_from_path(file_path),
            'encoding': None
        }
        
        # Detect encoding for text files
        if file_info['extension'] in ['.csv', '.txt', '.tsv']:
            file_info['encoding'] = self.detect_encoding(file_path)
        
        return file_info
    
    def read_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read file with automatic format detection and encoding handling"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.xlsx', '.xls']:
                return self.read_excel_file(file_path)
            else:
                return self.read_text_file(file_path)
                
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            return None
    
    def read_excel_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read Excel files with error handling"""
        try:
            # Try reading the first sheet
            df = pd.read_excel(file_path, engine='openpyxl')
            
            if df.empty:
                # Try reading all sheets and combine
                xl_file = pd.ExcelFile(file_path)
                dfs = []
                for sheet_name in xl_file.sheet_names:
                    sheet_df = pd.read_excel(file_path, sheet_name=sheet_name)
                    if not sheet_df.empty:
                        dfs.append(sheet_df)
                
                if dfs:
                    df = pd.concat(dfs, ignore_index=True)
            
            return self.clean_dataframe(df)
            
        except Exception as e:
            print(f"❌ Excel read error: {e}")
            return None
    
    def read_text_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read text files (CSV, TSV, etc.) with encoding detection"""
        encoding = self.detect_encoding(file_path)
        
        # Try different separators
        separators = [',', '\t', ';', '|', '~']
        
        for sep in separators:
            try:
                df = pd.read_csv(
                    file_path,
                    sep=sep,
                    encoding=encoding,
                    low_memory=False,
                    na_values=['', 'NULL', 'null', 'N/A', 'n/a', '#N/A'],
                    keep_default_na=True
                )
                
                # Check if separation worked well
                if len(df.columns) > 1 and len(df) > 0:
                    return self.clean_dataframe(df)
                    
            except Exception as e:
                continue
        
        # If all separators fail, try with default settings
        try:
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            return self.clean_dataframe(df)
        except Exception as e:
            print(f"❌ Text file read error: {e}")
            return None
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize dataframe"""
        if df is None or df.empty:
            return df
        
        # Clean column names
        df.columns = [str(col).strip() for col in df.columns]
        
        # Remove completely empty rows and columns  
        df = df.dropna(how='all')
        df = df.loc[:, df.notna().any()]
        
        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' strings with actual NaN
            df[col] = df[col].replace('nan', pd.NA)
        
        return df
    
    def detect_encoding(self, file_path: str) -> str:
        """Detect file encoding"""
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                detected_encoding = result['encoding']
                
                # Validate detected encoding
                if detected_encoding and result['confidence'] > 0.7:
                    return detected_encoding
        except:
            pass
        
        # Fallback to trying common encodings
        for encoding in self.encoding_priority:
            try:
                with open(file_path, 'r', encoding=encoding) as file:
                    file.read(1000)  # Try to read first 1000 chars
                return encoding
            except:
                continue
        
        return 'utf-8'  # Final fallback
    
    def detect_platform_from_path(self, file_path: str) -> str:
        """Detect platform from file path and name"""
        path_lower = file_path.lower()
        file_name_lower = os.path.basename(file_path).lower()
        
        platform_keywords = {
            'spo-spotify': ['spotify', 'spo'],
            'apl-apple-music': ['apple', 'apl', 'itunes'],
            'apl-itunes': ['itunes'],
            'amz-amazon': ['amazon', 'amz'],
            'ytb-youtube': ['youtube', 'ytb', 'yt'],
            'dzr-deezer': ['deezer', 'dzr'],
            'tdl-tidal': ['tidal', 'tdl'],
            'pnd-pandora': ['pandora', 'pnd'],
            'scu-soundcloud': ['soundcloud', 'scu'],
            'vvo-vevo': ['vevo', 'vvo'],
            'fbk-facebook': ['facebook', 'fbk', 'fb'],
            'ins-instagram': ['instagram', 'ins', 'ig'],
            'ttk-tiktok': ['tiktok', 'ttk'],
            'awa-awa': ['awa'],
            'boo-boomplay': ['boomplay', 'boo'],
            'jio-jiosaavn': ['jiosaavn', 'jio'],
            'gna-gaana': ['gaana', 'gna'],
            'ang-anghami': ['anghami', 'ang']
        }
        
        # Check file path and name for platform keywords
        for platform_id, keywords in platform_keywords.items():
            for keyword in keywords:
                if keyword in path_lower or keyword in file_name_lower:
                    return platform_id
        
        # Try to extract from folder structure
        path_parts = Path(file_path).parts
        for part in path_parts:
            part_clean = part.lower().replace('-', '').replace('_', '')
            for platform_id, keywords in platform_keywords.items():
                for keyword in keywords:
                    if keyword in part_clean:
                        return platform_id
        
        return 'unknown'
    
    def extract_date_from_path(self, file_path: str) -> Optional[str]:
        """Extract date information from file path"""
        # Look for YYYYMM or YYYY-MM patterns
        date_patterns = [
            r'(\d{4})(\d{2})',      # YYYYMM
            r'(\d{4})-(\d{2})',     # YYYY-MM
            r'(\d{4})_(\d{2})',     # YYYY_MM
            r'(\d{4})\.(\d{2})',    # YYYY.MM
        ]
        
        path_str = str(file_path)
        
        for pattern in date_patterns:
            matches = re.findall(pattern, path_str)
            if matches:
                year, month = matches[-1]  # Take the last match
                try:
                    # Validate date
                    if 2020 <= int(year) <= 2030 and 1 <= int(month) <= 12:
                        return f"{year}{month}"
                except:
                    continue
        
        return None
    
    def calculate_checksum(self, file_path: str) -> str:
        """Calculate MD5 checksum of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
    
    def validate_file_structure(self, df: pd.DataFrame, file_path: str) -> Dict:
        """Validate file structure and return quality metrics"""
        if df is None or df.empty:
            return {'valid': False, 'issues': ['File is empty or unreadable']}
        
        issues = []
        warnings = []
        
        # Check for basic requirements
        if len(df.columns) < 2:
            issues.append('File has too few columns')
        
        if len(df) < 1:
            issues.append('File has no data rows')
        
        # Check for completely empty columns
        empty_cols = df.columns[df.isnull().all()].tolist()
        if empty_cols:
            warnings.append(f'Empty columns detected: {empty_cols}')
        
        # Check data quality
        missing_data_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        if missing_data_pct > 50:
            warnings.append(f'High missing data percentage: {missing_data_pct:.1f}%')
        
        # Check for potential encoding issues
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            if df[col].astype(str).str.contains('â€™|â€œ|â€|Ã¡|Ã©').any():
                warnings.append(f'Potential encoding issues in column: {col}')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'row_count': len(df),
            'column_count': len(df.columns),
            'missing_data_percentage': missing_data_pct,
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024)
        }
    
    def get_file_sample(self, file_path: str, n_rows: int = 5) -> Dict:
        """Get a sample of the file for preview"""
        try:
            df = self.read_file(file_path)
            if df is None or df.empty:
                return {'error': 'Could not read file'}
            
            sample = df.head(n_rows).to_dict(orient='records')
            
            return {
                'columns': list(df.columns),
                'sample_data': sample,
                'total_rows': len(df),
                'total_columns': len(df.columns)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def batch_process_files(self, file_paths: List[str], callback_func) -> Dict:
        """Process multiple files with progress tracking"""
        results = {
            'processed': [],
            'failed': [],
            'total_files': len(file_paths),
            'total_records': 0
        }
        
        for i, file_path in enumerate(file_paths):
            try:
                print(f"📁 Processing file {i+1}/{len(file_paths)}: {os.path.basename(file_path)}")
                
                file_result = callback_func(file_path)
                
                if file_result.get('success', False):
                    results['processed'].append({
                        'file': file_path,
                        'records': file_result.get('records', 0)
                    })
                    results['total_records'] += file_result.get('records', 0)
                else:
                    results['failed'].append({
                        'file': file_path,
                        'error': file_result.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'file': file_path,
                    'error': str(e)
                })
        
        return results

# Example usage and testing
if __name__ == "__main__":
    handler = FileHandler()
    
    # Test file discovery
    files = handler.discover_files("./data/raw")
    print(f"Found {len(files)} files")
    
    # Test file analysis
    for file_path in files[:3]:  # Test first 3 files
        analysis = handler.analyze_file(file_path) 
        print(f"\nFile: {analysis['name']}")
        print(f"Platform: {analysis['platform']}")
        print(f"Date: {analysis['date_folder']}")
        print(f"Size: {analysis['size']} bytes")
        
        # Test file reading
        df = handler.read_file(file_path)
        if df is not None:
            print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
            
            # Test validation
            validation = handler.validate_file_structure(df, file_path)
            print(f"Valid: {validation['valid']}")
            if validation['issues']:
                print(f"Issues: {validation['issues']}")
        else:
            print("Failed to read file")
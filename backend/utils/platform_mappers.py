# backend/utils/platform_mappers.py
class PlatformMapper:
    """Map platform identifiers and standardize platform data"""
    
    def __init__(self):
        self.platform_mappings = {
            'spotify': 'spo-spotify',
            'apple': 'apl-apple-music',
            'apple music': 'apl-apple-music',
            'itunes': 'apl-itunes',
            'youtube': 'ytb-youtube',
            'amazon': 'amz-amazon',
            'deezer': 'dzr-deezer',
            'tidal': 'tdl-tidal',
            'pandora': 'pnd-pandora',
            'soundcloud': 'scu-soundcloud'
        }
    
    def get_platform_id(self, platform_name):
        """Get standardized platform ID"""
        clean_name = platform_name.lower().strip()
        return self.platform_mappings.get(clean_name, 'unknown')
    
    def get_platform_category(self, platform_id):
        """Get platform category"""
        categories = {
            'spo-spotify': 'streaming',
            'apl-apple-music': 'streaming',
            'apl-itunes': 'sales',
            'ytb-youtube': 'video',
            'amz-amazon': 'streaming'
        }
        return categories.get(platform_id, 'streaming')
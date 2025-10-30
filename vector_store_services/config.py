"""
Configuration for Vector Store Services

This module contains configuration settings for vector store services.
"""

import os
from typing import Dict, Any


class VectorStoreConfig:
    """Configuration class for vector store services"""
    
    # Qdrant Configuration
    QDRANT_URL = os.getenv('QDRANT_URL', 'localhost:6333')
    QDRANT_API_KEY = os.getenv('QDRANT_API_KEY', None)
    
    # Default Collection Settings
    DEFAULT_COLLECTION_NAME = os.getenv('DEFAULT_COLLECTION_NAME', 'default_collection')
    DEFAULT_VECTOR_SIZE = int(os.getenv('DEFAULT_VECTOR_SIZE', '384'))
    DEFAULT_DISTANCE = os.getenv('DEFAULT_DISTANCE', 'Cosine')
    
    # Search Settings
    DEFAULT_SEARCH_LIMIT = int(os.getenv('DEFAULT_SEARCH_LIMIT', '10'))
    DEFAULT_SCORE_THRESHOLD = float(os.getenv('DEFAULT_SCORE_THRESHOLD', '0.0'))
    
    # Batch Settings
    DEFAULT_BATCH_SIZE = int(os.getenv('DEFAULT_BATCH_SIZE', '100'))
    
    @classmethod
    def get_qdrant_config(cls) -> Dict[str, Any]:
        """Get Qdrant configuration dictionary"""
        return {
            'url': cls.QDRANT_URL,
            'api_key': cls.QDRANT_API_KEY,
            'collection_name': cls.DEFAULT_COLLECTION_NAME,
            'vector_size': cls.DEFAULT_VECTOR_SIZE
        }
    
    @classmethod
    def get_search_config(cls) -> Dict[str, Any]:
        """Get search configuration dictionary"""
        return {
            'limit': cls.DEFAULT_SEARCH_LIMIT,
            'score_threshold': cls.DEFAULT_SCORE_THRESHOLD
        }

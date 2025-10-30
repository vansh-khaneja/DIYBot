"""
Qdrant Vector Store Service

This module provides utilities for interacting with Qdrant vector database.
Supports basic operations like:
- Collection management (create, delete, list)
- Embedding operations (add, delete, get)
- Similarity search with metadata filtering
- Batch operations for efficiency
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import uuid
from datetime import datetime

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
except ImportError:
    QdrantClient = None
    models = None
    Distance = None
    VectorParams = None
    PointStruct = None
    Filter = None
    FieldCondition = None
    MatchValue = None

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingPayload:
    """Data structure for embedding payload with metadata"""
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        # Add timestamp if not present
        if 'timestamp' not in self.metadata:
            self.metadata['timestamp'] = datetime.now().isoformat()


@dataclass
class SearchResult:
    """Data structure for search results"""
    id: str
    score: float
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class QdrantService:
    """Service class for Qdrant vector database operations"""
    
    def __init__(self, 
                 url: str = None, 
                 api_key: str = None,
                 collection_name: str = "default_collection",
                 vector_size: int = 384):
        """
        Initialize Qdrant service
        
        Args:
            url: Qdrant server URL (default: localhost:6333)
            api_key: API key for authentication (optional)
            collection_name: Default collection name
            vector_size: Vector dimension size
        """
        if QdrantClient is None:
            raise ImportError("qdrant-client is not installed. Install it with: pip install qdrant-client")
        
        self.url = url or os.getenv('QDRANT_URL', 'localhost:6333')
        self.api_key = api_key or os.getenv('QDRANT_API_KEY')
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        # Initialize client
        self.client = self._initialize_client()
        
        logger.info(f"QdrantService initialized with URL: {self.url}")
    
    def _initialize_client(self) -> QdrantClient:
        """Initialize Qdrant client with proper configuration"""
        try:
            # Handle different URL formats
            if self.url.startswith('https://'):
                # Already a full HTTPS URL (Qdrant Cloud)
                clean_url = self.url
            elif self.url.startswith('http://'):
                # HTTP URL (local or custom)
                clean_url = self.url
            else:
                # Just domain name - determine if it's cloud or local
                if 'qdrant.tech' in self.url or 'qdrant.cloud' in self.url:
                    # Qdrant Cloud - add https://
                    clean_url = f"https://{self.url}"
                else:
                    # Local Qdrant - check if port already included
                    if ':6333' in self.url:
                        clean_url = f"http://{self.url}"
                    else:
                        clean_url = f"http://{self.url}:6333"
            
            if self.api_key:
                # Use API key authentication
                client = QdrantClient(
                    url=clean_url,
                    api_key=self.api_key
                )
            else:
                # No API key (local only)
                client = QdrantClient(url=clean_url)
            
            # Test connection
            client.get_collections()
            logger.info(f"Successfully connected to Qdrant at {clean_url}")
            return client
            
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            # Don't raise error during startup - let it fail gracefully
            logger.warning("Qdrant connection failed - service will be unavailable until connection is established")
            return None
    
    def _check_client(self) -> bool:
        """Check if client is available"""
        if self.client is None:
            logger.error("Qdrant client is not available - connection failed")
            return False
        return True

    def create_collection(self, 
                         collection_name: str = None, 
                         vector_size: int = None,
                         distance: str = "Cosine") -> bool:
        """
        Create a new collection
        
        Args:
            collection_name: Name of the collection
            vector_size: Vector dimension size
            distance: Distance metric (Cosine, Dot, Euclid)
            
        Returns:
            bool: True if collection created successfully
        """
        if not self._check_client():
            return False
            
        collection_name = collection_name or self.collection_name
        vector_size = vector_size or self.vector_size
        
        try:
            # Check if collection already exists
            collections = self.client.get_collections()
            existing_names = [col.name for col in collections.collections]
            
            if collection_name in existing_names:
                logger.warning(f"Collection '{collection_name}' already exists")
                return True
            
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=getattr(Distance, distance.upper())
                )
            )
            
            logger.info(f"Collection '{collection_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection '{collection_name}': {e}")
            return False
    
    def delete_collection(self, collection_name: str = None) -> bool:
        """
        Delete a collection
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            bool: True if collection deleted successfully
        """
        collection_name = collection_name or self.collection_name
        
        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete collection '{collection_name}': {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        List all collections
        
        Returns:
            List[str]: List of collection names
        """
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def add_embedding(self, 
                     embedding_payload: EmbeddingPayload,
                     collection_name: str = None) -> bool:
        """
        Add a single embedding to the collection
        
        Args:
            embedding_payload: EmbeddingPayload object with vector and metadata
            collection_name: Target collection name
            
        Returns:
            bool: True if embedding added successfully
        """
        collection_name = collection_name or self.collection_name
        
        try:
            # Ensure collection exists
            if not self._collection_exists(collection_name):
                self.create_collection(collection_name)
            
            # Ensure ID is UUID format for Qdrant Cloud compatibility
            point_id = embedding_payload.id
            if not self._is_valid_uuid(point_id):
                point_id = str(uuid.uuid4())
                logger.info(f"Converted string ID '{embedding_payload.id}' to UUID: {point_id}")
            
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding_payload.vector,
                payload={
                    **embedding_payload.payload,
                    **embedding_payload.metadata
                }
            )
            
            # Upsert point
            self.client.upsert(
                collection_name=collection_name,
                points=[point]
            )
            
            logger.info(f"Embedding '{embedding_payload.id}' added to collection '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embedding '{embedding_payload.id}': {e}")
            return False
    
    def add_embeddings_batch(self, 
                            embedding_payloads: List[EmbeddingPayload],
                            collection_name: str = None,
                            batch_size: int = 100) -> bool:
        """
        Add multiple embeddings in batches
        
        Args:
            embedding_payloads: List of EmbeddingPayload objects
            collection_name: Target collection name
            batch_size: Number of embeddings per batch
            
        Returns:
            bool: True if all embeddings added successfully
        """
        collection_name = collection_name or self.collection_name
        
        try:
            # Ensure collection exists
            if not self._collection_exists(collection_name):
                self.create_collection(collection_name)
            
            # Process in batches
            for i in range(0, len(embedding_payloads), batch_size):
                batch = embedding_payloads[i:i + batch_size]
                points = []
                
                for payload in batch:
                    point = PointStruct(
                        id=payload.id,
                        vector=payload.vector,
                        payload={
                            **payload.payload,
                            **payload.metadata
                        }
                    )
                    points.append(point)
                
                # Upsert batch
                self.client.upsert(
                    collection_name=collection_name,
                    points=points
                )
                
                logger.info(f"Batch {i//batch_size + 1}: Added {len(points)} embeddings")
            
            logger.info(f"Successfully added {len(embedding_payloads)} embeddings to '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings batch: {e}")
            return False
    
    def delete_embedding(self, 
                        embedding_id: str,
                        collection_name: str = None) -> bool:
        """
        Delete an embedding by ID
        
        Args:
            embedding_id: ID of the embedding to delete
            collection_name: Target collection name
            
        Returns:
            bool: True if embedding deleted successfully
        """
        collection_name = collection_name or self.collection_name
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(points=[embedding_id])
            )
            
            logger.info(f"Embedding '{embedding_id}' deleted from '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete embedding '{embedding_id}': {e}")
            return False
    
    def get_embedding(self, 
                     embedding_id: str,
                     collection_name: str = None) -> Optional[EmbeddingPayload]:
        """
        Get an embedding by ID
        
        Args:
            embedding_id: ID of the embedding to retrieve
            collection_name: Target collection name
            
        Returns:
            EmbeddingPayload or None if not found
        """
        collection_name = collection_name or self.collection_name
        
        try:
            result = self.client.retrieve(
                collection_name=collection_name,
                ids=[embedding_id],
                with_payload=True,
                with_vectors=True
            )
            
            if result:
                point = result[0]
                return EmbeddingPayload(
                    id=point.id,
                    vector=point.vector,
                    payload=point.payload,
                    metadata=point.payload
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get embedding '{embedding_id}': {e}")
            return None
    
    def search_similar(self, 
                      query_vector: List[float],
                      collection_name: str = None,
                      limit: int = 10,
                      score_threshold: float = 0.0,
                      metadata_filter: Optional[Dict[str, Any]] = None) -> List[SearchResult]:
        """
        Search for similar embeddings
        
        Args:
            query_vector: Query vector for similarity search
            collection_name: Target collection name
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            metadata_filter: Optional metadata filter
            
        Returns:
            List[SearchResult]: List of similar embeddings
        """
        collection_name = collection_name or self.collection_name
        
        try:
            # Build filter if metadata_filter provided
            search_filter = None
            if metadata_filter:
                conditions = []
                for key, value in metadata_filter.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                search_filter = Filter(must=conditions)
            
            # Perform search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=search_filter,
                with_payload=True
            )
            
            # Convert to SearchResult objects
            search_results = []
            for result in results:
                search_results.append(SearchResult(
                    id=result.id,
                    score=result.score,
                    payload=result.payload,
                    metadata=result.payload
                ))
            
            logger.info(f"Found {len(search_results)} similar embeddings")
            return search_results
            
        except Exception as e:
            logger.error(f"Failed to search similar embeddings: {e}")
            return []
    
    def get_collection_info(self, collection_name: str = None) -> Optional[Dict[str, Any]]:
        """
        Get collection information
        
        Args:
            collection_name: Target collection name
            
        Returns:
            Dict with collection info or None if not found
        """
        collection_name = collection_name or self.collection_name
        
        try:
            info = self.client.get_collection(collection_name)
            return {
                'name': collection_name,
                'vectors_count': info.vectors_count,
                'indexed_vectors_count': info.indexed_vectors_count,
                'points_count': info.points_count,
                'segments_count': info.segments_count,
                'config': {
                    'vector_size': info.config.params.vectors.size,
                    'distance': info.config.params.vectors.distance
                }
            }
        except Exception as e:
            logger.error(f"Failed to get collection info for '{collection_name}': {e}")
            return None
    
    def _collection_exists(self, collection_name: str) -> bool:
        """Check if collection exists"""
        try:
            collections = self.client.get_collections()
            return collection_name in [col.name for col in collections.collections]
        except:
            return False
    
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            uuid.UUID(uuid_string)
            return True
        except ValueError:
            return False
    
    def generate_id(self) -> str:
        """Generate a unique ID for embeddings"""
        return str(uuid.uuid4())
    
    def health_check(self) -> bool:
        """Check if Qdrant service is healthy"""
        if self.client is None:
            return False
        try:
            self.client.get_collections()
            return True
        except:
            return False

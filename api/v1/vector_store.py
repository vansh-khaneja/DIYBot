"""
Vector Store API Endpoints

This module provides API endpoints for vector store operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from vector_store_services.qdrant_service.qdrant_service import QdrantService, EmbeddingPayload, SearchResult
from vector_store_services.config import VectorStoreConfig

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/vector-store", tags=["vector-store"])

# Initialize Qdrant service
qdrant_service = QdrantService(**VectorStoreConfig.get_qdrant_config())


# Pydantic models for API
class EmbeddingRequest(BaseModel):
    id: str
    vector: List[float]
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    query_vector: List[float]
    collection_name: Optional[str] = None
    limit: int = 10
    score_threshold: float = 0.0
    metadata_filter: Optional[Dict[str, Any]] = None


class CollectionRequest(BaseModel):
    collection_name: str
    vector_size: int = 384
    distance: str = "Cosine"


@router.get("/health")
async def health_check():
    """Check if vector store service is healthy"""
    try:
        is_healthy = qdrant_service.health_check()
        return {
            "success": True,
            "healthy": is_healthy,
            "service": "qdrant",
            "message": "Service is healthy" if is_healthy else "Service is not available - check Qdrant connection"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "success": False,
            "healthy": False,
            "service": "qdrant",
            "error": str(e)
        }


@router.post("/collections")
async def create_collection(request: CollectionRequest):
    """Create a new collection"""
    try:
        success = qdrant_service.create_collection(
            collection_name=request.collection_name,
            vector_size=request.vector_size,
            distance=request.distance
        )
        
        if success:
            return {
                "success": True,
                "message": f"Collection '{request.collection_name}' created successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create collection")
            
    except Exception as e:
        logger.error(f"Failed to create collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create collection: {str(e)}")


@router.get("/collections")
async def list_collections():
    """List all collections with detailed information"""
    try:
        collections = qdrant_service.list_collections()
        
        # Get detailed info for each collection
        collection_details = []
        for collection_name in collections:
            info = qdrant_service.get_collection_info(collection_name)
            if info:
                collection_details.append({
                    "name": collection_name,
                    "points_count": info.get('points_count', 0),
                    "vectors_count": info.get('vectors_count', 0),
                    "vector_size": info.get('config', {}).get('vector_size', 3072),
                    "distance": str(info.get('config', {}).get('distance', 'Cosine'))
                })
            else:
                collection_details.append({
                    "name": collection_name,
                    "points_count": 0,
                    "vectors_count": 0,
                    "vector_size": 3072,
                    "distance": "Unknown"
                })
        
        return {
            "success": True,
            "total_collections": len(collections),
            "collections": collection_details
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.delete("/collections/{collection_name}")
async def delete_collection(collection_name: str):
    """Delete a collection"""
    try:
        success = qdrant_service.delete_collection(collection_name)
        
        if success:
            return {
                "success": True,
                "message": f"Collection '{collection_name}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to delete collection")
            
    except Exception as e:
        logger.error(f"Failed to delete collection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")


@router.get("/collections/{collection_name}/info")
async def get_collection_info(collection_name: str):
    """Get collection information"""
    try:
        info = qdrant_service.get_collection_info(collection_name)
        
        if info:
            return {
                "success": True,
                "info": info
            }
        else:
            raise HTTPException(status_code=404, detail="Collection not found")
            
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get collection info: {str(e)}")


@router.post("/embeddings")
async def add_embedding(request: EmbeddingRequest, collection_name: str = None):
    """Add a single embedding"""
    try:
        embedding = EmbeddingPayload(
            id=request.id,
            vector=request.vector,
            payload=request.payload,
            metadata=request.metadata
        )
        
        success = qdrant_service.add_embedding(embedding, collection_name)
        
        if success:
            return {
                "success": True,
                "message": f"Embedding '{request.id}' added successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add embedding")
            
    except Exception as e:
        logger.error(f"Failed to add embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add embedding: {str(e)}")


@router.post("/embeddings/batch")
async def add_embeddings_batch(requests: List[EmbeddingRequest], collection_name: str = None):
    """Add multiple embeddings in batch"""
    try:
        embeddings = []
        for request in requests:
            embedding = EmbeddingPayload(
                id=request.id,
                vector=request.vector,
                payload=request.payload,
                metadata=request.metadata
            )
            embeddings.append(embedding)
        
        success = qdrant_service.add_embeddings_batch(embeddings, collection_name)
        
        if success:
            return {
                "success": True,
                "message": f"Added {len(embeddings)} embeddings successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to add embeddings")
            
    except Exception as e:
        logger.error(f"Failed to add embeddings batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add embeddings: {str(e)}")


@router.get("/embeddings/{embedding_id}")
async def get_embedding(embedding_id: str, collection_name: str = None):
    """Get an embedding by ID"""
    try:
        embedding = qdrant_service.get_embedding(embedding_id, collection_name)
        
        if embedding:
            return {
                "success": True,
                "embedding": {
                    "id": embedding.id,
                    "vector": embedding.vector,
                    "payload": embedding.payload,
                    "metadata": embedding.metadata
                }
            }
        else:
            raise HTTPException(status_code=404, detail="Embedding not found")
            
    except Exception as e:
        logger.error(f"Failed to get embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get embedding: {str(e)}")


@router.delete("/embeddings/{embedding_id}")
async def delete_embedding(embedding_id: str, collection_name: str = None):
    """Delete an embedding by ID"""
    try:
        success = qdrant_service.delete_embedding(embedding_id, collection_name)
        
        if success:
            return {
                "success": True,
                "message": f"Embedding '{embedding_id}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to delete embedding")
            
    except Exception as e:
        logger.error(f"Failed to delete embedding: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete embedding: {str(e)}")


@router.post("/search")
async def search_similar(request: SearchRequest):
    """Search for similar embeddings"""
    try:
        results = qdrant_service.search_similar(
            query_vector=request.query_vector,
            collection_name=request.collection_name,
            limit=request.limit,
            score_threshold=request.score_threshold,
            metadata_filter=request.metadata_filter
        )
        
        # Convert SearchResult objects to dictionaries
        search_results = []
        for result in results:
            search_results.append({
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
                "metadata": result.metadata
            })
        
        return {
            "success": True,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        logger.error(f"Failed to search similar embeddings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to search: {str(e)}")


@router.post("/generate-id")
async def generate_id():
    """Generate a unique ID for embeddings"""
    try:
        unique_id = qdrant_service.generate_id()
        return {
            "success": True,
            "id": unique_id
        }
    except Exception as e:
        logger.error(f"Failed to generate ID: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate ID: {str(e)}")

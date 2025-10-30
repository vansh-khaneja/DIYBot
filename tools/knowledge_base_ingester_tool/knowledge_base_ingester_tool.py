"""
Knowledge Base Ingester Tool - Uses Qdrant Vector Store with OpenAI Embeddings

This tool ingests documents into a vector database for semantic search.
It uses OpenAI's text-embedding-3-large model for high-quality embeddings.
"""

import sys
import os
import uuid
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import services with error handling
try:
    from vector_store_services.qdrant_service.qdrant_service import QdrantService, EmbeddingPayload
    from vector_store_services.config import VectorStoreConfig
except ImportError:
    QdrantService = None
    EmbeddingPayload = None
    VectorStoreConfig = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class KnowledgeBaseIngesterTool:
    """
    Tool for ingesting documents into a vector database for semantic search.
    
    This tool uses OpenAI's text-embedding-3-large model to create high-quality
    embeddings and stores them in Qdrant vector database.
    """
    
    def __init__(self, collection_name: str = "knowledge_base"):
        """
        Initialize the knowledge base ingester tool.
        
        Args:
            collection_name: Name of the collection to store documents
        """
        self.collection_name = collection_name
        self.openai_client = None
        self.qdrant_service = None
        
        # Initialize OpenAI client
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                print("Warning: OPENAI_API_KEY not set. OpenAI embeddings will not be available.")
        else:
            print("Warning: OpenAI not available. Install with: pip install openai")
        
        # Initialize Qdrant service
        if QdrantService:
            try:
                config = VectorStoreConfig.get_qdrant_config()
                self.qdrant_service = QdrantService(
                    url=config.get('url'),
                    api_key=config.get('api_key'),
                    collection_name=collection_name,
                    vector_size=3072  # text-embedding-3-large size
                )
            except Exception as e:
                print(f"Warning: Could not initialize Qdrant service: {e}")
        else:
            print("Warning: Qdrant service not available.")
    
    def get_openai_embedding(self, text: str) -> List[float]:
        """
        Get embedding from OpenAI using text-embedding-3-large model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of float values representing the embedding
        """
        if not self.openai_client:
            raise Exception("OpenAI client not available. Check OPENAI_API_KEY.")
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-large",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to get OpenAI embedding: {e}")
    
    def ingest_document(
        self, 
        content: str, 
        title: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a single document into the knowledge base.
        
        Args:
            content: The document content to ingest
            title: Optional title for the document
            source: Optional source of the document
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with success status and document ID
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available",
                    "document_id": None
                }
            
            if not self.openai_client:
                return {
                    "success": False,
                    "error": "OpenAI client not available. Check OPENAI_API_KEY.",
                    "document_id": None
                }
            
            # Generate unique ID
            document_id = str(uuid.uuid4())
            
            # Get embedding
            embedding_vector = self.get_openai_embedding(content)
            
            # Prepare metadata
            doc_metadata = {
                "title": title or "Untitled Document",
                "source": source or "Unknown",
                "content_length": len(content),
                "ingested_at": "2024-01-01T00:00:00",  # You might want to use datetime.now().isoformat()
                **(metadata or {})
            }
            
            # Create embedding payload
            embedding_payload = EmbeddingPayload(
                id=document_id,
                vector=embedding_vector,
                payload={
                    "content": content,
                    "title": title or "Untitled Document",
                    "source": source or "Unknown"
                },
                metadata=doc_metadata
            )
            
            # Add to vector store
            success = self.qdrant_service.add_embedding(embedding_payload, self.collection_name)
            
            if success:
                return {
                    "success": True,
                    "document_id": document_id,
                    "metadata": {
                        "title": title,
                        "source": source,
                        "content_length": len(content),
                        "embedding_size": len(embedding_vector)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to add document to vector store",
                    "document_id": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "document_id": None
            }
    
    def ingest_documents_batch(
        self, 
        documents: List[Dict[str, Any]],
        batch_size: int = 50
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents in batches.
        
        Args:
            documents: List of documents, each with 'content' and optional 'title', 'source', 'metadata'
            batch_size: Number of documents to process per batch
            
        Returns:
            Dictionary with success status and results
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available",
                    "results": []
                }
            
            if not self.openai_client:
                return {
                    "success": False,
                    "error": "OpenAI client not available. Check OPENAI_API_KEY.",
                    "results": []
                }
            
            results = []
            successful_count = 0
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_embeddings = []
                
                for doc in batch:
                    try:
                        # Extract document data
                        content = doc.get('content', '')
                        title = doc.get('title')
                        source = doc.get('source')
                        metadata = doc.get('metadata', {})
                        
                        if not content:
                            results.append({
                                "success": False,
                                "error": "Document content is empty",
                                "document_id": None
                            })
                            continue
                        
                        # Generate unique ID
                        document_id = str(uuid.uuid4())
                        
                        # Get embedding
                        embedding_vector = self.get_openai_embedding(content)
                        
                        # Prepare metadata
                        doc_metadata = {
                            "title": title or "Untitled Document",
                            "source": source or "Unknown",
                            "content_length": len(content),
                            "ingested_at": "2024-01-01T00:00:00",
                            **metadata
                        }
                        
                        # Create embedding payload
                        embedding_payload = EmbeddingPayload(
                            id=document_id,
                            vector=embedding_vector,
                            payload={
                                "content": content,
                                "title": title or "Untitled Document",
                                "source": source or "Unknown"
                            },
                            metadata=doc_metadata
                        )
                        
                        batch_embeddings.append(embedding_payload)
                        
                        results.append({
                            "success": True,
                            "document_id": document_id,
                            "metadata": {
                                "title": title,
                                "source": source,
                                "content_length": len(content),
                                "embedding_size": len(embedding_vector)
                            }
                        })
                        
                    except Exception as e:
                        results.append({
                            "success": False,
                            "error": str(e),
                            "document_id": None
                        })
                
                # Add batch to vector store
                if batch_embeddings:
                    batch_success = self.qdrant_service.add_embeddings_batch(
                        batch_embeddings, 
                        self.collection_name,
                        batch_size=batch_size
                    )
                    
                    if batch_success:
                        successful_count += len(batch_embeddings)
            
            return {
                "success": True,
                "total_documents": len(documents),
                "successful_count": successful_count,
                "failed_count": len(documents) - successful_count,
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the knowledge base collection.
        
        Returns:
            Dictionary with collection information
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available"
                }
            
            info = self.qdrant_service.get_collection_info(self.collection_name)
            
            if info:
                return {
                    "success": True,
                    "collection_name": self.collection_name,
                    "points_count": info.get('points_count', 0),
                    "vectors_count": info.get('vectors_count', 0),
                    "vector_size": info.get('config', {}).get('vector_size', 3072)
                }
            else:
                return {
                    "success": False,
                    "error": "Collection not found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """
        Delete a document from the knowledge base.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            Dictionary with success status
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available"
                }
            
            success = self.qdrant_service.delete_embedding(document_id, self.collection_name)
            
            return {
                "success": success,
                "document_id": document_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_all_collections(self) -> Dict[str, Any]:
        """
        Get all collections from the knowledge base.
        
        Returns:
            Dictionary with success status and list of collections
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available",
                    "collections": []
                }
            
            collections = self.qdrant_service.list_collections()
            
            # Get detailed info for each collection
            collection_details = []
            for collection_name in collections:
                info = self.qdrant_service.get_collection_info(collection_name)
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
            return {
                "success": False,
                "error": str(e),
                "collections": []
            }


# Convenience function for quick usage
def ingest_document(
    content: str, 
    title: Optional[str] = None,
    source: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    collection_name: str = "knowledge_base"
) -> Dict[str, Any]:
    """
    Quick function to ingest a single document.
    
    Args:
        content: The document content to ingest
        title: Optional title for the document
        source: Optional source of the document
        metadata: Optional additional metadata
        collection_name: Name of the collection to store the document
        
    Returns:
        Dictionary with success status and document ID
    """
    tool = KnowledgeBaseIngesterTool(collection_name)
    return tool.ingest_document(content, title, source, metadata)


def ingest_documents_batch(
    documents: List[Dict[str, Any]],
    collection_name: str = "knowledge_base",
    batch_size: int = 50
) -> Dict[str, Any]:
    """
    Quick function to ingest multiple documents.
    
    Args:
        documents: List of documents to ingest
        collection_name: Name of the collection to store documents
        batch_size: Number of documents to process per batch
        
    Returns:
        Dictionary with success status and results
    """
    tool = KnowledgeBaseIngesterTool(collection_name)
    return tool.ingest_documents_batch(documents, batch_size)


def get_all_collections() -> Dict[str, Any]:
    """
    Quick function to get all collections from the knowledge base.
    
    Returns:
        Dictionary with success status and list of collections
    """
    tool = KnowledgeBaseIngesterTool()
    return tool.get_all_collections()

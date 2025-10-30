"""
Knowledge Base Retriever Tool - Uses Qdrant Vector Store with OpenAI Embeddings

This tool retrieves relevant documents from a vector database using semantic search.
It uses OpenAI's text-embedding-3-large model for high-quality embeddings.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import services with error handling
try:
    from vector_store_services.qdrant_service.qdrant_service import QdrantService, SearchResult
    from vector_store_services.config import VectorStoreConfig
except ImportError:
    QdrantService = None
    SearchResult = None
    VectorStoreConfig = None

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class KnowledgeBaseRetrieverTool:
    """
    Tool for retrieving relevant documents from a vector database using semantic search.
    
    This tool uses OpenAI's text-embedding-3-large model to create high-quality
    embeddings and searches for similar documents in Qdrant vector database.
    """
    
    def __init__(self, collection_name: str = "knowledge_base"):
        """
        Initialize the knowledge base retriever tool.
        
        Args:
            collection_name: Name of the collection to search in
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
    
    def search_documents(
        self, 
        query: str,
        limit: int = 5,
        score_threshold: float = 0.7,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant documents using semantic similarity.
        
        Args:
            query: The search query
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0.0 to 1.0)
            metadata_filter: Optional metadata filter (e.g., {"source": "wikipedia"})
            
        Returns:
            Dictionary with search results and metadata
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
            
            # Get embedding for the query
            query_embedding = self.get_openai_embedding(query)
            
            # Search for similar documents
            search_results = self.qdrant_service.search_similar(
                query_vector=query_embedding,
                collection_name=self.collection_name,
                limit=limit,
                score_threshold=score_threshold,
                metadata_filter=metadata_filter
            )
            
            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "document_id": result.id,
                    "score": result.score,
                    "content": result.payload.get("content", ""),
                    "title": result.payload.get("title", "Untitled"),
                    "source": result.payload.get("source", "Unknown"),
                    "metadata": result.metadata
                })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(formatted_results),
                "results": formatted_results,
                "search_metadata": {
                    "limit": limit,
                    "score_threshold": score_threshold,
                    "metadata_filter": metadata_filter
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def get_document_by_id(self, document_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific document by its ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Dictionary with document data
        """
        try:
            if not self.qdrant_service:
                return {
                    "success": False,
                    "error": "Qdrant service not available"
                }
            
            # Get document from vector store
            embedding = self.qdrant_service.get_embedding(document_id, self.collection_name)
            
            if embedding:
                return {
                    "success": True,
                    "document_id": document_id,
                    "content": embedding.payload.get("content", ""),
                    "title": embedding.payload.get("title", "Untitled"),
                    "source": embedding.payload.get("source", "Unknown"),
                    "metadata": embedding.metadata
                }
            else:
                return {
                    "success": False,
                    "error": "Document not found",
                    "document_id": document_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_with_context(
        self, 
        query: str,
        context_length: int = 2000,
        limit: int = 3,
        score_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Search for documents and return them with context for LLM usage.
        
        Args:
            query: The search query
            context_length: Maximum total length of context to return
            limit: Maximum number of documents to retrieve
            score_threshold: Minimum similarity score
            
        Returns:
            Dictionary with formatted context for LLM usage
        """
        try:
            # Search for relevant documents
            search_result = self.search_documents(
                query=query,
                limit=limit,
                score_threshold=score_threshold
            )
            
            if not search_result["success"]:
                return search_result
            
            # Format context for LLM
            context_parts = []
            total_length = 0
            
            for i, doc in enumerate(search_result["results"]):
                # Format document with metadata
                doc_text = f"Document {i+1} (Score: {doc['score']:.3f}):\n"
                doc_text += f"Title: {doc['title']}\n"
                doc_text += f"Source: {doc['source']}\n"
                doc_text += f"Content: {doc['content']}\n\n"
                
                # Check if adding this document would exceed context length
                if total_length + len(doc_text) > context_length:
                    break
                
                context_parts.append(doc_text)
                total_length += len(doc_text)
            
            context = "".join(context_parts)
            
            return {
                "success": True,
                "query": query,
                "context": context,
                "context_length": len(context),
                "documents_used": len(context_parts),
                "total_documents_found": search_result["results_count"],
                "search_metadata": search_result["search_metadata"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge base collection.
        
        Returns:
            Dictionary with collection statistics
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
                    "total_documents": info.get('points_count', 0),
                    "total_vectors": info.get('vectors_count', 0),
                    "vector_size": info.get('config', {}).get('vector_size', 3072),
                    "collection_status": "Available"
                }
            else:
                return {
                    "success": False,
                    "error": "Collection not found",
                    "collection_name": self.collection_name
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


# Convenience functions for quick usage
def search_documents(
    query: str,
    collection_name: str = "knowledge_base",
    limit: int = 5,
    score_threshold: float = 0.7,
    metadata_filter: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Quick function to search for relevant documents.
    
    Args:
        query: The search query
        collection_name: Name of the collection to search in
        limit: Maximum number of results to return
        score_threshold: Minimum similarity score
        metadata_filter: Optional metadata filter
        
    Returns:
        Dictionary with search results
    """
    tool = KnowledgeBaseRetrieverTool(collection_name)
    return tool.search_documents(query, limit, score_threshold, metadata_filter)


def search_with_context(
    query: str,
    collection_name: str = "knowledge_base",
    context_length: int = 2000,
    limit: int = 3,
    score_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Quick function to search for documents and return formatted context.
    
    Args:
        query: The search query
        collection_name: Name of the collection to search in
        context_length: Maximum total length of context to return
        limit: Maximum number of documents to retrieve
        score_threshold: Minimum similarity score
        
    Returns:
        Dictionary with formatted context for LLM usage
    """
    tool = KnowledgeBaseRetrieverTool(collection_name)
    return tool.search_with_context(query, context_length, limit, score_threshold)


def get_document_by_id(
    document_id: str,
    collection_name: str = "knowledge_base"
) -> Dict[str, Any]:
    """
    Quick function to retrieve a document by ID.
    
    Args:
        document_id: ID of the document to retrieve
        collection_name: Name of the collection to search in
        
    Returns:
        Dictionary with document data
    """
    tool = KnowledgeBaseRetrieverTool(collection_name)
    return tool.get_document_by_id(document_id)


def get_all_collections() -> Dict[str, Any]:
    """
    Quick function to get all collections from the knowledge base.
    
    Returns:
        Dictionary with success status and list of collections
    """
    tool = KnowledgeBaseRetrieverTool()
    return tool.get_all_collections()

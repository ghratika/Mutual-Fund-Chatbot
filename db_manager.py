import os
import sys
import json
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer
from chunker import MutualFundChunker

# Design Aesthetics: Log printing with professional styling
def log_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

def log_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")

def log_error(msg):
    print(f"\033[91m[ERROR]\033[0m {msg}")

class BGELocalEmbeddingFunction(EmbeddingFunction):
    """
    Custom ChromaDB Embedding Function that integrates BAAI/bge-small-en-v1.5
    locally via the sentence-transformers library.
    """
    def __init__(self, model_name="BAAI/bge-small-en-v1.5"):
        log_info(f"Loading local BGE Small embedding model '{model_name}'...")
        self.model = SentenceTransformer(model_name)
        log_success("Embedding model loaded successfully.")

    def __call__(self, input: Documents) -> Embeddings:
        # Generate and normalize embeddings for cosine similarity
        embeddings = self.model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()

class VectorDBManager:
    def __init__(self, db_dir="db", collection_name="mutual_fund_corpus"):
        self.db_dir = db_dir
        self.collection_name = collection_name
        
        log_info(f"Initializing local persistent ChromaDB client in: {self.db_dir}")
        self.client = chromadb.PersistentClient(path=self.db_dir)
        
        # Load our custom BGE Small embedding function
        self.embedding_function = BGELocalEmbeddingFunction()
        
        # Connect to or create the collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )
        log_success(f"ChromaDB collection '{self.collection_name}' initialized.")

    def upsert_chunks(self, chunks):
        log_info(f"Preparing to upsert {len(chunks)} chunks into ChromaDB...")
        
        ids = []
        documents = []
        metadatas = []
        
        for c in chunks:
            ids.append(c["id"])
            documents.append(c["text"])
            metadatas.append(c["metadata"])
            
        try:
            # Perform an idempotent upsert (overwrites on ID match)
            self.collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            log_success(f"Successfully upserted {len(chunks)} chunks into ChromaDB.")
        except Exception as e:
            log_error(f"Error during ChromaDB upsert: {e}")
            raise e

    def query(self, query_text, limit=3, where_filter=None):
        """
        Executes a vector similarity search with support for metadata filters.
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=limit,
                where=where_filter
            )
            return results
        except Exception as e:
            log_error(f"Error executing ChromaDB query: {e}")
            return None

def main():
    try:
        # Step 1: Chunk corpus.json
        chunker = MutualFundChunker()
        chunks = chunker.generate_chunks()
        
        # Step 2: Initialize ChromaDB & Upsert
        db_manager = VectorDBManager()
        db_manager.upsert_chunks(chunks)
        
        # Step 3: Automated Verification Check (Prevent Cross-Talk)
        log_info("Executing database verification query with metadata filter...")
        
        # Scenario: Asking for the manager of Small Cap fund, filtered specifically to HDFC Small Cap
        query_text = "Who is the fund manager?"
        where_filter = {"scheme_name": "HDFC Small Cap Fund Direct Growth"}
        
        results = db_manager.query(query_text, limit=2, where_filter=where_filter)
        
        if results and results.get("documents") and results["documents"][0]:
            log_success("Verification Query Succeeded! Search results:")
            for idx, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][idx]
                distance = results["distances"][0][idx] if "distances" in results else "N/A"
                # Safe printing for Windows console
                safe_doc = doc.replace("₹", "Rs.")
                print(f"  [{idx+1}] [Dist: {distance:.4f}] {safe_doc}")
                print(f"      Metadata: {meta}")
        else:
            log_error("Verification query returned no results.")
            
    except Exception as e:
        log_error(f"Fatal error running db_manager pipeline: {e}")
        exit(1)

if __name__ == "__main__":
    main()

import os
import re
import json
import math
import numpy as np
from db_manager import VectorDBManager, log_info, log_success, log_error

class LocalBM25:
    """
    Lightweight, local Python implementation of the BM25 ranking algorithm
    optimized for small subsets of context chunks.
    """
    def __init__(self, documents, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_tokens = [self._tokenize(doc) for doc in documents]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = sum(self.doc_lens) / len(self.doc_lens) if self.doc_lens else 1.0
        self.doc_freqs = {}
        self.idf = {}
        self._compute_doc_freqs()
        self._compute_idf()

    def _tokenize(self, text):
        # Lowercase and split by alphanumeric tokens
        text = text.lower()
        return re.findall(r'\b\w+\b', text)

    def _compute_doc_freqs(self):
        for tokens in self.doc_tokens:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def _compute_idf(self):
        N = len(self.documents)
        for token, df in self.doc_freqs.items():
            # Standard BM25 IDF formulation with smoothing
            self.idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1.0)

    def score(self, query, doc_idx):
        query_tokens = self._tokenize(query)
        doc_tokens = self.doc_tokens[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        score = 0.0
        for token in query_tokens:
            if token not in self.doc_freqs:
                continue
            tf = doc_tokens.count(token)
            idf_val = self.idf[token]
            num = tf * (self.k1 + 1)
            denom = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += idf_val * (num / denom)
        return score

class MutualFundRetrievalEngine:
    """
    Retrieval engine that performs deterministic pre-filtering on HDFC schemes,
    queries ChromaDB, executes hybrid BM25 + Semantic score fusion, and
    constructs prompt contexts.
    """
    def __init__(self, corpus_path="data/corpus.json", db_dir="db", collection_name="mutual_fund_corpus"):
        self.corpus_path = corpus_path
        
        # Load corpus from JSON to extract raw parameters
        log_info(f"Loading raw corpus from {self.corpus_path}...")
        if not os.path.exists(self.corpus_path):
            raise FileNotFoundError(f"Corpus file not found at {self.corpus_path}. Please run scraper.py first.")
            
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            self.corpus = json.load(f)
            
        # Connect to ChromaDB
        self.db_manager = VectorDBManager(db_dir=db_dir, collection_name=collection_name)
        
        # Auto-seed the database if the collection is empty
        try:
            count = self.db_manager.collection.count()
            if count == 0:
                log_info("ChromaDB collection is empty. Auto-seeding database from data/corpus.json...")
                from db_manager import main as seed_db
                seed_db()
        except Exception as e:
            log_error(f"Error checking or seeding database: {e}")

        log_success("MutualFundRetrievalEngine initialized successfully.")

    def extract_scheme_name(self, query: str):
        """
        Extracts the specific scheme name from the user's query using keyword mappings.
        """
        query_lower = query.lower()
        
        scheme_map = {
            "mid cap": "HDFC Mid Cap Fund Direct Growth",
            "mid-cap": "HDFC Mid Cap Fund Direct Growth",
            "midcap": "HDFC Mid Cap Fund Direct Growth",
            "large cap": "HDFC Large Cap Fund Direct Growth",
            "large-cap": "HDFC Large Cap Fund Direct Growth",
            "largecap": "HDFC Large Cap Fund Direct Growth",
            "small cap": "HDFC Small Cap Fund Direct Growth",
            "small-cap": "HDFC Small Cap Fund Direct Growth",
            "smallcap": "HDFC Small Cap Fund Direct Growth",
            "gold": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
            "etf": "HDFC Gold ETF Fund of Fund Direct Plan Growth",
            "defence": "HDFC Defence Fund Direct Growth",
            "defense": "HDFC Defence Fund Direct Growth"
        }
        
        for kw, name in scheme_map.items():
            if kw in query_lower:
                return name
                
        return None

    def retrieve(self, query: str, limit=3):
        """
        Executes hybrid semantic vector search + keyword matching (BM25) with pre-filtering.
        """
        scheme_name = self.extract_scheme_name(query)
        where_filter = None
        if scheme_name:
            where_filter = {"scheme_name": scheme_name}
            log_info(f"Deterministic pre-filtering applied for scheme: '{scheme_name}'")
        else:
            log_info("No specific scheme matched. Executing unfiltered search.")

        # Query ChromaDB (retrieve a larger pool of candidates to rerank)
        candidate_limit = max(10, limit * 2)
        results = self.db_manager.query(query, limit=candidate_limit, where_filter=where_filter)
        
        if not results or not results.get("documents") or not results["documents"][0]:
            log_info("No document chunks returned from ChromaDB.")
            return []

        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        ids = results["ids"][0]

        # Calculate semantic similarities (Similarity = 1.0 - Cosine Distance, bounded [0, 1])
        semantic_scores = [max(0.0, 1.0 - dist) for dist in distances]

        # Fit local BM25 on the retrieved candidates
        bm25 = LocalBM25(docs)
        bm25_scores = [bm25.score(query, idx) for idx in range(len(docs))]
        
        # Normalize BM25 scores
        max_bm25 = max(bm25_scores) if bm25_scores else 1.0
        normalized_bm25 = [score / max_bm25 if max_bm25 > 0.0 else 0.0 for score in bm25_scores]

        # Perform weighted score fusion (60% semantic, 40% keyword BM25)
        fused_items = []
        for idx in range(len(docs)):
            combined_score = 0.6 * semantic_scores[idx] + 0.4 * normalized_bm25[idx]
            fused_items.append({
                "id": ids[idx],
                "text": docs[idx],
                "metadata": metadatas[idx],
                "semantic_score": semantic_scores[idx],
                "bm25_score": bm25_scores[idx],
                "combined_score": combined_score
            })

        # Sort candidate items by combined score in descending order
        fused_items.sort(key=lambda x: x["combined_score"], reverse=True)
        return fused_items[:limit]

    def build_prompt_context(self, query: str, limit=2):
        """
        Assembles retrieved text chunks alongside raw metrics from the structured JSON store.
        """
        scheme_name = self.extract_scheme_name(query)
        retrieved_items = self.retrieve(query, limit=limit)
        
        raw_metrics_str = ""
        source_url = ""
        
        if scheme_name:
            matched_fund = next((fund for fund in self.corpus if fund.get("scheme_name") == scheme_name), None)
            if matched_fund:
                source_url = matched_fund.get("url", "")
                raw_metrics_str = (
                    f"Scheme Name: {matched_fund.get('scheme_name')}\n"
                    f"Category: {matched_fund.get('category')} ({matched_fund.get('sub_category')})\n"
                    f"Net Asset Value (NAV): ₹{matched_fund.get('nav')} (as of {matched_fund.get('nav_date')})\n"
                    f"Assets Under Management (AUM) / Fund Size: ₹{matched_fund.get('aum')} Crores\n"
                    f"1-Month Return: {matched_fund.get('return_1m')}%\n"
                    f"6-Month Return: {matched_fund.get('return_6m')}%\n"
                    f"1-Year Return: {matched_fund.get('return_1y')}%\n"
                    f"Expense Ratio: {matched_fund.get('expense_ratio')}%\n"
                    f"Exit Load: {matched_fund.get('exit_load')}\n"
                    f"Minimum SIP Investment: ₹{matched_fund.get('min_sip')}\n"
                    f"Riskometer: {matched_fund.get('riskometer')}\n"
                    f"Benchmark Index: {matched_fund.get('benchmark')}\n"
                )

        chunks_str = ""
        for idx, item in enumerate(retrieved_items):
            chunks_str += f"\n[Document {idx+1}] (Chunk Type: {item['metadata'].get('chunk_type')}):\n{item['text']}\n"
            
        context = "MUTUAL FUND FAQ CONTEXT INFORMATION:\n"
        if raw_metrics_str:
            context += "--- RAW QUANTITATIVE METRICS ---\n"
            context += raw_metrics_str
            context += f"Source Link: {source_url}\n"
            context += "---------------------------------\n"
            
        if chunks_str:
            context += "\n--- RETRIEVED SEMANTIC CHUNKS ---\n"
            context += chunks_str
            context += "---------------------------------\n"
        else:
            context += "\n[WARNING] No semantic chunks retrieved from vector store.\n"

        return context, retrieved_items

if __name__ == "__main__":
    # Test runner
    print("[INFO] Running MutualFundRetrievalEngine simple test...")
    engine = MutualFundRetrievalEngine()
    test_query = "What is the exit load of HDFC Small Cap Fund?"
    context, items = engine.build_prompt_context(test_query)
    print("\n--- Built Prompt Context ---")
    print(context)

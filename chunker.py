import json
import hashlib
import os

class MutualFundChunker:
    def __init__(self, corpus_path="data/corpus.json"):
        self.corpus_path = corpus_path

    def load_corpus(self):
        if not os.path.exists(self.corpus_path):
            raise FileNotFoundError(f"Corpus file not found at {self.corpus_path}. Please run scraper.py first.")
            
        with open(self.corpus_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def generate_chunks(self, corpus=None):
        if corpus is None:
            corpus = self.load_corpus()
            
        chunks = []
        
        for fund in corpus:
            scheme_name = fund.get("scheme_name")
            url = fund.get("url")
            category = fund.get("category")
            sub_category = fund.get("sub_category")
            nav = fund.get("nav")
            nav_date = fund.get("nav_date")
            expense_ratio = fund.get("expense_ratio")
            aum = fund.get("aum")
            return_1m = fund.get("return_1m")
            return_6m = fund.get("return_6m")
            return_1y = fund.get("return_1y")
            exit_load = fund.get("exit_load")
            min_sip = fund.get("min_sip")
            riskometer = fund.get("riskometer")
            benchmark = fund.get("benchmark")
            description = fund.get("description")
            
            # --- 1. Core Metrics Chunk ---
            metrics_text = (
                f"Fund Scheme Name: {scheme_name}. "
                f"Category: {category} ({sub_category}). "
                f"Net Asset Value (NAV): ₹{nav} (as of {nav_date}). "
                f"Assets Under Management (AUM) / Fund Size: ₹{aum} Crores. "
                f"1-Month Return Rate: {return_1m}%. "
                f"6-Month Return Rate: {return_6m}%. "
                f"1-Year Return Rate: {return_1y}%. "
                f"Expense Ratio: {expense_ratio}%. "
                f"Exit Load Details: {exit_load}. "
                f"Minimum SIP investment: ₹{min_sip}. "
                f"Riskometer Category: {riskometer}. "
                f"Benchmark Index: {benchmark}."
            )
            
            metrics_id = hashlib.md5(metrics_text.encode("utf-8")).hexdigest()
            chunks.append({
                "id": f"metrics_{metrics_id}",
                "text": metrics_text,
                "metadata": {
                    "scheme_name": scheme_name,
                    "url": url,
                    "chunk_type": "metrics"
                }
            })
            
            # --- 2. Scheme Description Chunk ---
            desc_text = (
                f"Fund Scheme Name: {scheme_name} "
                f"Investment Objective & Description: {description}"
            )
            
            desc_id = hashlib.md5(desc_text.encode("utf-8")).hexdigest()
            chunks.append({
                "id": f"desc_{desc_id}",
                "text": desc_text,
                "metadata": {
                    "scheme_name": scheme_name,
                    "url": url,
                    "chunk_type": "description"
                }
            })
            
            # --- 3. Fund Manager Profile Chunks (One per manager) ---
            managers = fund.get("fund_managers", [])
            for mgr in managers:
                mgr_name = mgr.get("name")
                education = mgr.get("education")
                experience = mgr.get("experience")
                date_from = mgr.get("date_from")
                funds_count = mgr.get("funds_managed_count")
                
                # Format start date nicely if present
                start_date_str = date_from
                if date_from and "T" in date_from:
                    start_date_str = date_from.split("T")[0]
                
                mgr_text = (
                    f"Fund Scheme Name: {scheme_name} - Fund Manager Profile: Managed by {mgr_name}. "
                    f"Education Background: {education}. "
                    f"Professional Experience: {experience}. "
                    f"Start date managing this fund: {start_date_str}. "
                    f"Total number of other schemes managed by {mgr_name}: {funds_count}."
                )
                
                mgr_id = hashlib.md5(mgr_text.encode("utf-8")).hexdigest()
                chunks.append({
                    "id": f"manager_{mgr_id}",
                    "text": mgr_text,
                    "metadata": {
                        "scheme_name": scheme_name,
                        "url": url,
                        "chunk_type": "manager",
                        "manager_name": mgr_name
                    }
                })
                
        return chunks

if __name__ == "__main__":
    import sys
    # Test execution
    print("[INFO] Running MutualFundChunker test...")
    try:
        chunker = MutualFundChunker()
        all_chunks = chunker.generate_chunks()
        print(f"[SUCCESS] Successfully generated {len(all_chunks)} semantic chunks from corpus.json!")
        
        # Print a sample chunk of each type safely
        types_printed = set()
        for c in all_chunks:
            c_type = c["metadata"]["chunk_type"]
            if c_type not in types_printed:
                print(f"\n--- Sample Chunk (Type: {c_type}) ---")
                print(f"ID: {c['id']}")
                # Replace rupee symbol with Rs. solely for safe console printing on Windows
                safe_text = c['text'].replace("₹", "Rs.")
                print(f"Text: {safe_text}")
                print(f"Metadata: {c['metadata']}")
                types_printed.add(c_type)
                
    except Exception as e:
        print(f"[ERROR] Chunker test failed: {e}")

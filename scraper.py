import os
import time
import random
import json
import requests
from bs4 import BeautifulSoup

# Design Aesthetics: Log printing with professional styling
def log_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

def log_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")

def log_error(msg):
    print(f"\033[91m[ERROR]\033[0m {msg}")

class GrowwScraper:
    def __init__(self):
        self.urls = [
            "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
            "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth"
        ]
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def fetch_fund_data(self, url):
        log_info(f"Initiating request for: {url}")
        try:
            # Adding random sleep (jitter) to respect rate limits
            sleep_time = random.uniform(1.5, 3.0)
            log_info(f"Sleeping for {sleep_time:.2f} seconds before requesting...")
            time.sleep(sleep_time)

            response = requests.get(url, headers=self.headers, timeout=15)
            
            if response.status_code != 200:
                log_error(f"Failed to fetch {url} (HTTP status: {response.status_code})")
                return None
                
            soup = BeautifulSoup(response.text, "html.parser")
            script_tag = soup.find("script", id="__NEXT_DATA__")
            
            if not script_tag:
                log_error(f"Did not find '__NEXT_DATA__' script tag on {url}")
                return None
                
            next_data = json.loads(script_tag.string)
            page_props = next_data.get("props", {}).get("pageProps", {})
            mf_data = page_props.get("mfServerSideData", {})
            
            if not mf_data:
                log_error(f"No 'mfServerSideData' field found in hydration props for {url}")
                return None
                
            return self.parse_mf_data(mf_data, url)

        except Exception as e:
            log_error(f"Exception raised while scraping {url}: {e}")
            return None

    def parse_mf_data(self, mf_data, url):
        # Extract fund managers details cleanly
        raw_managers = mf_data.get("fund_manager_details", [])
        parsed_managers = []
        for mgr in raw_managers:
            parsed_managers.append({
                "name": mgr.get("person_name"),
                "education": mgr.get("education"),
                "experience": mgr.get("experience"),
                "date_from": mgr.get("date_from"),
                "funds_managed_count": len(mgr.get("funds_managed", []))
            })

        # Structured schema representation
        return_stats = mf_data.get("return_stats", [])
        first_stat = return_stats[0] if isinstance(return_stats, list) and len(return_stats) > 0 else {}

        parsed_fund = {
            "scheme_name": mf_data.get("scheme_name"),
            "url": url,
            "category": mf_data.get("category"),
            "sub_category": mf_data.get("sub_category"),
            "nav": mf_data.get("nav"),
            "nav_date": mf_data.get("nav_date"),
            "expense_ratio": mf_data.get("expense_ratio"),
            "exit_load": mf_data.get("exit_load"),
            "min_sip": mf_data.get("min_sip_investment"),
            "riskometer": mf_data.get("nfo_risk"),
            "benchmark": mf_data.get("benchmark"),
            "description": mf_data.get("description"),
            "fund_managers": parsed_managers,
            "aum": mf_data.get("aum"),
            "return_1m": first_stat.get("return1m"),
            "return_6m": first_stat.get("return6m"),
            "return_1y": first_stat.get("return1y")
        }
        
        # Ingestion Integrity Validation check
        self.validate_fund_data(parsed_fund, url)
        return parsed_fund

    def validate_fund_data(self, fund, url):
        # Validate critical fields that are required by the FAQ chatbot system
        required_fields = [
            "scheme_name",
            "nav",
            "expense_ratio",
            "exit_load",
            "riskometer",
            "benchmark",
            "fund_managers",
            "aum",
            "return_1m",
            "return_6m",
            "return_1y"
        ]
        
        for field in required_fields:
            if fund.get(field) is None or fund.get(field) == "":
                raise ValueError(f"Ingestion Integrity Violation: Critical field '{field}' is missing for {url}")
        
        if not fund["fund_managers"]:
            raise ValueError(f"Ingestion Integrity Violation: No fund managers returned for {url}")
            
        log_success(f"Successfully scraped and validated: {fund['scheme_name']}")

    def scrape_all(self):
        log_info("Starting batch scrape of 5 target Groww mutual fund schemes...")
        corpus = []
        
        for url in self.urls:
            fund_data = self.fetch_fund_data(url)
            if fund_data:
                corpus.append(fund_data)
            else:
                raise RuntimeError(f"Scraping aborted: Failed to ingest data from {url}")
        
        # Verify that all 5 schemes are fully harvested
        if len(corpus) != 5:
            raise RuntimeError(f"Corpus Ingestion Mismatch: Expected 5 funds, harvested {len(corpus)}")
            
        return corpus

def main():
    try:
        scraper = GrowwScraper()
        corpus = scraper.scrape_all()
        
        # Write to workspace data/ directory (created automatically if missing)
        output_dir = "data"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "corpus.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(corpus, f, indent=2, ensure_ascii=False)
            
        log_success(f"Ingestion completed. Structured data written to {output_path}")
        
    except Exception as e:
        log_error(f"Fatal error running GrowwScraper pipeline: {e}")
        exit(1)

if __name__ == "__main__":
    main()

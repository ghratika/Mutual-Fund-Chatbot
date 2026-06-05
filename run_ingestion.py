import os
import sys
import time
import datetime
import argparse

# Adjust paths to make sure we import local modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from scraper import main as run_scraper
from db_manager import main as run_db_manager

# Design Aesthetics: Log printing with professional styling
def log_info(msg):
    print(f"\033[94m[INFO]\033[0m {msg}")

def log_success(msg):
    print(f"\033[92m[SUCCESS]\033[0m {msg}")

def log_error(msg):
    print(f"\033[91m[ERROR]\033[0m {msg}")

def execute_ingestion():
    """
    Executes the full ingestion pipeline: scraping the source URLs and updating the vector database.
    """
    start_time = time.time()
    log_info(f"Starting scheduled ingestion pipeline at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST...")
    
    try:
        # Step 1: Run scraper to update data/corpus.json
        run_scraper()
        
        # Step 2: Run db_manager to update ChromaDB and verify
        run_db_manager()
        
        duration = time.time() - start_time
        log_success(f"Ingestion pipeline completed successfully in {duration:.2f} seconds.")
    except Exception as e:
        log_error(f"Ingestion pipeline failed: {e}")

def get_seconds_until_next_run(target_hour=10, target_minute=0):
    """
    Calculates the number of seconds until the next 10:00 AM IST.
    """
    now = datetime.datetime.now()
    # Create target datetime for today at 10:00 AM
    target_today = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    if now >= target_today:
        # If the target time has already passed today, target 10:00 AM tomorrow
        target_time = target_today + datetime.timedelta(days=1)
    else:
        target_time = target_today
        
    return (target_time - now).total_seconds(), target_time

def main():
    parser = argparse.ArgumentParser(description="Daily Ingestion Scheduler for HDFC Mutual Fund FAQ Assistant")
    parser.add_argument("--now", action="store_true", help="Run the ingestion pipeline once immediately and exit")
    args = parser.parse_args()

    if args.now:
        execute_ingestion()
        return

    log_info("Starting the Daily Ingestion Scheduler...")
    log_info("Scheduler configured to run every day at 10:00 AM IST (local system time).")
    
    while True:
        seconds_to_wait, next_run = get_seconds_until_next_run(10, 0)
        log_info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {seconds_to_wait/3600:.2f} hours)")
        
        # Sleep until the next scheduled time
        # We sleep in smaller increments (e.g., 60 seconds) so the process remains responsive to interruption
        while seconds_to_wait > 0:
            sleep_duration = min(60.0, seconds_to_wait)
            time.sleep(sleep_duration)
            seconds_to_wait -= sleep_duration
            
        # Execute the pipeline
        execute_ingestion()
        
        # Sleep for a minute to prevent double-firing in the same minute
        time.sleep(60)

if __name__ == "__main__":
    main()

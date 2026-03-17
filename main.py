import os
import sys
from datetime import datetime
from scraper import scrape_and_save, aggregate_comments
from llm_processor import call_llm
from validator import validate_and_fix_stumppdogg
from send_email import dispatch_stumppdogg_email
from kb_updater import update_knowledge_base

TODAY_STR = datetime.now().strftime("%Y-%m-%d")

# --- AUTO-LOGGING SETUP ---
class DualLogger:
    """Writes print statements to both the console and a log file."""
    def __init__(self, filepath):
        self.terminal = sys.stdout
        # 'a' mode appends to the file so it doesn't overwrite earlier runs on the same day
        self.log = open(filepath, "a", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush() # Forces immediate save to prevent data loss on crash

    def flush(self):
        self.terminal.flush()
        self.log.flush()
# --------------------------

def main():
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"\n[{current_time}] --- Starting #StumpPdogg Daily Pipeline for {TODAY_STR} ---")

    # MAIN CONFIGS
    published_before_hours = 24
    published_after_hours = 48

    # Step 1: Scrape YouTube
    videos_found = scrape_and_save(TODAY_STR, published_before_hours, published_after_hours)
    if not videos_found:
        print("Pipeline stopped: No recent videos found.")
        return

    # Step 2: Aggregate Comments
    aggregated_file = aggregate_comments(TODAY_STR)
    if not aggregated_file:
        print("Pipeline stopped: No comments to aggregate.")
        return

    # Step 2.5: Update the Knowledge Base
    kb_updated = update_knowledge_base()

    # Step 3: Run GPT-5
    llm_output_file = call_llm(aggregated_file, TODAY_STR)
    if not llm_output_file:
        print("Pipeline stopped: LLM processing failed.")
        return

    # Step 4: Validate and Fix Hallucinations
    is_valid = validate_and_fix_stumppdogg(TODAY_STR)
    if not is_valid:
        print("Pipeline stopped: Validation failed.")
        return

    # Step 5: Dispatch the Email
    dispatch_stumppdogg_email()
    
    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    # Create the logs folder and set up the file path
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", f"{TODAY_STR}.log")
    
    # Redirect standard output and errors to our DualLogger
    sys.stdout = DualLogger(log_path)
    sys.stderr = sys.stdout  # This captures all red error tracebacks if the script crashes!
    
    main()
import os
from datetime import datetime
from scraper import step_one_scrape_and_save, step_two_aggregate_comments
from llm_processor import step_three_call_llm
from validator import validate_and_fix_stumppdogg
from send_email import dispatch_stumppdogg_email

TODAY_STR = datetime.now().strftime("%Y-%m-%d")

def main():
    print(f"--- Starting #StumpPdogg Daily Pipeline for {TODAY_STR} ---")
    
    # Step 1: Scrape YouTube
    # videos_found = step_one_scrape_and_save(TODAY_STR)
    # if not videos_found:
    #     print("Pipeline stopped: No recent videos found.")
    #     return

    # # Step 2: Aggregate Comments
    # aggregated_file = step_two_aggregate_comments(TODAY_STR)
    # if not aggregated_file:
    #     print("Pipeline stopped: No comments to aggregate.")
    #     return

    # # Step 3: Run GPT-5
    # llm_output_file = step_three_call_llm(aggregated_file, TODAY_STR)
    # if not llm_output_file:
    #     print("Pipeline stopped: LLM processing failed.")
    #     return

    # # Step 4: Validate and Fix Hallucinations
    # is_valid = validate_and_fix_stumppdogg(TODAY_STR)
    # if not is_valid:
    #     print("Pipeline stopped: Validation failed.")
    #     return

    # Step 5: Dispatch the Email
    dispatch_stumppdogg_email()
    
    print("--- Pipeline Complete ---")

if __name__ == "__main__":
    main()
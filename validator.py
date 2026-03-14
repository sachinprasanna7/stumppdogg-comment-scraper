import os
import re
from datetime import datetime

def validate_stumppdogg_output():
    today_str = datetime.now().strftime("%Y-%m-%d")
    source_path = os.path.join("llm_input_comments", f"{today_str}.txt")
    llm_path = os.path.join("stumppdogg_comments", f"{today_str}.txt")

    if not os.path.exists(source_path) or not os.path.exists(llm_path):
        print(f"Error: Files for {today_str} not found. Ensure Step 1-3 ran successfully.")
        return

    # 1. Load Source of Truth into a dictionary for quick lookup
    # Format in source: Author: @name | Likes: X | Comment: Text
    source_lookup = {}
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "Author:" in line and "|" in line:
                try:
                    parts = line.split("|")
                    author = parts[0].replace("Author:", "").strip()
                    # We store the comment text normalized (lowercase, no spaces) to help matching
                    comment_text = parts[2].replace("Comment:", "").strip()
                    source_lookup[author] = comment_text
                except IndexError:
                    continue

    # 2. Parse LLM Output
    # Format in LLM: [Number]. Question from @name ... "The Question: [text]"
    with open(llm_path, 'r', encoding='utf-8') as f:
        llm_text = f.read()

    # Regex to find blocks like: Question from @name ... The Question: "text"
    # This might need slight adjustment based on your exact prompt output
    findings = re.findall(r"Question from (@[\w.]+).*?The Question:\s*\"(.*?)\"", llm_text, re.DOTALL)

    print(f"\n--- VALIDATION REPORT FOR {today_str} ---")
    errors_found = 0
    matches_found = 0

    for author, llm_comment in findings:
        llm_comment = llm_comment.strip()
        
        if author in source_lookup:
            actual_comment = source_lookup[author]
            
            # Use fuzzy matching (checking if the LLM comment is a substring of the source)
            # This handles cases where the LLM might have trimmed a few words
            if llm_comment[:30].lower() in actual_comment.lower():
                matches_found += 1
            else:
                errors_found += 1
                print(f"\n❌ MISMATCH DETECTED: {author}")
                print(f"   LLM Says: {llm_comment[:100]}...")
                print(f"   Source Says: {actual_comment[:100]}...")
        else:
            errors_found += 1
            print(f"\n⚠️ HALLUCINATION: Author {author} not found in source file!")

    print("\n-------------------------------------------")
    print(f"Total Questions Checked: {len(findings)}")
    print(f"✅ Verified Matches: {matches_found}")
    print(f"🚨 Potential Errors: {errors_found}")
    print("-------------------------------------------\n")

    return errors_found == 0

if __name__ == "__main__":
    validate_stumppdogg_output()
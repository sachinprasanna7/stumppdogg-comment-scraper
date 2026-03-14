import os
import re
from datetime import datetime

def validate_and_fix_stumppdogg():
    today_str = datetime.now().strftime("%Y-%m-%d")
    source_path = os.path.join("llm_input_comments", f"{today_str}.txt")
    llm_path = os.path.join("stumppdogg_comments", f"{today_str}.txt")
    corrected_dir = "corrected_stumppdogg_comments"
    os.makedirs(corrected_dir, exist_ok=True)
    corrected_path = os.path.join(corrected_dir, f"{today_str}.txt")

    if not os.path.exists(source_path) or not os.path.exists(llm_path):
        print(f"Error: Files for {today_str} not found.")
        return False

    # 1. Load Source of Truth (Raw Comments)
    # Mapping Author -> Comment Text
    source_lookup = {}
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "Author:" in line and "Comment:" in line:
                try:
                    # Extract Author and Comment using regex to be safe
                    author_match = re.search(r"Author:\s*(@[\w\.-]+)", line)
                    comment_match = re.search(r"Comment:\s*(.*)", line)
                    if author_match and comment_match:
                        author = author_match.group(1).strip()
                        comment = comment_match.group(1).strip()
                        source_lookup[author] = comment
                except Exception:
                    continue

    # 2. Read LLM Output
    with open(llm_path, 'r', encoding='utf-8') as f:
        llm_text = f.read()

    # 3. Robust Regex to find the LLM's pairings
    # This handles hyphens, stars, and different "Question" prefixes
    findings = re.findall(r"Question from\s+(@[\w\.-]+).*?Question[:\s*]+\"(.*?)\"", llm_text, re.DOTALL | re.IGNORECASE)

    if not findings:
        print("🚨 Regex failed to find any questions in the LLM output. Checking format...")
        return False

    print(f"\n--- VALIDATION & AUTO-FIX REPORT ({today_str}) ---")
    
    corrected_text = llm_text
    errors_fixed = 0
    matches = 0

    for author, llm_comment in findings:
        llm_comment_clean = llm_comment.strip()
        
        if author in source_lookup:
            actual_comment = source_lookup[author]
            
            # Check if the LLM's version is significantly different from the source
            # We check if the first 20 characters match (ignoring case/spaces)
            if llm_comment_clean[:20].lower() in actual_comment.lower():
                matches += 1
            else:
                # MISMATCH FOUND: Auto-fix the text in the corrected version
                print(f"🔧 Fixing Mismatch for {author}")
                print(f"   Original LLM: {llm_comment_clean[:50]}...")
                print(f"   Corrected to: {actual_comment[:50]}...")
                
                # Replace the hallucinated comment with the real one in our corrected string
                corrected_text = corrected_text.replace(llm_comment, actual_comment)
                errors_fixed += 1
        else:
            print(f"⚠️ Warning: Author {author} not found in source of truth!")

    # 4. Save the Corrected Version
    with open(corrected_path, 'w', encoding='utf-8') as f:
        f.write(corrected_text)

    print("\n-------------------------------------------")
    print(f"Total Questions Analyzed: {len(findings)}")
    print(f"✅ Verified Matches: {matches}")
    print(f"🛠 Errors Auto-Fixed: {errors_fixed}")
    print(f"📂 Corrected file saved to: {corrected_path}")
    print("-------------------------------------------\n")

    return True

if __name__ == "__main__":
    validate_and_fix_stumppdogg()
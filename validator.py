import os
import re
import difflib

def normalize_text(text):
    """Used ONLY for comparison: removes extra spaces, newlines, and makes lowercase."""
    if not text:
        return ""
    return " ".join(text.strip().split()).lower()

def validate_and_fix_stumppdogg(today_str):
    source_path = os.path.join("llm_input_comments", f"{today_str}.txt")
    llm_path = os.path.join("stumppdogg_comments", f"{today_str}.txt")
    corrected_dir = "corrected_stumppdogg_comments"
    os.makedirs(corrected_dir, exist_ok=True)
    corrected_path = os.path.join(corrected_dir, f"{today_str}.txt")

    if not os.path.exists(source_path) or not os.path.exists(llm_path):
        print(f"Error: Files for {today_str} not found.")
        return False

    # 1. Load Source of Truth as a SET to automatically remove duplicates
    source_comments = set()
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "Author:" in line and "Comment:" in line:
                author_match = re.search(r"Author:\s*(@[\w\.-]+)", line)
                comment_match = re.search(r"Comment:\s*(.*)", line)
                if author_match and comment_match:
                    # Storing as a tuple: (author, comment)
                    source_comments.add((
                        author_match.group(1).strip(),
                        comment_match.group(1).strip()
                    ))

    # 2. Read LLM Output
    with open(llm_path, 'r', encoding='utf-8') as f:
        llm_text = f.read()

    findings = re.findall(r"Question from\s+(@[\w\.-]+).*?Question[:\s*]+\"(.*?)\"", llm_text, re.DOTALL | re.IGNORECASE)

    if not findings:
        print("🚨 Regex failed to find any questions in the LLM output.")
        return False

    print(f"\n{'='*60}")
    print(f"--- VALIDATION & AUTO-FIX REPORT ({today_str}) ---")
    print(f"--- Unique Source Comments Loaded: {len(source_comments)} ---")
    print(f"{'='*60}")
    
    corrected_text = llm_text
    errors_fixed = 0

    # 3. Analyze and Compare
    for idx, (llm_author, llm_comment) in enumerate(findings, 1):
        llm_author = llm_author.strip()
        
        print(f"\n[Question {idx}] Picking comment from LLM generated:")
        print(f"  -> Commenter: {llm_author}")
        print(f"  -> Comment: {llm_comment}")
        print(f"  -> Searching for the comment in source of truth...")
        
        norm_llm_comment = normalize_text(llm_comment)
        
        true_data = None
        best_match = None
        highest_ratio = 0.0

        # Unpacking the tuple from our set
        for src_author, src_comment in source_comments:
            norm_src_comment = normalize_text(src_comment)
            
            # Substring match (Fast & catches perfect truncations)
            if norm_llm_comment in norm_src_comment or norm_src_comment in norm_llm_comment:
                true_data = (src_author, src_comment)
                highest_ratio = 1.0
                break
                
            # Fuzzy match (Slower, catches typos/hallucinations)
            similarity = difflib.SequenceMatcher(None, norm_llm_comment, norm_src_comment).ratio()
            if similarity > highest_ratio:
                highest_ratio = similarity
                best_match = (src_author, src_comment)

        if true_data is None and highest_ratio >= 0.90:
            true_data = best_match

        # 4. Compare and Replace
        if true_data:
            # Unpack the winning tuple
            true_author, true_comment = true_data
            
            print(f"  -> Match found! (Similarity: {highest_ratio:.2%})")
            print(f"  -> Source Commenter: {true_author}")
            print(f"  -> Source Comment: {true_comment}")
            print("  -> Comparing both...")
            
            needs_fix = False
            
            # Check Author
            if llm_author != true_author:
                print(f"     [Action] Fixing Commenter Name. Replacing '{llm_author}' with '{true_author}'")
                corrected_text = corrected_text.replace(llm_author, true_author)
                needs_fix = True
            else:
                print("     [OK] Commenter name matches.")
                
            # Check Comment
            if llm_comment != true_comment:
                print("     [Action] Fixing Comment Text. Overwriting with source of truth.")
                corrected_text = corrected_text.replace(llm_comment, true_comment)
                needs_fix = True
            else:
                print("     [OK] Comment text matches perfectly.")

            if needs_fix:
                errors_fixed += 1
        else:
            print(f"  -> ⚠️ WARNING: No match found! LLM hallucinated this comment.")

    # 5. Save the Corrected Version
    with open(corrected_path, 'w', encoding='utf-8') as f:
        f.write(corrected_text)

    print(f"\n{'='*60}")
    print(f"🛠 Total Errors Auto-Fixed: {errors_fixed}")
    print(f"📂 Final validated file saved to: {corrected_path}")
    print(f"{'='*60}\n")
    return True

# if __name__ == "__main__":
#     from datetime import datetime
#     TODAY_STR = datetime.now().strftime("%Y-%m-%d")
#     validate_and_fix_stumppdogg(TODAY_STR)
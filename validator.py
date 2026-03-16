import os
import re

def validate_and_fix_stumppdogg(today_str):
    source_path = os.path.join("llm_input_comments", f"{today_str}.txt")
    llm_path = os.path.join("stumppdogg_comments", f"{today_str}.txt")
    corrected_dir = "corrected_stumppdogg_comments"
    os.makedirs(corrected_dir, exist_ok=True)
    corrected_path = os.path.join(corrected_dir, f"{today_str}.txt")

    if not os.path.exists(source_path) or not os.path.exists(llm_path):
        print(f"Error: Files for {today_str} not found.")
        return False

    # 1. Load Source of Truth as a list of dictionaries
    source_comments = []
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "Author:" in line and "Comment:" in line:
                author_match = re.search(r"Author:\s*(@[\w\.-]+)", line)
                comment_match = re.search(r"Comment:\s*(.*)", line)
                if author_match and comment_match:
                    source_comments.append({
                        "author": author_match.group(1).strip(),
                        "comment": comment_match.group(1).strip()
                    })

    # 2. Read LLM Output
    with open(llm_path, 'r', encoding='utf-8') as f:
        llm_text = f.read()

    # Find all generated questions and authors
    findings = re.findall(r"Question from\s+(@[\w\.-]+).*?Question[:\s*]+\"(.*?)\"", llm_text, re.DOTALL | re.IGNORECASE)

    if not findings:
        print("🚨 Regex failed to find any questions in the LLM output.")
        return False

    print(f"\n--- VALIDATION & AUTO-FIX REPORT ({today_str}) ---")
    corrected_text = llm_text
    errors_fixed = 0

    for llm_author, llm_comment in findings:
        llm_comment_clean = llm_comment.strip()
        
        # Take the first 30 chars of the LLM comment to use as a search substring
        search_snippet = llm_comment_clean[:30].lower()
        
        true_data = None
        # Loop through source to find matching text
        for src in source_comments:
            if search_snippet in src["comment"].lower() or llm_comment_clean.lower() in src["comment"].lower():
                true_data = src
                break

        if true_data:
            needs_fix = False
            
            # Check if Author is wrong
            if llm_author != true_data["author"]:
                corrected_text = corrected_text.replace(llm_author, true_data["author"])
                needs_fix = True
                
            # Check if Comment was shortened/altered
            if llm_comment_clean != true_data["comment"]:
                # Escaping regex characters in case the comment has question marks/brackets
                safe_llm_comment = re.escape(llm_comment)
                # Replace the hallucinated comment with the true, full comment
                corrected_text = re.sub(safe_llm_comment, lambda _: true_data["comment"], corrected_text)
                needs_fix = True

            if needs_fix:
                print(f"🔧 Fixed hallucination for substring: '{search_snippet}...'")
                errors_fixed += 1
        else:
            print(f"⚠️ Warning: LLM completely hallucinated a comment. Snippet: '{search_snippet}...' not found in source.")

    # 4. Save the Corrected Version
    with open(corrected_path, 'w', encoding='utf-8') as f:
        f.write(corrected_text)

    print(f"🛠 Errors Auto-Fixed: {errors_fixed}")
    print(f"📂 Corrected file saved to: {corrected_path}\n")
    return True
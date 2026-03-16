import os
import csv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def step_three_call_llm(aggregated_filepath, today_str):
    """Sends the aggregated text to GPT-5 and saves the final output."""
    os.makedirs("stumppdogg_comments", exist_ok=True)
    
    with open(aggregated_filepath, 'r', encoding='utf-8') as f:
        raw_comments_data = f.read()
        
    past_questions = []
    kb_path = os.path.join("knowledge_base", "Stumppdogg_Comments.csv")
    
    if os.path.exists(kb_path):
        with open(kb_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Comment' in row and row['Comment'].strip():
                    past_questions.append(row['Comment'].strip())
        print(f"Loaded {len(past_questions)} previous questions from the KB.")
        
    past_questions_formatted = "\n".join([f"- {q}" for q in past_questions])

    prompt = f"""
    I am providing a raw list of YouTube comments from recent videos on the channel "pdoggspeaks". 
    
    ### PREVIOUSLY ANSWERED QUESTIONS (DO NOT REPEAT THESE TOPICS):
    {past_questions_formatted}
    
    **Your Task:**
    Analyze the new list of comments below and extract the Top 10 best questions for #StumpPdogg.
    
    **Selection Criteria:**
    1. Technical Depth
    2. Stories & Experiences
    3. Recent Events & Controversies
    4. Originality (CRITICAL)
    
    **Output Format EXACTLY like this:**
    [Number]. Question from [Author] (Likes: [Number]) [From Video: Actual Video Name]
    * The Question: "[Insert the exact question]"
    
    New comment data:
    {raw_comments_data}
    """

    print("Sending data to GPT-5...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.4", # Upgraded Model
            messages=[
                {"role": "system", "content": "You are an expert cricket analyst. You must extract comments EXACTLY as they are written without summarizing or shortening them."},
                {"role": "user", "content": prompt}
            ],
        )
        
        final_output = response.choices[0].message.content
        final_filepath = os.path.join("stumppdogg_comments", f"{today_str}.txt")
        
        with open(final_filepath, 'w', encoding='utf-8') as f:
            f.write(final_output)
            
        print(f"SUCCESS! Top 10 questions saved to: {final_filepath}")
        return final_filepath
        
    except Exception as e:
        print(f"LLM Error: {e}")
        return None
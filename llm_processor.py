import os
import csv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def call_llm(aggregated_filepath, today_str):
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
        print(f"Loaded {len(past_questions)} previous questions from the Knowledge Base.")
        
    past_questions_formatted = "\n".join([f"- {q}" for q in past_questions])

    prompt = f"""
I am providing a raw list of YouTube comments from recent videos on the channel "pdoggspeaks". Your task is to analyze these comments and extract the Top 10 best questions for our Q&A segment called #StumpPdogg. 

**Context & Knowledge Base:**
To help you understand the exact style, depth, and flavor of questions we look for, here is a list of previously selected #StumpPdogg questions:
### PREVIOUSLY ANSWERED QUESTIONS (DO NOT REPEAT THESE TOPICS):
{past_questions_formatted}
### END OF PREVIOUSLY ANSWERED QUESTIONS

**Your Task:**
Analyze the new list of comments below and extract the Top 10 best questions for our Q&A segment called #StumpPdogg. Take deep inspiration from the Knowledge Base above regarding the quality and technical level required.

**Selection Criteria:**
To make the top 10, a comment MUST be a question, and it should meet either of the first 5 these conditions and must meet the originality and conciseness requirements:
1. **Technical Depth:** Questions that ask for complex technical explanations, deep dives, or advanced problem-solving in cricket.
2. **Stories & Experiences:** Questions that specifically ask Pdogg to explain old incidents, share past career experiences, or tell stories.
3. **Recent Events & Controversies:** Questions that relate to recent cricket events, controversies, or hot topics that are currently being discussed in the cricket world.
4. **Current IPL Season:** Questions that are specifically about the ongoing IPL season, teams, players, strategies, or performances.
5. **Originality (CRITICAL):** Do NOT select a question if it strongly overlaps with a topic already answered in the Knowledge Base above. Be lenient—if it's a completely new angle on a similar topic, it's fine. But avoid obvious duplicates (e.g., if we already answered how rollers affect a pitch, do not pick another generic question about pitch rollers).
6. **Conciseness (NO ESSAYS):** Exclude extremely long, rambling comments, or multi-paragraph essays. If it takes too long to read on screen, drop it.

**Data Structure of New Comments:** The comments are grouped by video. Before each group of comments, there is a header with the video's name enclosed in square brackets, like this:
[Actual_Video_Name_Here]
 
Underneath that header, each comment is provided on a single line:
Author: [Username] | Likes: [Number] | Comment: [Text]

**Output Format:**
Please provide a clean, numbered list (1 to 10). For each selected question, look at the nearest [Actual_Video_Name_Here] header above the comment to identify the video. Do not add any additional text or formatting beyond what is requested. Also, make sure to get the exact question text as it is from raw comments data I am providing you below. Do not summarize or rephrase the questions—provide them exactly as they appear. The output should look exactly like this:

**[Number]. Question from [Author] (Likes: [Number]) [From Video: Actual Video Name]**
* **The Question:** "[Insert the exact question]"

Here is the new comment data to analyze:
{raw_comments_data}
"""

    print("Sending data to GPT-5...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.4", 
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
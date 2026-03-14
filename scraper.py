import os
import re
import glob
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from openai import OpenAI

# 1. Load variables
load_dotenv(override=True)
YT_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not all([YT_API_KEY, CHANNEL_ID, OPENAI_API_KEY]):
    raise ValueError("Missing an API Key or Channel ID in your .env file!")

# Initialize Clients
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)
client = OpenAI(api_key=OPENAI_API_KEY)

# Get today's date for file naming (YYYY-MM-DD)
TODAY_STR = datetime.now().strftime("%Y-%m-%d")

# --- HELPER FUNCTIONS ---

def get_target_videos():
    """Fetches videos published strictly between 48 and 24 hours ago."""
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(hours=48)).isoformat().replace('+00:00', 'Z')
    published_before = (now - timedelta(hours=24)).isoformat().replace('+00:00', 'Z')
    
    print(f"Searching for videos published between {published_after} and {published_before}...")
    
    request = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        publishedAfter=published_after,
        publishedBefore=published_before,
        type="video",
        maxResults=50
    )
    response = request.execute()
    
    videos = []
    for item in response.get('items', []):
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title']
        })
    return videos

def get_video_comments(video_id):
    """Fetches and cleans comments for a specific video."""
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        while request:
            response = request.execute()
            for item in response['items']:
                comment_data = item['snippet']['topLevelComment']['snippet']
                raw_comment = comment_data['textDisplay']
                clean_comment = raw_comment.replace('\n', ' ').replace('\r', ' ')
                
                comments.append({
                    'author': comment_data['authorDisplayName'],
                    'comment': clean_comment,
                    'likes': comment_data['likeCount']
                })
                
            if 'nextPageToken' in response:
                request = youtube.commentThreads().list(
                    part="snippet", videoId=video_id,
                    pageToken=response['nextPageToken'], maxResults=100, textFormat="plainText"
                )
            else:
                break
    except Exception:
        print(f"  Could not fetch comments for {video_id}.")
    return comments

def sanitize_and_format_title(title):
    """Replaces spaces with underscores and removes bad characters."""
    no_spaces = title.replace(' ', '_')
    return re.sub(r'[\\/*?:"<>|]', "", no_spaces)

# --- PIPELINE STEPS ---

def step_one_scrape_and_save():
    """Grabs comments for the target videos and saves them individually."""
    os.makedirs("comments", exist_ok=True)
    target_videos = get_target_videos()
    
    if not target_videos:
        print("No videos found in the 24-48 hour window.")
        return False

    for vid in target_videos:
        print(f"\nProcessing: {vid['title']}")
        comments = get_video_comments(vid['video_id'])
        
        if comments:
            safe_title = sanitize_and_format_title(vid['title'])
            filepath = os.path.join("comments", f"{TODAY_STR}-{safe_title}.txt")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in comments:
                    f.write(f"Author: {item['author']} | Likes: {item['likes']} | Comment: {item['comment']}\n")
            print(f"  Saved {len(comments)} comments to {filepath}")
        else:
            print("  No comments found.")
    return True

def step_two_aggregate_comments():
    """Scans the comments folder for today's files and combines them."""
    os.makedirs("llm_input_comments", exist_ok=True)
    
    # Find all txt files in comments/ that start with today's date
    search_pattern = os.path.join("comments", f"{TODAY_STR}-*.txt")
    todays_files = glob.glob(search_pattern)
    
    if not todays_files:
        print("No comment files found for today to aggregate.")
        return None
        
    aggregated_filepath = os.path.join("llm_input_comments", f"{TODAY_STR}.txt")
    
    with open(aggregated_filepath, 'w', encoding='utf-8') as outfile:
        for file in todays_files:
            # Extract the video name from the filename for the header
            filename = os.path.basename(file)
            video_name = filename.replace(f"{TODAY_STR}-", "").replace(".txt", "")
            
            outfile.write(f"\n[{video_name}]\n\n")
            
            with open(file, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                
    print(f"\nAggregated all of today's comments into: {aggregated_filepath}")
    return aggregated_filepath

def step_three_call_llm(aggregated_filepath):
    """Sends the aggregated text to OpenAI and saves the final output."""
    os.makedirs("stumppdogg_comments", exist_ok=True)
    
    with open(aggregated_filepath, 'r', encoding='utf-8') as f:
        raw_comments_data = f.read()
        
    prompt = f"""
I am providing a raw list of YouTube comments from recent videos on the channel "pdoggspeaks". 

**Data Structure:** The comments are grouped by video under a [VIDEO NAME] header.
Each comment is provided on a single line, formatted exactly like this:
Author: [Username] | Likes: [Number] | Comment: [Text]

**Your Task:**
Analyze this list of comments and extract the Top 10 best questions for a Q&A segment called #StumpPdogg. 

**Selection Criteria:**
To make the top 10, a comment MUST be a question, and it should ideally fall into one of these two categories:
1. **Technical Depth:** Questions that ask for complex technical explanations, deep dives, or advanced problem-solving.
2. **Stories & Experiences:** Questions that specifically ask Pdogg to explain old incidents, share past career experiences, or tell stories.
*Note: You can use the "Likes" count as a secondary signal, but question quality is the most important factor.*

**What to Filter Out (DO NOT INCLUDE):**
* General praise (e.g., "Great video")
* Spam or extremely basic questions
* Statements that are not phrased as questions

**Output Format:**
Please provide a clean, numbered list (1 to 10). For each selected question, format it exactly like this:

**[Number]. Question from [Author] (Likes: [Number]) [From Video: Insert Video Name]**
* **The Question:** "[Insert the exact question]"

Here is the comment data:
{raw_comments_data}
"""

    print("Sending data to OpenAI (this might take 10-20 seconds)...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert content producer and audience researcher for a highly technical YouTube channel."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    
    final_output = response.choices[0].message.content
    final_filepath = os.path.join("stumppdogg_comments", f"{TODAY_STR}.txt")
    
    with open(final_filepath, 'w', encoding='utf-8') as f:
        f.write(final_output)
        
    print(f"\nSUCCESS! Top 10 questions saved to: {final_filepath}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print(f"--- Starting StumpPdogg Daily Run for {TODAY_STR} ---")
    
    # 1. Scrape
    videos_found = step_one_scrape_and_save()
    
    if videos_found:
        # 2. Aggregate
        aggregated_file = step_two_aggregate_comments()
        
        if aggregated_file:
            # 3. Get LLM Output
            step_three_call_llm(aggregated_file)
            
    print("--- Run Complete ---")
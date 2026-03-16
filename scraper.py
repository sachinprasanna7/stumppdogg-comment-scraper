import os
import re
import glob
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from googleapiclient.discovery import build
from openai import OpenAI
import csv
from send_email import dispatch_stumppdogg_email

# 1. Load variables
load_dotenv(override=True)
YT_API_KEY = os.getenv('YOUTUBE_API_KEY')
CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID')

if not all([YT_API_KEY, CHANNEL_ID]):
    raise ValueError("Missing an API Key or Channel ID in your .env file!")

# Initialize Clients
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

def get_target_videos(published_before_hours=24, published_after_hours=48):
    """Fetches videos published strictly between 48 and 24 hours ago."""
    now = datetime.now(timezone.utc)
    published_after = (now - timedelta(hours=published_after_hours)).isoformat().replace('+00:00', 'Z')
    published_before = (now - timedelta(hours=published_before_hours)).isoformat().replace('+00:00', 'Z')

    published_after_indian_time = (now - timedelta(hours=published_after_hours) + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    published_before_indian_time = (now - timedelta(hours=published_before_hours) + timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"Searching for videos published between {published_after_indian_time} and {published_before_indian_time} (Indian Time)...")
    
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
    except Exception as e:
        print(f"Could not fetch comments for {video_id}: {e}")
    return comments

def sanitize_and_format_title(title):
    """Replaces spaces with underscores and removes bad characters."""
    no_spaces = title.replace(' ', '_')
    return re.sub(r'[\\/*?:"<>|]', "", no_spaces)

# --- PIPELINE STEPS ---

def scrape_and_save(TODAY_STR, published_before_hours=24, published_after_hours=48):
    """Grabs comments for the target videos and saves them individually."""
    os.makedirs("comments", exist_ok=True)
    target_videos = get_target_videos(published_before_hours=published_before_hours, published_after_hours=published_after_hours)

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


def aggregate_comments(TODAY_STR):
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
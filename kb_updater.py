import os
import requests
from dotenv import load_dotenv

def update_knowledge_base():
    """Downloads the latest Google Sheet as a CSV and overwrites the local KB."""
    load_dotenv(override=True)
    
    # We will add this to your .env file
    sheet_id = os.getenv('GOOGLE_SHEET_ID')
    
    if not sheet_id:
        print("Pipeline stopped: GOOGLE_SHEET_ID not found in .env")
        return False
        
    print("\n--- Updating Knowledge Base ---")
    print("  -> Fetching latest Stumppdogg_Comments from Google Drive...")
    
    # Google's hidden export URL feature
    # Note: gid=0 pulls the first tab of the spreadsheet. 
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"
    
    try:
        response = requests.get(export_url, timeout=10)
        
        if response.status_code == 200:
            os.makedirs("knowledge_base", exist_ok=True)
            file_path = os.path.join("knowledge_base", "Stumppdogg_Comments.csv")
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            print(f"  -> SUCCESS: Overwrote local KB at {file_path}")
            return True
        else:
            print(f"  -> ERROR: Failed to download sheet. HTTP Status: {response.status_code}")
            print("  -> (Did you make sure the sheet is set to 'Anyone with the link can view'?)")
            return False
            
    except Exception as e:
        print(f"  -> ERROR: Connection failed: {e}")
        return False
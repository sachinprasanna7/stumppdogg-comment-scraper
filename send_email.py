import os
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

def clean_markdown(text):
    """
    Strips out Likes, Video info, and markdown symbols.
    Bolds the @commenter handles.
    """
    # 1. Remove markdown bold stars (**)
    text = text.replace('**', '')
    
    # 2. Remove (Likes: X) - case insensitive
    text = re.sub(r'\(Likes:\s*\d+\)', '', text, flags=re.IGNORECASE)
    
    # 3. Remove [From Video: X] - handles anything inside the brackets
    text = re.sub(r'\[From Video:.*?\]', '', text, flags=re.IGNORECASE)
    
    # 4. Bold the @commenter (finds @ followed by alphanumeric/dots/underscores)
    text = re.sub(r'(@[\w.]+)', r'<b>\1</b>', text)
    
    # 5. Remove the leading bullets (*) from lines
    text = re.sub(r'^\s*\*\s*', '', text, flags=re.MULTILINE)
    
    # 6. Clean up "The Question:" and "Why chosen:" labels
    text = text.replace('The Question:', '<br><b style="color: #d4af37;">Question:</b>')
    text = text.replace('Why chosen:', '<br><b style="color: #666;">Insight:</b>')
    
    # 7. Convert newlines to HTML breaks
    text = text.replace('\n', '<br>')
    
    # 8. Final polish: Remove double breaks if any were created
    text = text.replace('<br><br><br>', '<br><br>')
    
    return text

def dispatch_stumppdogg_email():
    load_dotenv(override=True)
    
    SENDER = os.getenv('EMAIL_SENDER')
    PASSWORD = os.getenv('EMAIL_APP_PASSWORD')
    RECIPIENTS = os.getenv('RECIPIENT_EMAILS', '').split(',')
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    pretty_date = datetime.now().strftime("%d %b %Y")
    file_path = os.path.join("stumppdogg_comments", f"{today_str}.txt")
    
    if not os.path.exists(file_path):
        print(f"Error: Could not find today's file at {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # Apply the new cleaning logic
    html_content = clean_markdown(raw_content)

    # Build the HTML Structure
    html_body = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 20px;">
        <div style="max-width: 650px; margin: auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #eee;">
            
            <div style="background-color: #1a1a1a; padding: 25px; text-align: center;">
                <h1 style="color: #FFD700; margin: 0; font-size: 26px; letter-spacing: 1px;">#StumpPdogg</h1>
                <p style="color: #888; margin: 8px 0 0 0; font-size: 13px; text-transform: uppercase;">Questions for {pretty_date}</p>
            </div>
            
            <div style="padding: 30px; background-color: #ffffff;">
                <div style="font-size: 15px; color: #444;">
                    {html_content}
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #f0f0f0; text-align: center;">
                    <p style="font-size: 11px; color: #bbb;">
                        Automated Analysis • pdoggspeaks Knowledge Base Integration
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"#Stumppdogg Questions - {datetime.now().strftime('%d/%m/%Y')}"
    msg['From'] = SENDER
    msg['To'] = ", ".join(RECIPIENTS)
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.zoho.in', 465) as server:
            server.login(SENDER, PASSWORD)
            server.send_message(msg)
        print(f"Success: Cleaned & bolded email sent for {today_str}")
    except Exception as e:
        print(f"Email failed: {e}")

if __name__ == "__main__":
    dispatch_stumppdogg_email()
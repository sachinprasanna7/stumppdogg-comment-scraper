# 🏏 #StumpPdogg Automated Q&A Pipeline

An automated, end-to-end Python pipeline designed for the **pdoggspeaks** YouTube channel. This project scrapes recent YouTube comments, cross-references them with a historical knowledge base, uses GPT-5 to curate the top 10 best cricket questions for the #StumpPdogg segment, mathematically validates the AI's output to prevent hallucinations, and dispatches a formatted HTML email to the production team.

## ✨ Key Features
* **Smart YouTube Scraping:** Automatically targets videos published within a specific 24-48 hour window and extracts all top-level comments and like counts.
* **Google Sheets KB Sync:** Dynamically pulls the latest historical #StumpPdogg questions from a live Google Sheet to ensure the AI never selects duplicate topics.
* **GPT-5 Curation:** Leverages OpenAI's advanced reasoning model to filter out spam and select high-quality questions based on technical depth, storytelling potential, and recent cricket controversies.
* **Anti-Hallucination Validator:** Uses a dual-engine matching system (Exact Substring + Fuzzy `difflib` matching) to cross-reference the LLM's output with the raw source of truth, automatically fixing hallucinated usernames or truncated comment text.
* **Automated Zoho Dispatch:** Cleans markdown, formats the selected questions into a responsive, branded HTML email, and sends it via an Email Account
* **Persistent Dual-Logging:** Captures all terminal output and error tracebacks, saving them to daily `.log` files for easy debugging during unattended execution.

---

## 📂 Project Structure

```text
YOUTUBE-COMMENT-SCRAPER/
│
├── main.py                   # Central orchestrator & DualLogger setup
├── scraper.py                # Handles YouTube Data API v3 scraping & aggregation
├── kb_updater.py             # Downloads the live Google Sheet as a CSV
├── llm_processor.py          # Constructs the prompt and queries OpenAI GPT-5
├── validator.py              # The anti-hallucination substring & fuzzy search engine
├── send_email.py             # HTML formatter and Zoho SMTP dispatcher
│
├── .env                      # API keys and environment variables (Not tracked in Git)
├── requirements.txt          # Python dependencies
│
├── comments/                         # Raw scrape data per video
├── llm_input_comments/               # Aggregated daily comments (Source of Truth)
├── knowledge_base/                   # Stores Stumppdogg_Comments.csv
├── stumppdogg_comments/              # Raw output directly from GPT-5
├── corrected_stumppdogg_comments/    # Validated & fixed output (Final text)
└── logs/                             # Daily execution logs
```


## ⚙️ The Pipeline Workflow

When main.py is executed, it runs through the following sequential pipeline:

* **Scrape (scraper.py)**: Calculates a strict timezone-aware UTC window (24 to 48 hours ago). Fetches all video IDs published in that window for the pdoggspeaks channel, paginates through the comment threads, and saves them locally.

* **Aggregate (scraper.py)**: Combines all individual video comment files for the day into one master "Source of Truth" file.

* **Update Knowledge Base (kb_updater.py)**: Pings a public Google Sheets export URL to download the absolute latest master list of previously answered questions, overwriting the local CSV.

* **LLM Processing (llm_processor.py)**: Sends the aggregated comments and the historical KB to GPT-5. The model is instructed to strictly select 10 unique, highly technical, or story-driven questions and format them consistently.

* **Validation (validator.py)**: Reads the GPT-5 output and compares every selected question against the Source of Truth.

Step 1: Checks for an exact substring match (to catch perfect truncations).

Step 2: Uses fuzzy string matching (90% similarity threshold) to catch typos or altered words.

Step 3: Overwrites the LLM's text and author handle with the exact original text from the Source of Truth.

* **Dispatch (send_email.py)**: Reads the validated output, strips out ugly markdown and API artifacts (like [From Video: X]), wraps the text in a stylized HTML template, and sends it to the designated recipients via Email
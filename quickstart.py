import os.path
import json
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from passwords import *

# Define required scopes and document ID
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]
DOCUMENT_ID = docID

# Initializes and returns Google API credentials, handling refresh or new login if needed.
def initialize_credentials():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

# Fetches and returns the content of the specified Google Doc.
def fetch_document_content(service):
    if not DOCUMENT_ID:
        raise ValueError("Document ID is not provided")
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    return document.get('body', {}).get('content', [])

# Converts specific Unicode sequences to their corresponding characters.
def convert_unicode_sequences(text):
    return re.sub(r'\\u201', "'", text)

# Converts content into HTML format, handling bold text and line breaks.
def format_html(content):
    content = re.sub(r'/b(.*?)\/b', r'<b>\1</b>', content)
    content = content.replace('\n', '</p><p>')
    return f"<p>{content}</p>"

# Converts content into plain text, removing formatting markers and line breaks.
def format_plain_text(content):
    content = re.sub(r'/b(.*?)\/b', r'\1', content)
    return content.replace('\n', ' ')

# Extracts topics from the document content, returning them as a list of strings.
def extract_topics(body_content):
    topics = []
    current_topic = []
    if body_content:
        for element in body_content:
            paragraph = element.get('paragraph')
            if not paragraph:
                continue
            paragraph_text = ""
            for text_run in paragraph.get('elements', []):
                content = text_run.get('textRun', {}).get('content', "")
                text_style = text_run.get('textRun', {}).get('textStyle', {})
                is_bold = text_style.get('bold', False)
                content = content.strip()
                if content and paragraph_text and not paragraph_text.endswith(" "):
                    paragraph_text += " "
                if is_bold:
                    content = f"/b{content}/b"
                paragraph_text += content
            if paragraph_text:
                if paragraph_text.isupper() or paragraph_text.endswith(":"):
                    if current_topic:
                        topics.append("\n".join(current_topic).strip())
                        current_topic = []
                current_topic.append(paragraph_text)
        if current_topic:
            topics.append("\n".join(current_topic).strip())
    return topics

# Organizes topics into a dictionary with both HTML and plain text formats.
def organize_topics(topics):
    topics_dict = {}
    for topic in topics:
        topic_name = topic.split(":")[0]
        topic_content = topic[len(topic_name) + 1:].strip()
        topic_name = convert_unicode_sequences(topic_name)
        topic_content = convert_unicode_sequences(topic_content)
        html_content = format_html(topic_content)
        plain_text_content = format_plain_text(topic_content)
        topics_dict[topic_name] = {
            "htmlText": html_content,
            "emailText": plain_text_content
        }
    return topics_dict

# Function to generate the JSON data: initializes credentials, fetches content, processes topics, and returns JSON.
def generate_prompts_json():
    creds = initialize_credentials()
    if creds:
        service = build("docs", "v1", credentials=creds)
    else:
        raise RuntimeError("Failed to obtain valid credentials")
    body_content = fetch_document_content(service)
    topics = extract_topics(body_content)
    topics_dict = organize_topics(topics)
    return json.dumps(topics_dict, indent=4, ensure_ascii=False)

#print(generate_prompts_json())

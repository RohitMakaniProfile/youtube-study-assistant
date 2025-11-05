import os
import re
import json
import datetime
import traceback
import uuid
import base64  # <-- NAYA IMPORT (Email ke liye)
from email.mime.text import MIMEText  # <-- NAYA IMPORT (Email ke liye)
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from openai import AzureOpenAI

# --- Naye Google Imports ---
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError  # <-- NAYA IMPORT (Error handling)
from fastapi.templating import Jinja2Templates

from google.cloud import dialogflow_v2 as dialogflow

# .env file se keys load karein
load_dotenv()

# --- Azure OpenAI Setup (waisa hi) ---
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# --- FastAPI App Setup (waisa hi) ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="AAPKA_KOI_BHI_SECRET_KEY")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Google OAuth Setup (UPDATE KIYA GAYA) ---
# --- Google OAuth Setup (UPDATE KIYA GAYA) ---
CLIENT_SECRETS_FILE = 'client_secret.json'
# --- NAYE SCOPES ADD KIYE GAYE ---
SCOPES = [
    'openid',  # <-- BAS YEH LINE ADD KARNI HAI
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/userinfo.email'
]
REDIRECT_URI = 'http://127.0.0.1:8000/auth/callback'

# --- Dialogflow Setup (waisa hi) ---
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'dialogflow_key.json'
try:
    with open('dialogflow_key.json', 'r') as f:
        key_data = json.load(f)
        DIALOGFLOW_PROJECT_ID = key_data['project_id']
except FileNotFoundError:
    print("WARNING: dialogflow_key.json not found. Chatbot functionality will not work.")
    DIALOGFLOW_PROJECT_ID = None


# --- Pydantic Models (waisa hi) ---
class VideoRequest(BaseModel): url: str


class CalendarRequest(BaseModel): summary: str; description: str


class DriveRequest(BaseModel): flashcards: str


class ChatRequest(BaseModel): message: str


# --- Helper Functions (waisa hi) ---
def get_video_id(url: str):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None


# --- AI Helper Functions (waisa hi) ---
def get_ai_summary(transcript: str) -> str:
    try:
        response = client.chat.completions.create(model=deployment_name, messages=[
            {"role": "system", "content": "You are a helpful AI assistant..."},
            {"role": "user", "content": f"Summarize:\n\n{transcript}"}], max_tokens=250)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in get_ai_summary: {traceback.format_exc()}");
        raise e


def get_ai_flashcards(transcript: str) -> str:
    try:
        response = client.chat.completions.create(model=deployment_name, messages=[
            {"role": "system", "content": "You are a helpful AI assistant..."},
            {"role": "user", "content": f"Generate 3-5 flashcards...:\n\n{transcript}"}], max_tokens=300)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in get_ai_flashcards: {traceback.format_exc()}");
        raise e


def get_ai_chat_answer(context_summary: str, question: str) -> str:
    try:
        response = client.chat.completions.create(model=deployment_name,
                                                  messages=[{"role": "system", "content": "You are 'EduTube Coach'..."},
                                                            {"role": "user",
                                                             "content": f"Summary:\n{context_summary}\n\nQuestion: {question}"}],
                                                  max_tokens=200)
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in get_ai_chat_answer: {traceback.format_exc()}");
        raise e


def detect_intent_texts(project_id: str, session_id: str, text: str, language_code: str):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)
    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    return response.query_result


# --- NAYA EMAIL HELPER FUNCTION ---
def create_and_send_message(credentials, to_email: str, subject: str, body_text: str):
    """Gmail service banata hai aur email bhejta hai."""
    try:
        service = build('gmail', 'v1', credentials=credentials)

        message = MIMEText(body_text)
        message['to'] = to_email
        message['subject'] = subject

        # Message ko base64-urlsafe format mein encode karna
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message_body = {
            'raw': encoded_message
        }

        # Email Bhejna
        service.users().messages().send(userId='me', body=create_message_body).execute()
        print(f"Email sent successfully to {to_email}")

    except HttpError as error:
        print(f"An error occurred while sending email: {error}")
    except Exception as e:
        print(f"A general error occurred in send_email: {traceback.format_exc()}")


# --- Frontend Endpoint (waisa hi) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    if 'session_id' not in request.session:
        request.session['session_id'] = str(uuid.uuid4())
    return templates.TemplateResponse("index.html", {"request": request})


# --- API Endpoint: Get Summary (UPDATED) ---
@app.post("/api/process-video")
async def process_video(request: Request, video_request: VideoRequest):
    video_id = get_video_id(video_request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    try:
        api = YouTubeTranscriptApi()
        list_of_all = api.list(video_id)
        try:
            transcript = list_of_all.find_transcript(['en'])
        except NoTranscriptFound:
            try:
                transcript = list_of_all.find_transcript(['hi'])
            except NoTranscriptFound:
                raise Exception("Could not find a transcript in English or Hindi.")

        transcript_data = transcript.fetch()
        full_transcript = " ".join([item.text for item in transcript_data])

        summary = await run_in_threadpool(get_ai_summary, full_transcript)
        flashcards = await run_in_threadpool(get_ai_flashcards, full_transcript)

        request.session['video_summary'] = summary

        # --- NAYA EMAIL BHEJNE KA CODE ---
        email_status = "Email not sent (User not logged in)."
        if 'credentials' in request.session and 'user_email' in request.session:
            try:
                creds_data = request.session['credentials']
                user_email = request.session['user_email']
                credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)

                email_subject = f"Your EduTube Summary for Video ID: {video_id}"
                email_body = f"Hello,\n\nHere is the summary you requested:\n\n---\n{summary}\n---\n\nHere are your flashcards:\n\n{flashcards}"

                # Email ko background mein bhejna taaki user ko wait na karna pade
                await run_in_threadpool(create_and_send_message, credentials, user_email, email_subject, email_body)
                email_status = f"Email notification sent to {user_email}!"

            except Exception as e:
                email_status = f"Failed to send email: {e}"
        # --- END OF NAYA CODE ---

        return {"summary": summary, "flashcards": flashcards,
                "email_status": email_status}  # Email status ko frontend par bhejna

    except Exception as e:
        print("--- ERROR IN /api/process-video ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"FULL TRACEBACK: {traceback.format_exc()}")


# --- Google Login Endpoints ---
@app.get("/login")
async def login():
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true',
                                                      prompt='consent')
    return RedirectResponse(authorization_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    code = request.query_params.get('code')
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # --- NAYA CODE: USER KA EMAIL FETCH KARNA ---
        # Credentials ka istemaal karke user ka email address nikaalna
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        user_email = user_info['email']

        # Credentials aur Email dono ko session mein save karna
        request.session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        request.session['user_email'] = user_email  # <-- EMAIL KO SAVE KIYA
        # --- END OF NAYA CODE ---

        return RedirectResponse(url='/')
    except Exception as e:
        print(f"--- ERROR IN /auth/callback ---")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Authentication failed: {traceback.format_exc()}")


@app.get("/check-auth")
async def check_auth(request: Request):
    # Ab email bhi check kar sakte hain
    if 'credentials' in request.session and 'user_email' in request.session:
        return {"logged_in": True, "email": request.session['user_email']}
    return {"logged_in": False}


# --- Calendar/Drive Endpoints (waisa hi) ---
@app.post("/api/add-to-calendar")
async def add_to_calendar(request: Request, cal_request: CalendarRequest):
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        creds_data = request.session['credentials']
        credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
        service = build('calendar', 'v3', credentials=credentials)
        start_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).isoformat()
        end_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)).isoformat()
        event = {'summary': f"Study: {cal_request.summary[:50]}...", 'description': cal_request.description,
                 'start': {'dateTime': start_time, 'timeZone': 'UTC'},
                 'end': {'dateTime': end_time, 'timeZone': 'UTC'}, }
        service.events().insert(calendarId='primary', body=event).execute()
        return {"message": "Event created successfully!"}
    except Exception as e:
        print(f"--- ERROR IN /api/add-to-calendar ---");
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error adding to calendar: {traceback.format_exc()}")


@app.post("/api/save-flashcards")
async def save_flashcards(request: Request, drive_request: DriveRequest):
    if 'credentials' not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        creds_data = request.session['credentials']
        credentials = Credentials.from_authorized_user_info(creds_data, SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        file_metadata = {'name': 'YouTube Flashcards.txt', 'mimeType': 'text/plain'}
        from io import BytesIO
        from googleapiclient.http import MediaIoBaseUpload
        file_content = drive_request.flashcards.encode('utf-8')
        media = MediaIoBaseUpload(BytesIO(file_content), mimetype='text/plain', resumable=True)
        service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return {"message": "Flashcards saved to Google Drive!"}
    except Exception as e:
        print(f"--- ERROR IN /api/save-flashcards ---");
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving to Drive: {traceback.format_exc()}")


# --- Chatbot Endpoint (waisa hi) ---
@app.post("/api/chat")
async def chat(request: Request, chat_request: ChatRequest):
    if not DIALOGFLOW_PROJECT_ID:
        raise HTTPException(status_code=500, detail="Dialogflow is not configured (key file not found).")
    session_id = request.session.get('session_id', str(uuid.uuid4()))
    user_message = chat_request.message
    try:
        df_response = detect_intent_texts(project_id=DIALOGFLOW_PROJECT_ID, session_id=session_id, text=user_message,
                                          language_code='en')
        intent_name = df_response.intent.display_name
        user_question = df_response.query_text
        summary = request.session.get('video_summary')

        if intent_name in ['ExplainConcept', 'Default Fallback Intent']:
            if not summary:
                return {"reply": "Pehle ek video process karein, taaki main uske context mein jawaab de sakoon."}
            ai_answer = await run_in_threadpool(get_ai_chat_answer, summary, user_question)
            return {"reply": ai_answer}
        else:
            return {"reply": df_response.fulfillment_text}
    except Exception as e:
        print(f"--- ERROR IN /api/chat ---");
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error in chat: {traceback.format_exc()}")
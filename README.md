# 🎓 EduTube Coach — AI-Powered YouTube Study Assistant  
> Transform passive YouTube watching into structured, efficient, & AI-powered learning 🚀  

EduTube Coach ek advanced **AI Study Assistant** hai jo YouTube videos ko **summary, flashcards, study calendar & notes automation** mein convert karta hai.  
Yeh aapki self-study ko **Productive + Organized + AI-powered** bana deta hai — bilkul “Personal AI Tutor” jaisa 👨‍🏫✨  

---

## 🚀 Features

| Feature | Description |
|--------|------------|
🎤 **Auto Transcript Fetching** | Just paste the YouTube URL — transcript extract ho jaata hai  
🧠 **AI Summary (Hindi + English)** | Azure GPT-4 use karke crisp study summary  
📚 **AI Flashcards** | Key concepts → question-answer format for revision  
🗓 **Google Calendar Sync** | Summary ko ek study event ke form mein schedule karein  
📂 **Google Drive Notes Save** | Flashcards as `.txt` saved directly to Drive  
📧 **Gmail Study Email** | Summary + flashcards auto email notification  
🤖 **Context-Aware Study Bot** | Ask questions about the video only — *video-aware LLM chatbot*  
⚡ **FastAPI Backend + JS Frontend** | Lightweight, fast and plug-and-play  

---

## 🧠 Architecture

YouTube URL → Transcript → GPT-4 Summary + Flashcards
↓

Send to Google Calendar (Study Event)

Save Flashcards to Google Drive

Email with Telegram-style notes via Gmail

Smart Chatbot (Dialogflow + GPT-4 context)


---

## 🛠 Tech Stack

### Backend
- **FastAPI**
- **Azure OpenAI GPT-4**
- **YouTube-Transcript-API**
- **Google OAuth 2.0**
- **Google Calendar API**
- **Google Drive API**
- **Gmail API**
- **Dialogflow**

### Frontend
- **HTML + CSS**
- **JavaScript (Fetch API)**

---

## 📁 Project Structure

Youtube-Study-Assistant
├── main.py # FastAPI backend
├── templates/
│ └── index.html # Frontend UI
├── static/
│ ├── style.css
│ └── app.js
├── client_secret.json # Google OAuth credentials
├── dialogflow_key.json # Dialogflow key
├── .env # Azure keys
└── requirements.txt



---

## ⚙️ Setup Guide (Run Locally)

###  1. Clone Repo

```bash
git clone https://github.com/RohitMakaniProfile/youtube-study-assistant)
cd youtube-study-assistant

```
### 2. Virtual Environment
```
python -m venv .venv
# Windows
source .venv/Scripts/activate
# Mac/Linux
# source .venv/bin/activate

```
### 3. Install Requirements
```
pip install -r requirements.txt

```
### 4. Add Keys
```
client_secret.json
dialogflow_key.json

Create .env file:
AZURE_OPENAI_API_KEY=YOUR_KEY
AZURE_OPENAI_ENDPOINT=YOUR_ENDPOINT
AZURE_OPENAI_DEPLOYMENT=YOUR_DEPLOYMENT
AZURE_OPENAI_API_VERSION=2024-12-01-preview

```
5. Start Server
```
uvicorn main:app --reload

```
6. Open App in Browser
```
http://127.0.0.1:8000/
First time use → Click Sign in with Google and give permissions

```
| Step | Action                              |
| ---- | ----------------------------------- |
| 1️⃣  | Paste YouTube URL                   |
| 2️⃣  | Click “Generate Summary”            |
| 3️⃣  | AI creates **summary + flashcards** |
| 4️⃣  | Add to **Google Calendar**          |
| 5️⃣  | Save notes to **Google Drive**      |
| 6️⃣  | Receive **Gmail Study Email**       |
| 7️⃣  | Chat with **AI Tutor about video**  |

```
```
Sample UI Screenshot
```
<img width="1834" height="849" alt="Screenshot 2025-11-05 092417" src="https://github.com/user-attachments/assets/8745bb4d-e667-4490-8b0d-dc12630d13cd" />

<img width="1828" height="812" alt="Screenshot 2025-11-05 092430" src="https://github.com/user-attachments/assets/ee17eaa3-ccdc-4b7f-aa63-0b6050b7c653" />

<img width="1324" height="419" alt="Screenshot 2025-11-05 092504" src="https://github.com/user-attachments/assets/7834e513-f56f-47e9-8b08-3ad9fb99248c" />


```
Contributing
```
Pull requests are welcome!
Ideas & feedback → Raise an issue or DM.




# Personal AI Assistant

A desktop AI assistant with GUI and voice input capabilities.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your Google API key:
```bash
# Copy .env.example to .env and add your key
copy .env.example .env
# Edit .env with your actual API key
```

3. Run the application:
```bash
python main.py
```

## Features
- Text and voice input
- Dark-themed GUI
- Local commands: `hello`, `time`, `open youtube/google/notepad/spotify/wiki`, `bye`
- Gemini LLM fallback for unknown queries
- Non-blocking UI with threading

## Security
- API key is read from `GENAI_API_KEY` environment variable
- Never commit `.env` files to version control
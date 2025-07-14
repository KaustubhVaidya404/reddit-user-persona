# Reddit User Persona Extractor

This Python script extracts public Reddit user activity and generates a comprehensive persona using OpenRouter-hosted LLMs.

## 🚀 Features
- CLI-based Reddit username input
- Limited scraping of recent posts/comments
- Persona generation using OpenRouter API
- Output saved as `.txt` in `out/` folder
- Custom model selection and token-safe prompt construction

## 🛠️ Requirements
- Python 3.8+
- OpenRouter API key


## 🔑 Setup
1. Clone this repository and install dependencies:
```bash
git clone https://github.com/KaustubhVaidya404/reddit-user-persona.git
cd reddit-user-persona
pip install -r requirements.txt
```
2. Create a .env file in the root directory:
```ini
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## 🧑‍💻 Usage
Run with a Reddit username:
```bash
python main.py --username kojied
```
Optional: use a custom model:
```bash
python main.py --username kojied --model mistralai/mixtral-8x7b
```
Output will be saved to:
```bash
out/persona_kojied.txt
```

## 📦 Output Format
Generated persona includes:
- Demographics: age, gender (if inferrable), occupation
- Interests, hobbies, frequent subreddits
- Personality traits, tone, style
- Motivations, frustrations, goals
- Citations from post/comment snippets

## ⚠️ Notes
- Scraping is limited to ~20 text blocks (~10k characters)
- If content exceeds LLM token limits, it’s truncated
- JS-rendered content may be missed (uses requests + bs4)

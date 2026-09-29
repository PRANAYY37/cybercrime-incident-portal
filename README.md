# Cybercrime Incident Classification & Reporting Portal

A beginner-friendly academic project built with Python, Streamlit, SQLite, Pandas, and the OpenAI API.

## Features

1. Incident complaint form
2. AI-based cybercrime category classification
3. Local keyword fallback when no API key is configured
4. AI-generated incident summary
5. SQLite case database
6. Dashboard with category and status statistics
7. Case tracker and status updates
8. CSV export

## Cybercrime categories

- Phishing / Social Engineering
- Online Financial Fraud
- Identity Theft
- Account Compromise
- Malware / Ransomware
- Cyberbullying / Online Harassment
- Data Breach
- Other

## Run on Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, normally:
http://localhost:8501

## OpenAI API

Set the environment variable before starting the app:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
$env:OPENAI_MODEL="gpt-5"
streamlit run app.py
```

If the key is missing or the API request fails, the application automatically uses the local fallback classifier and a local summary.

## Database

The SQLite file `cybercrime.db` is created automatically the first time the app runs.

## Academic demo

Use fictional/demo complaint text. Do not enter real passwords, bank account numbers, OTPs, government ID numbers, or other sensitive personal data.

## Suggested viva questions

- Why is SQLite used?
- Why is Streamlit used?
- What is NLP classification?
- What is the role of Pandas?
- What happens when the OpenAI API is unavailable?
- Why do we keep a fallback classifier?
- What are the limitations of AI-based classification?

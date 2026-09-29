import json
import os
import re
from typing import Dict, List

CATEGORIES = [
    "Phishing / Social Engineering",
    "Online Financial Fraud",
    "Identity Theft",
    "Account Compromise",
    "Malware / Ransomware",
    "Cyberbullying / Online Harassment",
    "Data Breach",
    "Other",
]

KEYWORDS = {
    "Phishing / Social Engineering": [
        "phishing", "fake email", "fake sms", "smishing", "spoof", "otp",
        "verification link", "click the link", "bank message", "fake website"
    ],
    "Online Financial Fraud": [
        "upi fraud", "upi", "payment fraud", "transaction", "money stolen",
        "bank transfer", "card fraud", "debit card", "credit card",
        "investment scam", "loan scam", "financial fraud"
    ],
    "Identity Theft": [
        "identity theft", "aadhaar", "pan card", "stolen identity",
        "impersonation", "used my identity", "identity documents"
    ],
    "Account Compromise": [
        "hacked account", "account hacked", "password changed", "login",
        "unauthorized login", "instagram hacked", "facebook hacked",
        "email hacked", "account takeover"
    ],
    "Malware / Ransomware": [
        "malware", "ransomware", "virus", "trojan", "spyware",
        "encrypted files", "files locked", "malicious software"
    ],
    "Cyberbullying / Online Harassment": [
        "cyberbullying", "harassment", "threatening messages", "online abuse",
        "stalking online", "blackmail", "abusive messages"
    ],
    "Data Breach": [
        "data breach", "database leaked", "customer data leaked",
        "personal data exposed", "records leaked", "information leaked"
    ],
}

def local_classify(text: str) -> Dict:
    normalized = re.sub(r"\s+", " ", text.lower()).strip()
    scores = {category: 0 for category in CATEGORIES}

    for category, words in KEYWORDS.items():
        for word in words:
            if word in normalized:
                scores[category] += 1

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]
    total_score = sum(scores.values())

    if best_score == 0:
        confidence = 0.35
        best_category = "Other"
    else:
        confidence = min(0.95, 0.55 + (best_score / max(total_score, best_score)) * 0.35)

    return {
        "category": best_category,
        "confidence": confidence,
        "reason": "Matched local cybercrime keywords.",
        "mode": "local"
    }

def _openai_client():
    try:
        from openai import OpenAI
        if not os.getenv("OPENAI_API_KEY"):
            return None
        return OpenAI()
    except Exception:
        return None

def ai_classify(text: str) -> Dict:
    client = _openai_client()
    if client is None:
        return local_classify(text)

    model = os.getenv("OPENAI_MODEL", "gpt-5")

    prompt = f"""
You are a cybercrime complaint triage assistant for an educational prototype.

Classify the complaint into exactly one of these categories:
{json.dumps(CATEGORIES)}

Return ONLY valid JSON with these keys:
category: one category from the list
confidence: number from 0 to 1
reason: short explanation

Complaint:
{text}
"""

    try:
        response = client.responses.create(
            model=model,
            input=prompt
        )
        raw = response.output_text.strip()
        data = json.loads(raw)

        if data.get("category") not in CATEGORIES:
            raise ValueError("Invalid category returned by AI.")

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return {
            "category": data["category"],
            "confidence": confidence,
            "reason": data.get("reason", "Classified by OpenAI."),
            "mode": "openai"
        }
    except Exception:
        result = local_classify(text)
        result["reason"] += " OpenAI classification was unavailable, so the local fallback was used."
        return result

def classify_incident(text: str) -> Dict:
    return ai_classify(text)

def generate_summary(text: str, category: str) -> str:
    client = _openai_client()

    if client is None:
        shortened = " ".join(text.split())
        if len(shortened) > 400:
            shortened = shortened[:397] + "..."
        return f"Reported category: {category}. Incident summary: {shortened}"

    model = os.getenv("OPENAI_MODEL", "gpt-5")
    prompt = f"""
Create a short, neutral incident summary for a cybercrime case-management dashboard.

Category: {category}
Complaint: {text}

Write 2-4 sentences. Do not invent names, amounts, dates, evidence, or legal conclusions.
"""
    try:
        response = client.responses.create(
            model=model,
            input=prompt
        )
        return response.output_text.strip()
    except Exception:
        return f"Reported category: {category}. Incident summary: {' '.join(text.split())[:400]}"

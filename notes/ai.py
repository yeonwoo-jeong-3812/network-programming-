import os
import json
from typing import List, Dict

import requests

try:
    from PyPDF2 import PdfReader
except Exception:  # Optional dependency; we will handle if missing at runtime
    PdfReader = None


OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2. Returns empty string on failure."""
    if PdfReader is None:
        raise RuntimeError("PyPDF2가 설치되어 있지 않습니다. pip install PyPDF2 로 설치해주세요.")
    try:
        reader = PdfReader(file_path)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text() or "")
        return "\n".join(texts).strip()
    except Exception as e:
        raise RuntimeError(f"PDF 텍스트 추출 중 오류: {e}")


def _openai_chat(messages: List[Dict[str, str]], temperature: float = 0.2, max_tokens: int = 800) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("환경변수 OPENAI_API_KEY가 설정되어 있지 않습니다.")

    url = f"{OPENAI_API_BASE}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    org_id = os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION")
    project_id = os.getenv("OPENAI_PROJECT_ID") or os.getenv("OPENAI_PROJECT")
    if org_id:
        headers["OpenAI-Organization"] = org_id
    if project_id:
        headers["OpenAI-Project"] = project_id
    payload = {
        "model": OPENAI_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def summarize_text(text: str, language: str = "ko") -> str:
    """Summarize given text into concise bullet points suitable for studying."""
    system = (
        "You are an expert study assistant. Summarize the provided text into concise, well-structured bullet points. "
        "Focus on key concepts, definitions, and important facts. Keep it in the user's language."
    )
    user = (
        f"언어: {language}\n\n다음 텍스트를 학습용 핵심 요약으로 7~10개 불릿으로 정리해줘.\n\n텍스트:\n{text[:12000]}"
    )
    return _openai_chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.2, max_tokens=900)


def generate_ox_quiz(summary: str, num_questions: int = 5, language: str = "ko") -> List[Dict[str, str]]:
    """Generate OX quiz (True/False) from a summary. Returns list of dict with question, answer(bool), explanation."""
    system = (
        "You generate accurate True/False (OX) questions from a given summary. "
        "Each question must be unambiguous and answerable as True or False with a short justification."
    )
    user = (
        f"언어: {language}\n요약을 기반으로 OX 문제 {num_questions}개 만들어줘.\n"
        "각 항목은 JSON 배열 요소로 다음 키를 포함해줘: question, answer, explanation.\n"
        "answer는 True/False 불리언. JSON만 출력.\n\n"
        f"요약:\n{summary[:8000]}"
    )
    content = _openai_chat([
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], temperature=0.3, max_tokens=1200)

    # Try to parse JSON from the model's output
    try:
        data = json.loads(content)
        items = []
        for it in data:
            q = str(it.get("question", "")).strip()
            a = it.get("answer", False)
            if isinstance(a, str):
                a = a.strip().lower() in ("true", "t", "o", "ox", "맞다")
            exp = str(it.get("explanation", "")).strip()
            if q:
                items.append({"question": q, "answer": bool(a), "explanation": exp})
        return items
    except Exception:
        # Fallback: return empty list if parsing fails
        return []

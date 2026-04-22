# ==========================================
# WEB SEARCH MODULE (STABLE VERSION)
# ==========================================

import requests
import os
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

def search_web(query: str) -> list:
    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": False
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        data = response.json()

        results = data.get("results", [])

        structured_results = []

        for r in results[:5]:
            structured_results.append({
                "title": r.get("title", "No Title"),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "source": r.get("source", "Unknown Source")
            })

        return structured_results

    except Exception as e:
        print("[Web Search Error]", e)
        return []
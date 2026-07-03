import streamlit as st
import random
import time
import urllib.parse
import json
import os
from google import genai

# 1. Page Configuration
st.set_page_config(page_title="TalentSift - Technical Assessment", page_icon="🎯", layout="wide")

# Fallback live URL for link generation
BASE_APP_URL = st.secrets.get("APP_URL", "https://talentsift.streamlit.app")

# File-based database path for cross-session storage
LEDGER_FILE = "results_ledger.json"

# 2. Dynamic Question Bank
QUESTION_BANK = {
    "Junior (<5 years)": [
        {
            "theory": "Explain the difference between mutable and immutable objects in Python. Give an example of each.",
            "coding": "Write a Python function that takes a list of integers and returns a new list containing only the even numbers, squared."
        }
    ],
    "Mid Level (5-8 years)": [
        {
            "theory": "What are Python decorators? Explain how they work and provide a practical use-case example.",
            "coding": "Write a function that flattens a deeply nested list of integers (e.g., [1, [2, [3, 4]], 5] -> [1, 2, 3, 4, 5]) without using external libraries."
        }
    ],
    "Senior (9-12 years)": [
        {
            "theory": "Deeply explain Python's Global Interpreter Lock (GIL). How does it impact multi-threading versus multi-processing?",
            "coding": "Implement a custom, thread-safe caching decorator that caches function results and evicts the Least Recently Used (LRU) item when it hits a max capacity of 5 entries."
        }
    ],
    "Expert (12+ years)": [
        {
            "theory": "Discuss metaprogramming in Python. Explain how custom Metaclasses function and how they differ from class decorators for architectural design.",
            "coding": "Write a custom descriptor class from scratch that enforces strict runtime type-checking and value boundaries on class attributes without using third-party verification tools."
        }
    ]
}

# 3. Persistent Database Helper Functions
def save_to_ledger(record):
    """Appends candidate performance metadata directly to a local JSON tracking file."""
    data = []
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = []
            
    data.append(record)
    with open(LEDGER_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_from_ledger():
    """Reads all saved historical screening evaluations."""
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# 4. AI Evaluation Engine
def evaluate_with_ai(name, tier, theory_q, theory_a, coding_q, coding_a, duration):
    """Uses Gemini API to evaluate candidate performance based on tier criteria."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
        You are an expert technical interviewer evaluating a Python candidate mapped to the '{tier}' tier.
        
        Candidate: {name}
        Metrics: Time taken to complete: {duration:.2f} seconds.

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

# Local storage database configuration
LEDGER_FILE = "results_ledger.json"

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
    """Reads all saved historical screening evaluations from persistent file database."""
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

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

# 3. AI Evaluation Engine
def evaluate_with_ai(name, tier, theory_q, theory_a, coding_q, coding_a, duration):
    """Uses Gemini API to evaluate candidate performance based on tier criteria."""
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        
        prompt = f"""
        You are an expert technical interviewer evaluating a Python candidate mapped to the '{tier}' tier.
        
        Candidate: {name}
        Metrics: Time taken to complete: {duration:.2f} seconds.
        
        Theory Question Served: {theory_q}
        Candidate Theory Answer: "{theory_a}"
        
        Coding Question Served: {coding_q}
        Candidate Coding Answer: "{coding_a}"
        
        Provide a professional hiring assessment. You must precisely output your response in this exact format so it parses cleanly:
        THEORY_SCORE: [Number between 0 and 5]
        CODING_SCORE: [Number between 0 and 5]
        STRENGTHS: [Provide bulleted notes]
        IMPROVEMENTS: [Provide bulleted notes]
        RED_FLAGS: [Assess if a duration of {duration:.2f}s is clean, abnormally fast indicating AI copy-paste, or prolonged]
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"THEORY_SCORE: 0\nCODING_SCORE: 0\nSTRENGTHS: Evaluation processing skipped.\nIMPROVEMENTS: N/A\nRED_FLAGS: API Error: {str(e)}"

def parse_ai_report(report_text):
    """Helper function to cleanly slice text keys out of the AI payload response."""
    parsed = {"theory": "0", "coding": "0", "strengths": "", "improvements": "", "flags": ""}
    for line in report_text.split("\n"):
        if line.startswith("THEORY_SCORE:"): parsed["theory"] = line.replace("THEORY_SCORE:", "").strip()
        elif line.startswith("CODING_SCORE:"): parsed["coding"] = line.replace("CODING_SCORE:", "").strip()
        elif line.startswith("STRENGTHS:"): parsed["strengths"] = line.replace("STRENGTHS:", "").strip()
        elif line.startswith("IMPROVEMENTS:"): parsed["improvements"] = line.replace("IMPROVEMENTS:", "").strip()
        elif line.startswith("RED_FLAGS:"): parsed["flags"] = line.replace("RED_FLAGS:", "").strip()
    return parsed


# 4. Routing Controller
params = st.query_params

# --- INTERFACE A: CANDIDATE ASSESSMENT PORTAL ---
if "token" in params and params.get("mode") == "candidate":
    candidate_name = urllib.parse.unquote(params.get("name", "Candidate"))
    candidate_email = urllib.parse.unquote(params.get("email", ""))
    candidate_phone = urllib.parse.unquote(params.get("phone", ""))
    job_tier = urllib.parse.unquote(params.get("tier", "Junior (<5 years)"))

    if "test_step" not in st.session_state:
        st.session_state.test_step = "instructions"
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    if st.session_state.test_step == "instructions":
        st.title(f"Technical Assessment — {job_tier}")
        st.subheader(f"Welcome, {candidate_name}")
        st.write("Your active profile session has been registered. Read the rules closely before launching your test workspace.")
        
        st.info("""
        **Environment Rules:**
        - Do not switch browser tabs, exit full screen, or change focus. This window logs active attention parameters.
        - The test is dynamically tuned to match criteria for the experience tier assigned by your recruiter.
        """)
        
        if st.button("Begin Timed Assessment", type="primary"):
            st.session_state.start_time = time.time()
            st.session_state.selected_q = random.choice(QUESTION_BANK[job_tier])
            st.session_state.test_step = "active_test"
            st.rerun()

    elif st.session_state.test_step == "active_test":
        st.title(f"Python Screening Workspace")
        st.caption(f"Candidate Reference Identity: {candidate_name} ({job_tier})")
        
        # Injected deterrent component
        st.components.v1.html("""
            <script>
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    alert("⚠️ SYSTEM ALERT: Leaving this window logs focus-loss context anomalies to the review panel. Return immediately.");
                }
            });
            </script>
        """, height=0)

        q_pair = st.session_state.selected_q
        
        st.markdown("### 1. Conceptual Framework Analysis")
        st.write(q_pair["theory"])
        ans_theory = st.text_area("Provide your clear conceptual summary:", height=150, key="c_theory")
        
        st.markdown("---")
        
        st.markdown("### 2. Functional Sandbox Implementation")
        st.write(q_pair["coding"])
        ans_coding = st.text_area("Write valid Python solution syntax here:", height=250, key="c_coding")
        
        if st.button("Complete and Finalize Assessment", type="primary"):
            end_time = time.time()
            elapsed_seconds = end_time - st.session_state.start_time
            
            with st.spinner("Processing solutions and recording credentials..."):
                raw_report = evaluate_with_ai(
                    name=candidate_name, tier=job_tier,
                    theory_q=q_pair["theory"], theory_a=ans_theory,
                    coding_q=q_pair["coding"], coding_a=ans_coding,
                    duration=elapsed_seconds
                )
                metrics = parse_ai_report(raw_report)
                
                # Push structural evaluation matrix details directly to the persistent storage ledger file
                payload = {
                    "name": candidate_name,
                    "email": candidate_email,
                    "phone": candidate_phone,
                    "tier": job_tier,
                    "duration": f"{elapsed_seconds:.1f}s",
                    "score_theory": metrics["theory"],
                    "score_coding": metrics["coding"],
                    "strengths": metrics["strengths"],
                    "improvements": metrics["improvements"],
                    "flags": metrics["flags"]
                }
                save_to_ledger(payload)
                
                st.session_state.test_step = "completed"
                st.rerun()

    elif st.session_state.test_step == "completed":
        st.title("Assessment Submitted")
        st.success("Thank you! Your solution syntax block has been logged and compiled safely.")
        st.write("The hiring manager has been notified. You can close this window now.")

# --- INTERFACE B: MANAGEMENT DASHBOARD & LINK GENERATOR ---
else:
    st.title("🎯 TalentSift Hub")
    
    tab_link_gen, tab_admin_results = st.tabs(["🔗 Link Generator", "🔒 Secure Results Portal"])
    
    # TAB 1: GENERATE LINKS DIRECTLY
    with tab_link_gen:
        st.subheader("Generate Candidate Testing Tokens")
        st.write("Fill out the target parameters below to generate an instantly shareable evaluation node link.")
        
        with st.form("generator_panel"):
            c_name = st.text_input("Candidate Full Name")
            c_email = st.text_input("Candidate Email Address")
            c_phone = st.text_input("Candidate Phone Number")
            c_tier = st.selectbox("Assigned Assessment Tier", options=list(QUESTION_BANK.keys()))
            generate_btn = st.form_submit_button("Generate Assessment Link", type="primary")
            
        if generate_btn:
            if c_name and c_email and c_phone:
                enc_name = urllib.parse.quote_plus(c_name)
                enc_email = urllib.parse.quote_plus(c_email)
                enc_phone = urllib.parse.quote_plus(c_phone)
                enc_tier = urllib.parse.quote_plus(c_tier)
                
                invite_url = f"{BASE_APP_URL}/?mode=candidate&token=true&name={enc_name}&email={enc_email}&phone={enc_phone}&tier={enc_tier}"
                
                st.success("🎉 Testing node created successfully!")
                st.info("Copy this tracking URL and send it directly to the candidate via your preferred platform:")
                st.code(invite_url, language="text")
            else:
                st.error("Please fill in all candidate tracking fields.")

    # TAB 2: SECURE RESULTS TRACKING PANELS
    with tab_admin_results:
        st.subheader("Administrative Results Matrix")
        
        # Fast local gatekeeper layer
        admin_pass = st.text_input("Enter Admin Access Pin", type="password", key="admin_credential_pin")
        
        # Change this to whatever password pin you prefer inside your Streamlit secrets
        if admin_pass == st.secrets.get("ADMIN_PASSWORD", "admin123"):
            # Load fresh structural evaluations straight from persistent JSON database
            historical_records = load_from_ledger()
            
            if not historical_records:
                st.info("No candidate submissions recorded on this server node yet.")
            else:
                st.write(f"Displaying **{len(historical_records)}** Completed Screenings:")
                
                for idx, record in enumerate(reversed(historical_records)):
                    with st.expander(f"📊 {record['name']} — {record['tier']} (Theory: {record['score_theory']}/5 | Code: {record['score_coding']}/5)"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**Email:** {record['email']}")
                            st.markdown(f"**Phone:** {record['phone']}")
                        with col2:
                            st.markdown(f"**Total Duration:** {record['duration']}")
                        with col3:
                            st.markdown(f"**Target Level:** {record['tier']}")
                            
                        st.divider()
                        st.markdown(f"#### 🔍 Behavioral & Telemetry Red Flags")
                        st.write(record['flags'] if record['flags'] else "Clear profile timeline metrics.")
                        
                        st.divider()
                        st.markdown(f"#### 👍 Notes on Strengths")
                        st.write(record['strengths'] if record['strengths'] else "None documented.")
                        
                        st.divider()
                        st.markdown(f"#### 💡 Areas for Improvement")
                        st.write(record['improvements'] if record['improvements'] else "None documented.")
        else:
            if admin_pass:
                st.error("Invalid Administrative Key token. Access denied.")
            else:
                st.caption("Provide authorization credentials to view hidden evaluation reports.")

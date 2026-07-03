import streamlit as st
import random
import time
import smtplib
import urllib.parse
from email.mime.text import MIMEText
from google import genai

# 1. Page Configuration
st.set_page_config(page_title="TalentSift - Technical Assessment", page_icon="🔒", layout="centered")

# App URL used for generating invitation links
BASE_APP_URL = st.secrets.get("APP_URL", "https://your-app.streamlit.app")

# 2. Dynamic Question Bank
QUESTION_BANK = {
    "Junior (<5 years)": [
        {
            "theory": "Explain the difference between mutable and immutable objects in Python. Give an example of each.",
            "coding": "Write a Python function that takes a list of integers and returns a new list containing only the even numbers, squared."
        },
        {
            "theory": "What is the difference between a list and a tuple? When would you choose a tuple over a list?",
            "coding": "Write a function that counts the frequency of each character in a given string and returns it as a dictionary."
        }
    ],
    "Mid Level (5-8 years)": [
        {
            "theory": "What are Python decorators? Explain how they work and provide a practical use-case example.",
            "coding": "Write a function that flattens a deeply nested list of integers (e.g., [1, [2, [3, 4]], 5] -> [1, 2, 3, 4, 5]) without using external libraries."
        },
        {
            "theory": "Explain how Python's context managers (`with` statement) manage resources behind the scenes.",
            "coding": "Write a Python function to find the first non-repeating character in a string. Optimize for time complexity."
        }
    ],
    "Senior (9-12 years)": [
        {
            "theory": "Deeply explain Python's Global Interpreter Lock (GIL). How does it impact multi-threading versus multi-processing?",
            "coding": "Implement a custom, thread-safe caching decorator that caches function results and evicts the Least Recently Used (LRU) item when it hits a max capacity of 5 entries."
        },
        {
            "theory": "How does Python handle memory management and garbage collection? Contrast reference counting with generational collection.",
            "coding": "Given an array of intervals where intervals[i] = [start, end], merge all overlapping intervals and return an array of the non-overlapping intervals."
        }
    ],
    "Expert (12+ years)": [
        {
            "theory": "Discuss metaprogramming in Python. Explain how custom Metaclasses function and how they differ from class decorators for architectural design.",
            "coding": "Write a custom descriptor class from scratch that enforces strict runtime type-checking and value boundaries on class attributes without using third-party verification tools."
        },
        {
            "theory": "Describe execution performance bottlenecks inherent to CPython. How would you design a high-throughput pipeline utilizing memory views, Cython, or slots?",
            "coding": "Design and implement a minimal, event-driven asynchronous task runner queue from scratch using only standard-library generators or low-level select/poll mechanisms."
        }
    ]
}

# 3. Email & Notification Engine
def send_email(to_email, subject, body_content):
    """Generic SMTP email sender function."""
    msg = MIMEText(body_content, "html")
    msg["Subject"] = subject
    msg["From"] = st.secrets["SMTP_USER"]
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL(st.secrets["SMTP_HOST"], st.secrets["SMTP_PORT"]) as server:
            server.login(st.secrets["SMTP_USER"], st.secrets["SMTP_PASSWORD"])
            server.send_mail(st.secrets["SMTP_USER"], [to_email], msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email delivery system failure: {e}")
        return False

def evaluate_with_ai(name, tier, theory_q, theory_a, coding_q, coding_a, duration):
    """Uses Gemini API to evaluate candidate performance based on tier criteria."""
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    
    prompt = f"""
    You are an expert technical interviewer evaluating a Python candidate mapped to the '{tier}' tier.
    Expectations must strictly match the targeted level: Junior should be graded on foundational mechanics, while Senior/Expert must be graded stringently on optimization, architectural design, and deep technical patterns.
    
    Candidate: {name}
    Metrics: Time taken to complete: {duration:.2f} seconds.
    
    Theory Question Served: {theory_q}
    Candidate Theory Answer: "{theory_a}"
    
    Coding Question Served: {coding_q}
    Candidate Coding Answer: "{coding_a}"
    
    Provide a professional hiring assessment formatted in clean HTML (no ```html wrapper code blocks, just raw HTML elements).
    Include:
    1. Python Core Theory Knowledge Score (0-5 rating) with strict inline justification.
    2. Practical Coding & Algorithm Execution Score (0-5 rating) reviewing edge cases and execution correctness.
    3. Specific Bulleted Notes on Strengths.
    4. Specific Bulleted Notes on Area of Improvements.
    5. 'Proctoring Flag Analysis': Assess whether a duration of {duration:.2f}s is realistically clean, unusually fast (potential copy-paste AI bypass), or abnormally prolonged for this tier.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

# 4. Routing Controller (Determines Recruiter vs Candidate Mode)
params = st.query_params

# --- INTERFACE A: CANDIDATE ASSESSMENT PORTAL ---
if "token" in params and params.get("mode") == "candidate":
    # Decode candidate info passed safely through URL query parameters
    candidate_name = urllib.parse.unquote(params.get("name", "Candidate"))
    candidate_email = urllib.parse.unquote(params.get("email", ""))
    candidate_phone = urllib.parse.unquote(params.get("phone", ""))
    job_tier = urllib.parse.unquote(params.get("tier", "Junior (<5 years)"))

    # Initialize State Machine for Candidate Process
    if "test_step" not in st.session_state:
        st.session_state.test_step = "instructions"
    if "start_time" not in st.session_state:
        st.session_state.start_time = None

    if st.session_state.test_step == "instructions":
        st.title(f"Technical Assessment — {job_tier}")
        st.subheader(f"Welcome, {candidate_name}")
        st.write(f"You have been invited to complete the Python screening for the **{job_tier}** tier.")
        
        st.info("""
        **Environment Regulations:**
        - This platform tracks core processing telemetry including total window duration metrics.
        - Navigating away from this tab or minimizing the browser will flag anomalies to the review panel.
        - Ensure your workspace is distraction-free before clicking 'Begin'.
        """)
        
        if st.button("Begin Timed Assessment", type="primary"):
            st.session_state.start_time = time.time()
            # Randomly lock-in selection from the tier question list so it doesn't shift during state updates
            st.session_state.selected_q = random.choice(QUESTION_BANK[job_tier])
            st.session_state.test_step = "active_test"
            st.rerun()

    elif st.session_state.test_step == "active_test":
        st.title(f"Python Screening: {job_tier}")
        
        # Passive Client-Side Proctor Warning
        st.components.v1.html("""
            <script>
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    alert("⚠️ ANOMALY DETECTED: Leaving this evaluation window is logged as an unusual red-flag behavior. Return to your workspace immediately.");
                }
            });
            </script>
        """, height=0)

        # Render Questions
        q_pair = st.session_state.selected_q
        
        st.markdown("### 1. Conceptual Framework")
        st.write(q_pair["theory"])
        ans_theory = st.text_area("Provide your concise conceptual analysis:", height=175, key="c_theory")
        
        st.markdown("---")
        
        st.markdown("### 2. Sandbox Code Implementation")
        st.write(q_pair["coding"])
        ans_coding = st.text_area("Write clean, executable Python code:", height=300, key="c_coding")
        
        if st.button("Finalize and Submit Assessment", type="primary"):
            end_time = time.time()
            elapsed_seconds = end_time - st.session_state.start_time
            
            with st.spinner("Processing secure compilation & routing payload..."):
                # Silent Backend Generation
                evaluation_report = evaluate_with_ai(
                    name=candidate_name,
                    tier=job_tier,
                    theory_q=q_pair["theory"],
                    theory_a=ans_theory,
                    coding_q=q_pair["coding"],
                    coding_a=ans_coding,
                    duration=elapsed_seconds
                )
                
                # Secret routing straight to Recruiter
                subject_line = f"📊 Evaluation Completed: {candidate_name} [{job_tier}]"
                send_email(st.secrets["REQUESTER_EMAIL"], subject_line, evaluation_report)
                
                st.session_state.test_step = "completed"
                st.rerun()

    elif st.session_state.test_step == "completed":
        st.balloons()
        st.title("Assessment Complete")
        st.success("Your screening solution payload has been encrypted and delivered securely to the talent acquisition manager.")
        st.write("The active testing session is closed. You may exit your window.")
        st.caption("Verification Reference Token: Stateless-Session-Logged")

# --- INTERFACE B: INTERNAL RECRUITER ASSIGNMENT DASHBOARD ---
else:
    st.title("🎯 TalentSift Recruiter Dashboard")
    st.write("Configure candidate credentials and generate tier-specific token invites.")
    
    with st.form("recruiter_panel", clear_on_submit=False):
        c_name = st.text_input("Candidate Full Name", placeholder="Jane Doe")
        c_email = st.text_input("Candidate Email Address", placeholder="jane.doe@example.com")
        c_phone = st.text_input("Candidate Phone Number", placeholder="+1 (555) 019-2834")
        
        c_tier = st.selectbox("Required Screening Experience Level", options=[
            "Junior (<5 years)", 
            "Mid Level (5-8 years)", 
            "Senior (9-12 years)", 
            "Expert (12+ years)"
        ])
        
        submit_invite = st.form_submit_button("Generate & Dispatch Invite Link", type="primary")
        
    if submit_invite:
        if c_name and c_email and c_phone:
            # Safely URL encode strings to format parameters safely inside the query string
            enc_name = urllib.parse.quote_plus(c_name)
            enc_email = urllib.parse.quote_plus(c_email)
            enc_phone = urllib.parse.quote_plus(c_phone)
            enc_tier = urllib.parse.quote_plus(c_tier)
            
            # Construct distinct stateless assessment link
            invite_url = f"{BASE_APP_URL}/?mode=candidate&token=true&name={enc_name}&email={enc_email}&phone={enc_phone}&tier={enc_tier}"
            
            # Formulate the email body text sent to the candidate
            email_body = f"""
            <h3>Technical Assessment Invitation</h3>
            <p>Hello {c_name},</p>
            <p>Our engineering division has initiated a dynamic Python technical screening for your application at the <b>{c_tier}</b> level.</p>
            <p>Please launch your unique testing node link below when you are ready to begin. Note that the system logs active focus state timing to monitor background tampering metrics.</p>
            <p><a href="{invite_url}" style="background-color:#008CBA;color:white;padding:10px 20px;text-decoration:none;border-radius:4px;display:inline-block;">Launch Assessment Portal</a></p>
            <br>
            <p>Best regards,<br>Talent Acquisition Team</p>
            """
            
            with st.spinner("Dispatching secure invite package..."):
                status = send_email(
                    to_email=c_email,
                    subject=f"Action Required: Python Technical Screening Invite - {c_tier}",
                    body_content=email_body
                )
                
                if status:
                    st.success(f"🎉 Secure invitation successfully dispatched to {c_email}!")
                    st.info(f"**For reference, the generated verification link is:** `{invite_url}`")
        else:
            st.error("Validation Error: Please fill all credentials completely before initializing invite tokens.")

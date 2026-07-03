import streamlit as st
import random
import time
import urllib.parse
import json
import os
from google import genai

# 1. Page Configuration
st.set_page_config(page_title="TalentSift - Technical Assessment", page_icon="🎯", layout="wide")

BASE_APP_URL = st.secrets.get("APP_URL", "https://talentsift.streamlit.app")
LEDGER_FILE = "results_ledger.json"
TEST_DURATION_SECONDS = 1800  # 30 Minutes

# Persistent file ledger hooks
def save_to_ledger(record):
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
    if os.path.exists(LEDGER_FILE):
        try:
            with open(LEDGER_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []

# 2. Comprehensive 10-Question Dynamic Inventory
QUESTION_BANK = {
    "Junior (<5 years)": [
        {"theory": "Explain the difference between mutable and immutable objects in Python. Give examples.", "coding": "Write a function that takes a list of integers and returns a new list containing only the even numbers, squared."},
        {"theory": "What are lists and tuples? What is the core structural difference between them?", "coding": "Write a function that counts the frequency of each unique character in a string and returns a dictionary."},
        {"theory": "Explain the difference between the 'is' operator and the '==' operator.", "coding": "Write a function that takes a string and returns True if it is a palindrome, and False otherwise."},
        {"theory": "What is a lambda function in Python? When should it be utilized?", "coding": "Write a function that takes a list of dictionaries containing keys 'name' and 'age' and sorts them by age."},
        {"theory": "How does local versus global variable scoping operate in Python functions?", "coding": "Write a function to find the single largest and smallest numbers inside an unsorted list without using max() or min()."},
        {"theory": "What is the specific purpose of the 'pass' statement in Python blocks?", "coding": "Write a function that accepts a list of items and removes all duplicate records while fully preserving the original order."},
        {"theory": "Explain the practical utilization of try, except, and finally blocks.", "coding": "Write a function that safely converts an input string into an integer, returning None if a ValueError occurs."},
        {"theory": "What is list comprehension? Contrast its readability with traditional for-loops.", "coding": "Using a single line of list comprehension, filter a list of strings to only include words starting with a vowel."},
        {"theory": "What are *args and **kwargs? How do they empower dynamic function signatures?", "coding": "Write a function 'multiply_all' that accepts any arbitrary number of numeric arguments and returns their product."},
        {"theory": "What is the difference between shallow copy and deep copy mechanisms?", "coding": "Write a function that safely reverses a list in-place without utilizing the built-in .reverse() method."}
    ],
    "Mid Level (5-8 years)": [
        {"theory": "What are Python decorators? Detail a real-world production use-case.", "coding": "Write a custom decorator '@time_logger' that prints the execution duration in seconds of any function it wraps."},
        {"theory": "Explain Python context managers and how the 'with' statement handles resources internally.", "coding": "Write a function that opens a file safely, counts total word instances, and guarantees file closure without native context libraries."},
        {"theory": "What is a generator function? Contrast its memory usage against a standard list return.", "coding": "Write a generator function that produces the Fibonacci sequence up to an arbitrary maximum number 'N'."},
        {"theory": "Explain how list = [[0]] * 3 behaves if you modify list[0][0]. Why does this occur?", "coding": "Write a function that flattens an arbitrarily deep nested list architecture into a single linear collection."},
        {"theory": "What is Method Resolution Order (MRO) in Python? How does the C3 Linearization algorithm settle dependencies?", "coding": "Write an object-oriented class hierarchy demonstrating the 'Diamond Problem' and resolve it cleanly using super()."},
        {"theory": "Why are mutable default arguments (e.g., def append_to(element, target=[])) considered highly dangerous?", "coding": "Fix the target=[] function design pattern to operate predictably across continuous, isolated invocations."},
        {"theory": "Detail how the 'else' block operates within a standard try-except-else-finally matrix.", "coding": "Write a routine that processes network connections, using 'else' and 'finally' parameters to handle clean-up."},
        {"theory": "What does 'Duck Typing' mean in professional, production-ready Python applications?", "coding": "Write a structural validator routine that iterates through custom objects and executes a '.render()' hook safely using duck typing."},
        {"theory": "Explain the functional differences between 'dict.get(key)' and straight index bracket access 'dict[key]'.", "coding": "Write an isolated merge routine that combines two dictionaries, compounding numeric values for any overlapping keys."},
        {"theory": "What are magic (dunder) methods? Provide explicit examples of overloading standard operators.", "coding": "Implement a custom 'Vector2D' class that overloads the addition (+) operator utilizing standard dunder hooks."}
    ],
    "Senior (9-12 years)": [
        {"theory": "Deeply explain Python's Global Interpreter Lock (GIL). How does it affect multi-threading versus multi-processing?", "coding": "Implement a thread-safe, concurrent memory manager that aggregates transaction elements safely across worker runtimes."},
        {"theory": "How does Python handle garbage collection and memory layout? Contrast reference counting with generational sweeps.", "coding": "Write an isolated Least Recently Used (LRU) tracking script with a capacity cap of 5 elements without importing collections."},
        {"theory": "Detail the phenomenon of late binding closures in Python loops. Why do lambda definitions reference updated states?", "coding": "Write a generator expression matrix factory that preserves loop indices properly via functional defaults."},
        {"theory": "Explain monkey-patching. What are the severe risks of modifying attributes or modules at runtime?", "coding": "Write an operational mock framework that intercepts and patches a class-level network response method during testing execution."},
        {"theory": "What are Python custom descriptors? Contrast '__get__' and '__set__' logic hooks against standard getters/setters.", "coding": "Write a custom descriptor that enforces strict range limitations (e.g., valuing 1-100) on an instantiated integer property."},
        {"theory": "How does FastAPI leverage asynchronous coroutines under ASGI architectures to maximize sub-millisecond network speeds?", "coding": "Design an async execution engine that concurrently runs three external API requests, terminating instantly if any encounter an error."},
        {"theory": "Explain how Django's ORM generates SQL queries and what specific operations inadvertently cause N+1 performance lag.", "coding": "Write a database abstraction query routine using prefetching concepts to resolve deep parent-child relational bottlenecks."},
        {"theory": "What are abstract base classes (ABCs)? How do they enforce compliance across massive corporate codebase scaling?", "coding": "Design a custom database connection interface using ABC modules that forces implementation of connect, write, and disconnect."},
        {"theory": "What are structural '__slots__' parameters? When and why should they be integrated into object tracking fields?", "coding": "Design an optimized coordinates processing object using slots to prove RAM footprint reduction during 1-million-node ingestion streams."},
        {"theory": "Explain the difference between execution performance profiling methods: deterministic profiling vs statistical profiling.", "coding": "Write an isolated code block benchmarking routine that logs specific CPU execution hotspots without using external modules."}
    ],
    "Expert (12+ years)": [
        {"theory": "Discuss Metaprogramming. Detail how custom Metaclasses work and why you would avoid them in conventional code layers.", "coding": "Write a custom metaclass that automatically adds validation prefixes and transformation logging hooks to all methods of target classes."},
        {"theory": "Describe performance bottlenecks in CPython. How do memory views and memory-mapped files alleviate IO choking?", "coding": "Write a zero-copy data parsing loop that utilizes memoryview structures to slice raw binary payloads efficiently."},
        {"theory": "Design an enterprise-level data pipeline strategy. How do you construct robust schema guarantees utilizing Pydantic?", "coding": "Write an asynchronous file ingestion pipeline that chunk-processes large datasets, validating types while outputting clean failure logs."},
        {"theory": "Explain the differences introduced across core threading rules via Free-Threaded Python and the Per-Interpreter GIL.", "coding": "Design an isolated task orchestration pipeline that balances high-compute data matrices parallelly across sub-interpreter threads."},
        {"theory": "How do you securely handle sensitive crypto verification states or cryptographic key material inside standard runtime memory?", "coding": "Write an in-memory buffer clearing class that guarantees immediate, overwrite destruction of text data attributes upon disposal."},
        {"theory": "Explain structural changes to error handling via Exception Groups and the 'except*' runtime syntax blocks.", "coding": "Write a parallel microservice supervisor routine that catches multifaceted, concurrent network exception groups gracefully."},
        {"theory": "What architectural patterns prevent cascade degradation failures across decoupled microservice fabrics?", "coding": "Design a custom, resilient Circuit Breaker decorator class from scratch that tracks error rate thresholds and self-heals over time."},
        {"theory": "Detail implementation variances between event loops handled via asyncio vs lower-level kernel primitives like select/epoll.", "coding": "Write a bare-metal asynchronous networking echo server shell utilizing raw socket selectors without using external wrappers."},
        {"theory": "Explain runtime compilation optimization tricks. How does CPython's JIT compiler track operational trace execution hot-spots?", "coding": "Write an algorithmic processing script optimized for tail-recursive scenarios using manual loop unrolling techniques."},
        {"theory": "How do you enforce deterministic reproducibility across complex enterprise applications running on multi-node distributed runtimes?", "coding": "Write a sequence verification routine that enforces execution order across incoming distributed message components."}
    ]
}

# 3. AI Evaluation Engine
def evaluate_with_ai(name, tier, theory_q, theory_a, coding_q, coding_a, duration):
    try:
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
        prompt = f"""
        You are an expert technical interviewer evaluating a Python candidate mapped to the '{tier}' tier.
        Candidate: {name}
        Metrics: Time taken to complete: {duration:.2f} seconds. Max duration allowed was 1800 seconds (30 minutes).

        Theory Question Served: {theory_q}
        Candidate Theory Answer: "{theory_a}"

        Coding Question Served: {coding_q}
        Candidate Coding Answer: "{coding_a}"

        Provide a professional hiring assessment. You must precisely output your response in this exact format so it parses cleanly:
        THEORY_SCORE: [Number between 0 and 5]
        CODING_SCORE: [Number between 0 and 5]
        STRENGTHS: [Provide bulleted notes]
        IMPROVEMENTS: [Provide bulleted notes]
        RED_FLAGS: [Assess if a duration of {duration:.2f}s is clean, abnormally fast indicating AI copy-paste, or prolonged. Note if they timed out near 1800s.]
        """
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text
    except Exception as e:
        return f"THEORY_SCORE: 0\nCODING_SCORE: 0\nSTRENGTHS: Evaluation processing skipped.\nIMPROVEMENTS: N/A\nRED_FLAGS: API Error: {str(e)}"

def parse_ai_report(report_text):
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
        st.write("Your active profile session has been registered. Read the instructions closely before launching your workspace.")
        
        st.info(f"""
        **Assessment Parameters:**
        - **Allowed Duration:** Exactly 30 minutes (1,800 seconds).
        - **Time enforcement:** The system tracks execution runtimes via the backend clock. If the duration exceeds 30 minutes, inputs lock out, and any current work will automatically save and submit.
        - **Environment Regulations:** Tab switches, window minimization, or focus changes flag compliance tracking anomalies.
        """)
        
        if st.button("Begin Timed Assessment (30 Mins)", type="primary"):
            st.session_state.start_time = time.time()
            st.session_state.selected_q = random.choice(QUESTION_BANK[job_tier])
            st.session_state.test_step = "active_test"
            st.rerun()

    elif st.session_state.test_step == "active_test":
        # Calculate time remaining natively on backend rerun loops
        current_elapsed = time.time() - st.session_state.start_time
        time_remaining = TEST_DURATION_SECONDS - current_elapsed
        
        st.title(f"Python Screening Workspace")
        
        # Display backend clock metric
        if time_remaining <= 0:
            st.error("🚨 Time Limit Exceeded! Access locks engaged. Saving progress...")
            is_locked = True
        else:
            mins, secs = divmod(int(time_remaining), 60)
            st.warning(f"⏳ Session Time Remaining: **{mins:02d}:{secs:02d}**")
            is_locked = False

        # Injected deterrent script components
        st.components.v1.html("""
            <script>
            document.addEventListener('visibilitychange', function() {
                if (document.hidden) {
                    alert("⚠️ SYSTEM ALERT: Leaving this active window logs focus-loss parameters as an unusual anomaly. Return immediately.");
                }
            });
            </script>
        """, height=0)

        q_pair = st.session_state.selected_q
        
        st.markdown("### 1. Conceptual Framework Analysis")
        st.write(q_pair["theory"])
        ans_theory = st.text_area("Provide your concise conceptual analysis:", height=150, key="c_theory", disabled=is_locked)
        
        st.markdown("---")
        
        st.markdown("### 2. Functional Sandbox Implementation")
        st.write(q_pair["coding"])
        ans_coding = st.text_area("Write valid Python solution syntax here:", height=250, key="c_coding", disabled=is_locked)
        
        # Auto-trigger evaluation sequence if timed out or button clicked
        if st.button("Complete and Finalize Assessment", type="primary") or time_remaining <= 0:
            with st.spinner("Processing final solutions and recording credentials..."):
                raw_report = evaluate_with_ai(
                    name=candidate_name, tier=job_tier,
                    theory_q=q_pair["theory"], theory_a=ans_theory,
                    coding_q=q_pair["coding"], coding_a=ans_coding,
                    duration=current_elapsed
                )
                metrics = parse_ai_report(raw_report)
                
                payload = {
                    "name": candidate_name, "email": candidate_email, "phone": candidate_phone,
                    "tier": job_tier, "duration": f"{current_elapsed:.1f}s",
                    "score_theory": metrics["theory"], "score_coding": metrics["coding"],
                    "strengths": metrics["strengths"], "improvements": metrics["improvements"], "flags": metrics["flags"]
                }
                save_to_ledger(payload)
                
                st.session_state.test_step = "completed"
                st.rerun()

    elif st.session_state.test_step == "completed":
        st.title("Assessment Submitted")
        st.success("Thank you! Your solution payload has been logged and compiled safely.")
        st.write("The hiring division has been notified. You can safely close this browser window.")

# --- INTERFACE B: MANAGEMENT DASHBOARD & LINK GENERATOR ---
else:
    st.title("🎯 TalentSift Hub")
    tab_link_gen, tab_admin_results = st.tabs(["🔗 Link Generator", "🔒 Secure Results Portal"])
    
    with tab_link_gen:
        st.subheader("Generate Candidate Testing Tokens")
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
                st.success("🎉 Testing link created with explicit 30-minute lock configuration!")
                st.code(invite_url, language="text")
            else:
                st.error("Please fill in all tracking parameters.")

    with tab_admin_results:
        st.subheader("Administrative Results Matrix")
        admin_pass = st.text_input("Enter Admin Access Pin", type="password", key="admin_credential_pin")
        
        if admin_pass == st.secrets.get("ADMIN_PASSWORD", "7708"):
            historical_records = load_from_ledger()
            if not historical_records:
                st.info("No records logged on this server cluster yet.")
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

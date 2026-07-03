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
        admin_pass = st.text_input("Enter Admin Access Pin", type="password")
        
        # Change this to whatever password pin you prefer inside your Streamlit secrets
        if admin_pass == st.secrets.get("ADMIN_PASSWORD", "admin123"):
            if not st.session_state.admin_results_db:
                st.info("No candidate submissions recorded in this active server context loop yet.")
            else:
                st.write(f"Displaying **{len(st.session_state.admin_results_db)}** Completed Screenings:")
                
                for idx, record in enumerate(reversed(st.session_state.admin_results_db)):
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

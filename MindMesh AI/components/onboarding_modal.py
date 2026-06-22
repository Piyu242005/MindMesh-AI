import streamlit as st

@st.dialog("🧠 MindMesh AI", width="large")
def show_onboarding():
    st.markdown("""
    ## Transform Video Courses Into Intelligent Knowledge Networks
    Welcome to MindMesh AI! Your personal, AI-powered learning assistant.
    
    *Developed with ❤️ by **Piyush Ramteke**.*
    """)
    
    st.divider()

    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.subheader("🚀 Quick Tour")
        st.markdown("""
        **1. Upload a Course**
        &rarr; Upload MP4, MKV, or MOV educational videos.

        **2. Process Content**
        &rarr; MindMesh AI extracts audio, transcribes content using Faster-Whisper, and generates semantic embeddings.

        **3. Build Knowledge Base**
        &rarr; All course content is stored in Qdrant Cloud for lightning-fast retrieval.

        **4. Ask Questions**
        &rarr; Chat with your course material using AI-powered semantic search and RAG technology.
        
        **5. Learn Faster**
        &rarr; Search entire courses instantly and get answers with timestamps.
        """)

    with col2:
        st.subheader("📋 Getting Started")
        
        # Determine progress based on file existence and session state
        import os
        videos_exist = len(os.listdir("videos")) > 0 if os.path.exists("videos") else False
        jsons_exist = len(os.listdir("jsons")) > 0 if os.path.exists("jsons") else False
        
        st.markdown(f"""
        {"✅" if videos_exist else "☐"} **Upload First Course**
        {"✅" if jsons_exist else "☐"} **Process Course**
        {"✅" if st.session_state.get("query_count", 0) > 0 else "☐"} **Ask First Question**
        ☐ **Explore AI Chat**
        {"✅" if st.session_state.get("onboarding_completed", False) else "☐"} **Complete Setup**
        """)

        st.markdown("<br/>", unsafe_allow_html=True)
        
        st.info("""
        **Example Questions:**
        - What is web development?
        - Explain Python lists.
        - Where did the instructor explain APIs?
        - Show me the timestamp where CSS Flexbox was discussed.
        """)
        
    st.divider()
    
    st.markdown("""
    **Important Notes:**
    • Upload quality educational videos for best results.
    • Initial processing may take a few minutes.
    • Answers include source references and timestamps.
    • Your knowledge base improves as more courses are added.
    """)

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🚀 Start Exploring", type="primary", use_container_width=True):
            st.session_state["onboarding_completed"] = True
            st.rerun()
    with col_btn2:
        if st.button("📖 View Documentation", use_container_width=True):
            st.session_state["onboarding_completed"] = True
            st.switch_page("pages/getting_started.py")

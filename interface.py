import streamlit as st
import requests

st.set_page_config(page_title="AI Content Engine", page_icon="📝")

st.title("Autonomous Content Generation")
st.markdown("Iterative Writer-Reviewer Loop powered by LangGraph")

# Replace this with your NEW Render URL after deployment
BACKEND_URL = "https://your-project-name.onrender.com/gerar"

tema = st.text_input("Enter the topic for your post:", placeholder="The future of AI in 2026...")

if st.button("Generate Content"):
    if not tema:
        st.warning("Please enter a topic.")
    else:
        with st.spinner("Agents are collaborating (Writing -> Reviewing)..."):
            try:
                response = requests.post(BACKEND_URL, json={"tema": tema})
                if response.status_code == 200:
                    data = response.json()
                    st.subheader("Final Draft")
                    st.success(data["texto_final"])
                    
                    with st.expander("View Reviewer Feedback"):
                        st.write(data["feedback_revisor"])
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Could not connect to backend: {e}")

st.divider()
st.caption("Developed by Bruno Sousa | Powered by LangGraph & Claude 3")
# app.py
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# We must import our src modules after loading the .env so the API key is available
from src.utils import load_candidate_data
from src.graph import app_graph
from src.callbacks import StreamlitCallbackHandler

# --- Streamlit App Configuration ---
st.set_page_config(
    page_title="AI-Powered Hiring Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI-Powered Hiring Assistant")
st.markdown("This app uses a multi-agent system to help you screen a large number of candidates and select a diverse team of 5.")

# --- Main App Logic ---
if "result" not in st.session_state:
    st.session_state.result = None

# "Start Screening" button to trigger the process
if st.button("Start Screening All 974 Candidates", type="primary", use_container_width=True):
    
    # 1. Load the candidate data
    with st.spinner("Step 1/4: Sourcing and parsing candidate profiles..."):
        candidate_data = load_candidate_data("data/form-submissions.json")
        if not candidate_data:
            st.error("Could not load candidate data. Please check the `data/form-submissions.json` file.")
            st.stop()
        
        st.success(f"Step 1/4: Sourcing complete. Found {len(candidate_data)} candidates.")

    # 2. Define the initial state for the graph
    initial_state = {"candidates": candidate_data}

    # 3. Setup UI elements for progress tracking
    progress_bar = st.progress(0, text="Starting the screening process...")
    status_text = st.empty()
    status_text.info("Step 2/4: Screening candidates... This will take a few minutes for all 974 candidates.")
    
    # 4. Setup the custom callback handler to update the UI
    handler = StreamlitCallbackHandler(progress_bar, status_text, len(candidate_data))
    config = {"callbacks": [handler], "recursion_limit": 100} # Set recursion limit high just in case, though not needed for this design
    
    # Invoke the graph. This is a blocking call, but the UI will update via the callback.
    final_state = app_graph.invoke(initial_state, config=config)

    # Final progress updates
    progress_bar.progress(0.75, text="Step 3/4: Analyzing for diversity...")
    st.success("Step 3/4: Diversity analysis complete.")

    progress_bar.progress(0.9, text="Step 4/4: Finalizing recommendations...")
    st.success("Step 4/4: Hiring manager has made the final selection.")
    
    progress_bar.progress(1.0, text="Screening Complete!")
    status_text.success("Screening Complete! Results are displayed below.")
    
    # Store the final result in the session state to persist it
    st.session_state.result = final_state.get('final_selection')

# --- Display the results ---
if st.session_state.result:
    st.header("🏆 Top 5 Recommended Candidates")
    st.markdown("Here are the top 5 candidates selected by our AI-powered hiring assistant, balancing skills, experience, and diversity.")

    selection = st.session_state.result
    
    # Load original data again to display richer candidate cards
    all_candidates_data = load_candidate_data("data/form-submissions.json")
    candidate_map = {c['name']: c for c in all_candidates_data}
    
    for i, name in enumerate(selection.selected_candidates):
        st.subheader(f"{i + 1}. {name}")
        
        candidate_info = candidate_map.get(name, {})
        
        # Create columns for a cleaner layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if candidate_info:
                st.markdown(f"**📍 Location:** {candidate_info.get('location', 'N/A')}")
                st.markdown(f"**🎓 Education:** {candidate_info.get('education', {}).get('highest_level', 'N/A')}")
                st.markdown(f"**🏢 Experience:** {candidate_info.get('work_experiences', [{}])[0].get('roleName', 'N/A')}")
                st.markdown(f"**🛠️ Top Skills:** {', '.join(candidate_info.get('skills', ['N/A'])[:3])}")

        with col2:
            with st.container(border=True):
                st.markdown("**🧠 Why they were chosen:**")
                st.info(selection.summaries[i])
        
        st.divider()
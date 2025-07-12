# src/callbacks.py
import streamlit as st
from langchain_core.callbacks.base import BaseCallbackHandler

class StreamlitCallbackHandler(BaseCallbackHandler):
    """A custom callback handler to update the Streamlit UI with progress."""
    def __init__(self, progress_bar, status_text, total_items):
        self.progress_bar = progress_bar
        self.status_text = status_text
        self.total = total_items
        self.processed = 0

    def on_agent_step(self):
        """Called by the agent after processing each item."""
        self.processed += 1
        progress = self.processed / self.total
        self.progress_bar.progress(min(progress, 1.0), text=f"Step 2/4: Screening candidate {self.processed} of {self.total}...")
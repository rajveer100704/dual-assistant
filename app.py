"""
HuggingFace Spaces entry point.
HF Spaces looks for app.py in the repo root.
This file simply re-exports the Streamlit app.
"""
# HF Spaces runs: streamlit run app.py
# So we import and re-export the Streamlit frontend.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Import triggers module-level registration in Streamlit
from app.frontend.streamlit_app import *  # noqa: F401, F403

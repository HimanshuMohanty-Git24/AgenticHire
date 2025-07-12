# src/visualize_graph.py
import os
import sys

# --- START OF FIX ---
# Corrected import path for MermaidDrawMethod. It's in the 'graph' submodule.
# --- END OF FIX ---

# Add the parent directory to the Python path to allow for package-like imports
# This is necessary to run this script directly and have it find `src.graph`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph import app_graph

def generate_graph_diagram():
    """
    Compiles the LangGraph workflow and generates a PNG image of the architecture
    using a reliable local rendering method, similar to the notebook example.
    """
    try:
        # Get the compiled graph object from your graph definition file
        graph = app_graph

        # Generate the PNG image data using the local PYPPETEER method.
        # This avoids the external API call error and works reliably in a script.
        png_data = graph.get_graph().draw_mermaid_png(
            method="pyppeteer",
            # Specify the output format as PNG
            format="png",
            # Use a larger scale for better resolution
            scale=2.0,
            # Set the width and height for the image
            width=1200,
            height=800,
        )

        # Define the output path in the project's root directory
        output_path = os.path.join(os.path.dirname(__file__), '..', 'workflow_diagram.png')

        # Save the generated PNG image to the file
        with open(output_path, "wb") as f:
            f.write(png_data)

        print(f"✅ Successfully generated graph diagram and saved it to: {output_path}")

    except ImportError as ie:
        if 'pyppeteer' in str(ie):
            print("\n---")
            print("🔴 Error: `pyppeteer` is not installed. This package is required for local rendering.")
            print("Please install it by running: `pip install pyppeteer`")
            print("---\n")
        else:
            print(f"\n---")
            print(f"🔴 An import error occurred: {ie}")
            print("Please ensure all dependencies from requirements.txt are installed.")
            print("---\n")
    except Exception as e:
        print(f"\n---")
        print(f"🔴 An unexpected error occurred during rendering: {e}")
        print("This may be related to the pyppeteer/Chromium installation.")
        print("Try running `pyppeteer-install` from your terminal if issues persist.")
        print("---\n")


if __name__ == "__main__":
    print("🚀 Generating LangGraph workflow diagram using local renderer...")
    generate_graph_diagram()
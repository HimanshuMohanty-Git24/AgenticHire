# src/utils.py
import json
from typing import List, Dict, Any

def load_candidate_data(filepath: str) -> List[Dict[str, Any]]:
    """Loads candidate data from a JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {filepath} was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: The file {filepath} is not a valid JSON file.")
        return []
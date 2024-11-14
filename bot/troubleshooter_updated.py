# troubleshooter.py
# Purpose: Backend program for managing cell improvement requests in a Jupyter Notebook.
#          Supports the enhanced troubleshooting interface in the notebook.

import nbformat
import os
import requests
from dotenv import load_dotenv

# Load API credentials (assuming Gemini or ChatGPT API keys)
load_dotenv("chatgpt_credentials.env")
CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")

# Define paths for the notebook files and output drafts
notebook_path = "BitBot_Notebook.ipynb"  # Path to the notebook being improved
updated_notebook_path = "BitBot_Notebook_Updated.ipynb"  # Path to save the updated notebook
output_dir = "drafts/"  # Directory to save draft improvements

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)


# ========== Helper Functions ==========

def load_notebook(path):
    """Loads the notebook content from a specified file path."""
    with open(path, 'r', encoding='utf-8') as f:
        return nbformat.read(f, as_version=4)

def save_notebook(notebook, path):
    """Saves the notebook to a specified path."""
    with open(path, 'w', encoding='utf-8') as f:
        nbformat.write(notebook, f)

def preview_cell_content(notebook, cell_indices):
    """Displays a preview of the content for specified cell indices."""
    previews = {}
    for idx in cell_indices:
        if idx < len(notebook.cells):
            previews[idx] = notebook.cells[idx].source[:150]  # Preview first 150 chars
    return previews

def ask_chatgpt(prompt):
    """Requests code improvement suggestions from ChatGPT API."""
    headers = {
        'Authorization': f'Bearer {CHATGPT_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")


# ========== Main Troubleshooting Function ==========

def troubleshoot_cell(cell_index, action):
    """
    Troubleshoot or improve the content of a specified cell.
    
    Parameters:
    - cell_index (int): Index of the cell to troubleshoot or improve.
    - action (str): Description of the action to take (e.g., 'Custom prompt', 'Create New Cell').
    """
    # Load the notebook
    notebook = load_notebook(notebook_path)
    
    # Ensure the cell index is within range
    if cell_index >= len(notebook.cells):
        print(f"[ERROR] Cell index {cell_index} is out of range.")
        return
    
    # Generate the improvement prompt based on the specified action
    if action == "Create New Cell":
        prompt = "Generate a new cell that fulfills the project's objectives."
    elif action == "Modify Cell(s)":
        prompt = "Make improvements to this cell's content and optimize its code."
    elif action == "Create Documentation":
        prompt = "Add comprehensive documentation and comments for clarity."
    else:
        prompt = action  # Use the custom prompt directly
    
    # Append the cell content to the prompt for context
    cell_content = notebook.cells[cell_index].source
    full_prompt = f"{prompt}\n\nCurrent Cell Content:\n{cell_content}"
    
    # Request improvements from ChatGPT
    try:
        suggested_code = ask_chatgpt(full_prompt)
    except Exception as e:
        print(f"[ERROR] Failed to request improvement: {e}")
        return
    
    # Apply the improved content to the cell
    notebook.cells[cell_index].source = suggested_code
    print(f"[INFO] Cell {cell_index} updated successfully with '{action}' action.")
    
    # Save the improved notebook
    save_notebook(notebook, updated_notebook_path)
    print(f"[INFO] Updated notebook saved as '{updated_notebook_path}'.")


# ========== Batch Troubleshooting Interface ==========

def start_batch_troubleshooting(selected_docs, cell_indices, action):
    """
    Runs troubleshooting for a batch of cells based on user-selected documents, cells, and action.
    
    Parameters:
    - selected_docs (list): List of selected documents to include in troubleshooting.
    - cell_indices (list): Indices of the cells to troubleshoot.
    - action (str): The action to apply to the cells.
    """
    # Load notebook and prepare to apply actions to selected cells
    notebook = load_notebook(notebook_path)
    
    # Confirm selected documents (for logging and tracking purposes)
    print(f"[INFO] Troubleshooting session for documents: {selected_docs}")
    
    # Preview selected cells if requested
    previews = preview_cell_content(notebook, cell_indices)
    for idx, content in previews.items():
        print(f"[Cell {idx} Preview]: {content}...")

    # Apply the chosen action to each selected cell
    for cell_index in cell_indices:
        troubleshoot_cell(cell_index, action)

    # Final confirmation message
    print(f"[INFO] Troubleshooting session completed. The updated notebook is saved at {updated_notebook_path}")

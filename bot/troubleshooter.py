troubleshooter.py
import requests
import nbformat
import shutil
import os

# Define API settings (Replace `YOUR_API_KEY` with your OpenAI API key)
API_KEY = 'YOUR_API_KEY'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'

# Notebook paths for original and updated versions
original_notebook_path = "BitBot_Notebook.ipynb"
updated_notebook_path = "BitBot_Notebook_Updated.ipynb"

# Ensure the updated notebook file is created based on the original if it doesn't exist
if not os.path.exists(updated_notebook_path):
    shutil.copyfile(original_notebook_path, updated_notebook_path)

# Load the updated notebook
def load_notebook(path):
    with open(path, 'r', encoding='utf-8') as nb_file:
        return nbformat.read(nb_file, as_version=4)

# Save the notebook with updated cells
def save_notebook(notebook, path):
    with open(path, 'w', encoding='utf-8') as nb_file:
        nbformat.write(notebook, nb_file)

# Function to call ChatGPT and ask for code improvements
def ask_chatgpt(prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    response = requests.post(ENDPOINT, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")

# Recursive function to iteratively improve the selected cell
def troubleshoot_cell(cell_index, max_iterations=5):
    notebook = load_notebook(updated_notebook_path)
    code = notebook.cells[cell_index].source  # Original code of the cell
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n===== Iteration {iteration} =====")
        
        # Request improvement suggestions from ChatGPT
        prompt = f"This is iteration {iteration}. Improve the following code:\n\n{code}"
        improved_code = ask_chatgpt(prompt)
        
        # Display original vs improved code
        print("Original Code:\n", code)
        print("\nImproved Code:\n", improved_code)
        
        # Request user input for feedback and approval
        user_feedback = input("Do you approve this improvement? (yes/no) ")
        if user_feedback.lower() == 'yes':
            # Test the improved code
            try:
                exec(improved_code)  # Execute the code (use with caution)
                print("Code executed successfully.")
                # Update notebook with improved code
                notebook.cells[cell_index].source = improved_code
                save_notebook(notebook, updated_notebook_path)
                print(f"Notebook cell {cell_index} saved successfully to {updated_notebook_path}.")
                code = improved_code  # Update the code for the next iteration
            except Exception as e:
                print("Code execution failed:", e)
                tips = input("Provide tips or describe the issue for the next iteration: ")
                prompt = f"Refine the code based on this feedback:\n{tips}\n\nOriginal Code:\n{code}\n\nImproved Code:\n{improved_code}"
        else:
            tips = input("Provide tips or specific issues for the next iteration: ")
            prompt = f"Refine the code based on this feedback:\n{tips}\n\nOriginal Code:\n{code}\n\nImproved Code:\n{improved_code}"
    
    print("\nFinal Code for cell", cell_index, ":\n", code)
    return code

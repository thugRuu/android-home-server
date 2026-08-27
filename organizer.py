import os
import shutil
from pathlib import Path

def organize_file(file_path, target_base_dir):
    """
    Reads a file's content, determines a category folder based on keywords 
    or content length, and moves it into that folder. Creates the folder if missing.
    """
    path = Path(file_path)
    target_base = Path(target_base_dir)

    if not path.exists():
        print(f"File not found: {file_path}")
        return

    # 1. Read the content of the file
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Could not read file as text: {e}")
        return

    # 2. Logic to determine the best folder name based on content
    folder_name = "general"
    lower_content = content.lower()

    if "python" in lower_content or "javascript" in lower_content or "code" in lower_content:
        folder_name = "code"
    elif "invoice" in lower_content or "bill" in lower_content or "price" in lower_content:
        folder_name = "finance"
    elif "note" in lower_content or "todo" in lower_content or "reminder" in lower_content:
        folder_name = "notes"
    elif len(content) > 500:
        folder_name = "documents"

    # 3. Define the destination folder path
    dest_folder = target_base / folder_name

    # 4. Create the folder if it does not exist
    dest_folder.mkdir(parents=True, exist_ok=True)

    # 5. Move the file into the folder
    dest_path = dest_folder / path.name
    shutil.move(str(path), str(dest_path))

    print(f"Successfully moved '{path.name}' to folder: '{folder_name}/'")

# Example Usage:
if __name__ == "__main__":
    # Create a dummy text file to test
    test_file = "sample_note.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("Remember to check the python script for the home server automation.")

    # Organize it into your uploads/ media folder
    organize_file(test_file, "./uploads")
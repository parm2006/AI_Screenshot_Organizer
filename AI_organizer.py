#python3 run.py .\AI_org\AI_organizer.py 3

import os
import re
import sys
from pathlib import Path
from google import genai
from dotenv import load_dotenv
import time as timecd

from AI_organizer_helpers import (
    SCREENSHOTS_DIRECTORY,
    rename_and_move_screenshot,
    list_categories,
    get_newest_screenshot,
    create_directory,
)

load_dotenv()
print("Starting AI Client")
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

inp = 0
# In main script, before the while loop:
screenshot_files = sorted(
    [f for f in os.listdir(SCREENSHOTS_DIRECTORY) if f.endswith('.png')],
    key=lambda f: os.path.getctime(os.path.join(SCREENSHOTS_DIRECTORY, f))  # Newest first
)
categories_cache = set(cat for cat in list_categories().strip().split('\n') if cat)

num_to_process = min(int(sys.argv[1]), len(screenshot_files))
print(f"Processing {num_to_process} images")
while(inp < int(sys.argv[1])):

    if not screenshot_files:
        print("No screenshots remaining")
        break
    
    newest_screenshot = screenshot_files.pop(0) 

    try:
        screenshotfile = client.files.upload(file=os.path.join(SCREENSHOTS_DIRECTORY, newest_screenshot))
    except Exception as e:
        print(f"Failed to upload {newest_screenshot}: {e}")
        continue

    combined_prompt = f"""
    Generate a new descriptive filename for the provided screenshot. They should all remain as .pngs
    Then, decide if the screenshot belongs in an existing category or if a new category should be created.
    The existing categories are: {', '.join(sorted(categories_cache))}.
    Only create a new category if absolutely necessary and keep the format consistent.
    If the screenshot is blank (solid color) or empty, the category must be 'trash'.  
    Personl User recommendations:
    Most of my cad screenshots belong to my eagle project if they are of a bench or a thing that holds up a box with 4 legs

    Output ONLY the new filename, followed immediately by a single pipe character '|', and then the category.
    Example Output Format: descriptive_filename_for_image|CategoryName
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash", # Use the desired model
        contents=[combined_prompt, screenshotfile]
    )

    filename, category = response.text.strip().split('|')
    #strip category name
    category = re.sub(r'[<>:"/\\|?*]', "_", category)
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    if not filename.lower().endswith('.png'):
        filename = filename + '.png'

    category_path = os.path.join(SCREENSHOTS_DIRECTORY, category)

    if not os.path.exists(category_path):
        print(f"Creating new folder: {category_path}")
        create_directory(category)
        categories_cache.add(category)

    dest_relative = os.path.join(category, filename)

    print(f"Moving {filename}:\n  TO:  {category_path}")
    rename_and_move_screenshot(newest_screenshot, dest_relative)
    
    #time.sleep(1)
    
    inp +=1
    print(f"Processed {inp}/{num_to_process}")
print("Finished")
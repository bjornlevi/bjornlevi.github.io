import os
import re
import random
from datetime import datetime
import openai
import hashlib

def generate_lng_pair(title):
    # This function generates a unique lng_pair based on the filename
    hash_object = hashlib.sha256(title.encode())
    return "id_" + hash_object.hexdigest()[:10]

def get_boolean_input(prompt):
    true_values = {'true', 't', '1', 'yes', 'y'}
    false_values = {'false', 'f', '0', 'no', 'n'}

    while True:
        user_input = input(prompt).lower()  # Convert to lower case to make the check case-insensitive

        if user_input in true_values:
            return True
        elif user_input in false_values:
            return False
        else:
            print("Please enter a valid response (e.g., 'yes' or 'no').")

def translate_text(api_key, text, target_languages):
    openai.api_key = api_key

    translations = {}
    for language in target_languages:
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "user",
                        "content": f"Translate the following text to {language}: '{text}'"
                    },
                ]
            )
            translation = response.choices[0].message.content
            translations[language] = translation
        except Exception as e:
            print(f"An error occurred: {e}")
            translations[language] = "Error in translation"

    return translations

def sanitize_title(title):
    # Remove unsafe characters for filenames
    return re.sub(r'[^a-zA-Z0-9_-]', '', title.replace(' ', '-').lower())

def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def create_new_post(language_folders):
    api_key = input("API key: ")
    title = input("Enter the title of the post: ")
    category = input("Enter the category of the post: ")
    file_path = input("Enter the path to the text file for the post: ")
    translate = get_boolean_input("Translate: True/False? ")
    post_id = generate_lng_pair(title)
    
    original_text = read_file_content(file_path)
    if original_text is None:
        return  # Exit if file reading fails

    # Save the original version
    img_number = random.randint(1, 10)  # Random image selection
    sanitized_title = sanitize_title(title)
    img_filename = f":post_pic{img_number}.jpg"
    file_date = datetime.now().strftime('%Y-%m-%d')
    filename = f"{file_date}-{sanitized_title}.markdown"
    original_file_path = os.path.join('_posts/', filename)

    # Define the template with user inputs
    template = f"""---
lng_pair: {post_id}
title: {title}
author: Björn Leví Gunnarsson
category: {category}
tags: [tag1, tag2]
img: "{img_filename}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{original_text}
"""

    with open(original_file_path, 'w', encoding='utf-8') as file:
        file.write(template)

    print(f"Original file created: {original_file_path}")

    if translate: #translate using ChatGPT API
        # Translate the title and text
        translated_titles = translate_text(api_key, title, list(language_folders.keys()))
        translated_texts = translate_text(api_key, original_text, list(language_folders.keys()))

        for language in language_folders:
            translated_title = translated_titles.get(language, "Error in title translation")
            translated_text = translated_texts.get(language, "Error in text translation")
            folder = language_folders[language]
            file_path = os.path.join(folder, filename)

            # Define the template with user inputs
            template = f"""---
lng_pair: {post_id}
title: {translated_title}
author: Björn Leví Gunnarsson
category: {category}
tags: [tag1, tag2]
img: "{img_filename}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{translated_text}
"""
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(template)

            print(f"File created in {language}: {file_path}")

    else: #create empty posts
        # Translate the title and text
        title = "New article - placeholder"
        text = "Lorem ipsum - placeholder"

        for language in language_folders:
            folder = language_folders[language]
            file_path = os.path.join(folder, filename)

            # Define the template with user inputs
            template = f"""---
lng_pair: {post_id}
title: {title}
author: Björn Leví Gunnarsson
category: {category}
tags: [tag1, tag2]
img: "{img_filename}"
date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
---

{text}
"""
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(template)

            print(f"File created in {language}: {file_path}")


# Usage
language_folders = {
    "Spanish": 'es/_posts/',
    "Ukrainian": 'uk/_posts/',
    "Polish": 'pl/_posts/',
    "English": 'en/_posts/',
}

create_new_post(language_folders)

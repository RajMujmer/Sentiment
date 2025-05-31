import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import streamlit as st
from typing import List, Tuple, Union
import string
import requests
from bs4 import BeautifulSoup
import os
import pickle
import spacy
import nltk

def about():
    # Load spaCy model only once when the function is called
    nlp1 = spacy.load("en_core_web_sm")

    input_type = st.radio(
        "Select Input Method:", ["Text Input", "URL Analysis"], key="input_type_radio")

    text_to_analyze = "" # Renamed for clarity, will hold the content for spaCy

    if input_type == "Text Input":
        text_to_analyze = st.text_area("Enter the text to analyze:", height=200, key="text_input_area")
    elif input_type == "URL Analysis":
        url = st.text_input("Enter the URL to analyze:", key="url_input")
        if url: # Only proceed if a URL is provided
            try:
                # Fetch the content from the URL
                response = requests.get(url)
                response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

                # Parse the HTML content
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract all readable text from the parsed HTML
                # You can customize this to extract text from specific tags if needed
                text_to_analyze = soup.get_text(separator=' ', strip=True)
                st.success("Successfully fetched text from URL.")

            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching URL: {e}. Please check the URL.")
                text_to_analyze = "" # Clear content if there was an error
            except Exception as e:
                st.error(f"An unexpected error occurred during URL processing: {e}")
                text_to_analyze = ""

    # --- Processing the text with spaCy ---
    if text_to_analyze: # Only process if there's actual text
        st.subheader("Text Analysis Results:")
        doc = nlp1(text_to_analyze)

        st.write("### Sentences:")
        # Correctly iterate over spaCy's sentence segments
        for i, sentence in enumerate(doc.sents):
            st.write(f"Sentence {i+1}: {sentence.text.strip()}") # .strip() to remove leading/trailing whitespace

        st.write("### Named Entities:")
        if doc.ents:
            for ent in doc.ents:
                st.write(f"Entity: **{ent.text}** (Label: {ent.label_})")
        else:
            st.write("No named entities found.")

        st.write("### Tokens and Part-of-Speech Tags:")
        token_data = []
        for token in doc:
            token_data.append({
                "Text": token.text,
                "Lemma": token.lemma_,
                "POS": token.pos_,
                "Tag": token.tag_,
                "Dependency": token.dep_,
                "Is Alpha": token.is_alpha,
                "Is Stop": token.is_stop
            })
        df_tokens = pd.DataFrame(token_data)
        st.dataframe(df_tokens)

    else:
        st.info("Please enter text or a URL to analyze.")

# To run this, you'd typically have a main Streamlit file (e.g., app.py) like this:
#
# import streamlit as st
# from your_module_name import about # Assuming the above code is in 'your_module_name.py'
#
# def main():
#     st.set_page_config(page_title="NLP Text Analyzer", layout="wide")
#     st.title("Welcome to the NLP Text Analyzer")
#
#     # You can create a simple navigation if you have multiple pages
#     menu_selection = st.sidebar.radio("Navigation", ["Home", "About Text Analysis"])
#
#     if menu_selection == "About Text Analysis":
#         about()
#     elif menu_selection == "Home":
#         st.write("This is the home page. Use the sidebar to navigate to the text analysis tool.")
#
# if __name__ == "__main__":
#     main()

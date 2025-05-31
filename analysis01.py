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
    nlp1 = spacy.load("en_core_web_sm")

    input_type = st.radio("Select Input Method:", ["Text Input", "URL Analysis"], key="input_type_radio")

    text = ""

    if input_type == "Text Input":
        text = st.text_area("Enter the text to analyze:", height=200, key="text_input_area")

    elif input_type == "URL Analysis":
        url = st.text_input("Enter the URL to analyze:", key="url_input")
        if url:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, "html.parser")
                paragraphs = soup.find_all("p")
                text = " ".join([para.get_text() for para in paragraphs])
                st.success("Text successfully extracted from URL.")
            except Exception as e:
                st.error(f"Error fetching URL: {e}")

    if text:
        st.subheader("Sentences:")
        doc = nlp1(text)
        for sentence in doc.sents:
            st.write(sentence.text)

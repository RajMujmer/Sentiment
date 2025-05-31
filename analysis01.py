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
    input_type = st.radio(
        "Select Input Method:", ["Text Input", "URL Analysis"], key="input_type_radio")
        text = ""
        if input_type == "Text Input": # MODIFIED: Line 282
          text = st.text_area("Enter the text to analyze:", height=200, key="text_input_area") # MODIFIED: Line 283
        elif input_type == "URL Analysis": # MODIFIED: Line 284
          url = st.text_input("Enter the URL to analyze:", key="url_input") 
    for sentence in text:
        print(sentence)

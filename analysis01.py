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
    st.title("Text Analysis")
    text = st.text_area("Enter the text to analyze:", height=200, key="text_input_area")

    if text:
        nlp1 = spacy.load("en_core_web_sm")
        doc = nlp1(text)

        st.write("### Token | POS | Lemma")
        for token in doc:
            st.write(f"{token.text} | {token.pos_} | {token.lemma_}")

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
    text = st.text_area("Enter the text to analyze:", height=200, key="text_input_area")
     nlp1 = spacy.load("en_core_web_sm")
    for token1 in text:
        return (token1, "  | ", token1.pos_ , "  |  ", token1.lemma_)

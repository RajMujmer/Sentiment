import streamlit as st
from bs4 import BeautifulSoup
import requests
from typing import Union
import re
from collections import defaultdict

# Enhanced Sentiment Lexicon
sentiment_lexicon = defaultdict(float)
# fmt: off
sentiment_lexicon.update({
    "good": 0.8, "great": 0.9, "excellent": 0.95, "amazing": 0.9, "wonderful": 0.85, "happy": 0.7, "love": 0.9, "best": 1.0, "awesome": 0.9, "joy": 0.8, "beautiful": 0.8,
    "bad": -0.8, "terrible": -0.9, "awful": -0.95, "horrible": -0.9, "sad": -0.7, "hate": -0.9, "worst": -1.0, "disgusting": -0.9, "angry": -0.8, "ugly": -0.8,
    "not": -0.5, "n't": -0.5, "no": -0.5,  # Negation
    "very": 0.3, "extremely": 0.5, "really": 0.4,  # Intensifiers
    "sarcastic": -0.6,  #Sarcasm (very basic)
})
# fmt: on


def calculate_sentiment_score(text: str) -> float:
    """
    Calculates a sentiment score with negation and intensifier handling.
    """
    text = text.lower()
    words = re.findall(r'\b\w+\b', text)
    score = 0.0
    negation = False
    for i, word in enumerate(words):
        if word in sentiment_lexicon:
            word_score = sentiment_lexicon[word]
            if negation:
                word_score *= -1
            score += word_score
        elif word in ["not", "n't", "no"]:
            negation = True
        elif word in ["very", "extremely", "really"]: #handle intensifiers
            if i+1 < len(words) and words[i+1] in sentiment_lexicon:
                score += sentiment_lexicon[words[i+1]] * 0.5 #reduce the effect
        else:
            negation = False #reset negation

    return score / len(words) if words else 0.0


def get_sentiment_label(score: float) -> str:
    """Gets sentiment label."""
    if score > 0.2:
        return "Positive"
    elif score < -0.2:
        return "Negative"
    else:
        return "Neutral"



def scrape_webpage(url: str) -> Union[str, None]:
    """
    Scrapes the text content from a given URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        for script_or_style in soup.find_all(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None



def main():
    """
    Main function.
    """
    st.title("Sentiment Analysis App")

    input_type = st.radio("Input Type:", ["Text", "URL"])

    input_text = ""
    if input_type == "Text":
        input_text = st.text_area("Enter the text to analyze:", "")
    else:
        url = st.text_input("Enter the URL of the webpage:")

    if st.button("Analyze Sentiment"):
        if input_type == "Text" and not input_text:
            st.error("Please enter text to analyze.")
            return
        elif input_type == "URL" and not url:
            st.error("Please enter a URL.")
            return

        st.spinner("Analyzing sentiment...")

        if input_type == "URL":
            text_content = scrape_webpage(url)
            if text_content:
                input_text = text_content
            else:
                return

        sentiment_score = calculate_sentiment_score(input_text)
        sentiment_label = get_sentiment_label(sentiment_score)

        st.subheader("Sentiment Analysis Result:")
        st.write(f"Label: {sentiment_label}")
        st.write(f"Score: {sentiment_score:.4f}")



if __name__ == "__main__":
    main()

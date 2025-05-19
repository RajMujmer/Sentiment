import streamlit as st
from bs4 import BeautifulSoup
import requests
from transformers import pipeline
from typing import Union

def scrape_webpage(url: str) -> Union[str, None]:
    """
    Scrapes the text content from a given URL.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        str: The text content of the webpage, or None if an error occurs.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses

        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style tags
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

def analyze_sentiment(text: str) -> Union[dict, None]:
    """
    Analyzes the sentiment of the given text using the transformers library.
    Specifies the framework to use, to avoid needing to have tensorflow or pytorch installed.

    Args:
        text (str): The text to analyze.

    Returns:
        dict: A dictionary containing the sentiment analysis result
              ('label' and 'score'), or None on error.
    """
    try:
        # Load the sentiment analysis model with framework='pt'
        model = pipeline('sentiment-analysis', framework='np')  # Specify framework
        result = model(text)[0]  # Get the first result
        return result
    except Exception as e:
        st.error(f"Error analyzing sentiment: {e}")
        return None

def main():
    """
    Main function to run the Streamlit application.
    """
    st.title("Sentiment Analysis App")

    input_type = st.radio("Input Type:", ["Text", "URL"])

    input_text = ""  # Initialize input_text
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

        st.spinner("Analyzing sentiment...")  # Show a spinner

        if input_type == "URL":
            text_content = scrape_webpage(url)
            if text_content:
                input_text = text_content
            else:
                # scrape_webpage already shows an error, so just return here
                return

        # Now, analyze the sentiment:
        sentiment_result = analyze_sentiment(input_text)
        if sentiment_result:
            st.subheader("Sentiment Analysis Result:")
            st.write(f"Label: {sentiment_result['label']}")
            st.write(f"Score: {sentiment_result['score']:.4f}")
        else:
            st.error("Sentiment analysis failed.") # analyze_sentiment already shows error

if __name__ == "__main__":
    main()

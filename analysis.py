import streamlit as st
import re
from typing import List, Tuple, Union
import string
import requests
from bs4 import BeautifulSoup
import os
import pickle  # Import pickle


def load_words(file_path: str, encoding: str = "utf-8") -> List[str]:
    """Loads words from a text file into a list. Handles encoding issues.

    Args:
        file_path (str): Path to the word list file.
        encoding (str, optional):  Encoding to use. Defaults to "utf-8".
    Returns:
        List[str]:  List of words, or an empty list on error.
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            words = [line.strip().lower() for line in f]
        return words
    except UnicodeDecodeError:
        st.warning(
            f"Warning:  '{encoding}' encoding failed for {file_path}. Trying 'latin-1'."
        )
        try:
            return load_words(
                file_path, encoding="latin-1"
            )  # Recursive call with latin-1
        except Exception as e:
            st.error(
                f"Error:  Failed to load {file_path} with both utf-8 and latin-1.  Error: {e}"
            )
            return []
    except FileNotFoundError:
        st.error(f"Error: File not found at {file_path}")
        return []
    except Exception as e:
        st.error(f"An error occurred while loading {file_path}: {e}")
        return []


# Load word lists from .txt files
@st.cache_data  # Cache the loaded words for performance
def get_word_lists() -> Tuple[List[str], List[str], List[str]]:
    """Loads positive, negative, and stop words from text files.

    Returns:
        Tuple[List[str], List[str], List[str]]: positive, negative, and stop words lists.
    """
    positive_words = load_words("positive-words.txt")  # Load positive words
    negative_words = load_words("negative-words.txt")  # Load negative words
    # Load stop words directly, from a single file.
    stop_words_file = "OnlyStopWords.txt"  # <--- CHANGE THIS PATH IF NEEDED
    stop_words = load_words(stop_words_file)
    return positive_words, negative_words, stop_words



def scrape_text_from_url(url: str) -> Union[str, None]:
    """
    Scrapes text content from a given URL.

    Args:
        url (str): The URL to scrape.

    Returns:
        str: The extracted text, or None on error.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses

        soup = BeautifulSoup(response.content, "html.parser")
        # Remove script and style tags
        for script_or_style in soup.find_all(["script", "style"]):
            script_or_style.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching URL: {e}")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None



def calculate_polarity_subjectivity(
    text: str, stop_words: List[str], positive_words: List[str], negative_words: List[str]
) -> Tuple[float, float]:
    """
    Calculates polarity and subjectivity of a text.

    Args:
        text (str): The input text.
        stop_words (List[str]): A list of stop words.
        positive_words (List[str]): List of positive words.
        negative_words (List[str]): List of negative words.

    Returns:
        Tuple[float, float]: Polarity score (-1 to 1) and subjectivity score (0 to 1).
    """
    if not text:
        return 0.0, 0.0

    # Remove punctuation and convert to lowercase
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [
        word for word in text.split() if word not in stop_words
    ]  # Remove Stop words

    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    subjective_count = sum(
        1 for word in words
    )  # Simplified: Count all non-stop words as subjective

    total_words = len(words)
    if total_words == 0:
        return 0.0, 0.0

    polarity = (positive_count - negative_count) / total_words
    subjectivity = subjective_count / total_words

    return polarity, subjectivity


def calculate_fog_index(text: str, stop_words: List[str]) -> float:
    """
    Calculates the Gunning Fog Index of a text.

    Args:
        text (str): The input text.
        stop_words (List[str]): A list of stop words.

    Returns:
        float: The Gunning Fog Index.
    """
    if not text:
        return 0.0

    sentences = re.split(r"[.!?]+", text)
    total_sentences = len(sentences)
    if total_sentences == 0:
        return 0.0

    words = text.lower().split()
    total_words = len(words)

    complex_words = count_complex_words(text, stop_words)

    average_sentence_length = total_words / total_sentences
    percentage_complex_words = (complex_words / total_words) * 100

    fog_index = 0.4 * (average_sentence_length + percentage_complex_words)
    return fog_index



def count_complex_words(text: str, stop_words: List[str]) -> int:
    """
    Counts complex words (words with 3 or more syllables) in a text.

    Args:
        text (str): The input text.
        stop_words (List[str]): A list of stop words.

    Returns:
        int: The number of complex words.
    """
    if not text:
        return 0

    text = text.lower().translate(str.maketrans("", "", string.punctuation))  # remove punctuation
    words = [word for word in text.split() if word not in stop_words]
    complex_word_count = 0
    for word in words:
        vowels = "aeiouy"
        syllable_count = 0
        if len(word) > 2:
            for i, char in enumerate(word):
                if char in vowels:
                    if i == 0 or word[i - 1] not in vowels:
                        syllable_count += 1
            if word.endswith("e"):
                if word[-2] in vowels:
                    syllable_count -= 1
            if syllable_count >= 3:
                complex_word_count += 1
    return complex_word_count



def count_words(text: str, stop_words: List[str]) -> int:
    """Counts the total number of words in a text, excluding stop words and punctuation."""
    if not text:
        return 0
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [word for word in text.split() if word not in stop_words]
    return len(words)

def count_stop_words(text: str, stop_words: List[str]) -> int: # 178
    """Counts the number of stop words in a text."""
    if not text:
        return 0
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    stop_word_count = sum(1 for word in words if word in stop_words)
    return stop_word_count

def count_syllables(word: str) -> int:
    """Counts the number of syllables in a single word."""
    vowels = "aeiouy"
    syllable_count = 0
    for i, char in enumerate(word):
        if char in vowels:
            if i == 0 or word[i - 1] not in vowels:
                syllable_count += 1
    if word.endswith("e"):
        if word[-2] in vowels:
            syllable_count -= 1
    return syllable_count if syllable_count > 0 else 1



def calculate_average_syllables_per_word(
    text: str, stop_words: List[str]
) -> float:
    """Calculates the average number of syllables per word in a text."""
    if not text:
        return 0.0
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [word for word in text.split() if word not in stop_words]
    total_syllables = sum(count_syllables(word) for word in words)
    word_count = len(words)
    return total_syllables / word_count if word_count else 0.0



def count_personal_pronouns(text: str) -> int:
    """Counts personal pronouns in a text (case-insensitive)."""
    if not text:
        return 0
    pronoun_pattern = r"\b(i|me|my|mine|you|your|yours|he|she|him|her|his|hers|it|its|we|us|our|ours|they|them|their|theirs)\b"
    pronouns = re.findall(pronoun_pattern, text, re.IGNORECASE)
    return len(pronouns)



def calculate_average_word_length(text: str, stop_words: List[str]) -> float:
    """Calculates the average word length in a text, excluding stop words and punctuation."""
    if not text:
        return 0.0
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [word for word in text.split() if word not in stop_words]
    total_word_length = sum(len(word) for word in words)
    word_count = len(words)
    return total_word_length / word_count if word_count else 0.0



def analyze_sentiment(polarity: float) -> str:
    """
    Analyzes sentiment based on polarity score.

    Args:
        polarity (float): The polarity score.

    Returns:
        str: The sentiment label ("Positive", "Negative", or "Neutral").
    """
    if polarity > 0.2:
        return "Positive"
    elif polarity < -0.2:
        return "Negative"
    else:
        return "Neutral"



def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(layout="centered", page_title="Text Analysis Dashboard")
    st.title("Professional Text Analysis Dashboard")
    st.markdown(
        """
        <p style='font-size: 1.1rem; color: #555; text-align: center; margin-bottom: 2rem;'>
            Gain valuable insights into the sentiment and readability of your text or any webpage.
            Simply paste your content or a URL below to get started.
        </p>
        """,
        unsafe_allow_html=True # MODIFIED: Lines 269-275
    )
    # Input type selection
    
    input_type = st.radio(
        "Select Input Method:", ["Text Input", "URL Analysis"], key="input_type_radio"
    )  # Removed File option

    # Input text area or URL input
    text = ""
    if input_type == "Text Input": # MODIFIED: Line 282
        text = st.text_area("Enter the text to analyze:", height=200, key="text_input_area") # MODIFIED: Line 283
    elif input_type == "URL Analysis": # MODIFIED: Line 284
        url = st.text_input("Enter the URL to analyze:", key="url_input") # MODIFIED: Line 285



    # Load word lists, including stop words.
    positive_words, negative_words, stop_words = get_word_lists()  # Load the words

    # Analyze button
    if st.button("Analyze Content", key="analyze_button"): # MODIFIED: Line 290
        if input_type == "URL Analysis" and not url: # MODIFIED: Line 291
            st.error("Please enter a URL.")
            return
        elif input_type == "Text Input" and not text: # MODIFIED: Line 293
            st.error("Please enter the text to analyze")
            return


        if input_type == "URL Analysis": # MODIFIED: Line 297
            text = scrape_text_from_url(url)
            if text is None:  # Error occurred during scraping
                return

        with st.spinner("Processing your request..."):
        # Calculate metrics
            polarity, subjectivity = calculate_polarity_subjectivity(text, stop_words, positive_words, negative_words) # Pass the word lists
            fog_index = calculate_fog_index(text, stop_words)
            complex_word_count = count_complex_words(text, stop_words)
            word_count = count_words(text, stop_words)
            average_syllables_per_word = calculate_average_syllables_per_word(
                text, stop_words
            )
            personal_pronoun_count = count_personal_pronouns(text)
            average_word_length = calculate_average_word_length(text, stop_words)
            average_sentence_length = (
                len(text.split()) / len(re.split(r"[.!?]+", text))
                if len(re.split(r"[.!?]+", text)) > 0
                else 0
            )
            percentage_complex_words = (
                complex_word_count / word_count
            ) * 100 if word_count else 0
            stop_word_count = count_stop_words(text, stop_words)
        st.success("Analysis complete! Here are the detailed insights.")
        sentiment = analyze_sentiment(polarity)

        # Display results with styled sections
        st.markdown(
            """
            <style>
            body {
                background-color: #f8f9fa; /* Changed from #f0f8ff to a slightly brighter light blue */ # Line 330
                color: #333;
                font-family: 'Segoe UI', 'Roboto', sans-serif; 
            }
            .stApp { /* Main app container */
                background-color: #f8f9fa; /* Changed from #f0f8ff to match body background */ # Line 334
            }
            report-section {
                padding: 1.8rem;
                margin-bottom: 1.8rem;
                border-radius: 0.8rem;
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                box-shadow: 0 0.3rem 1rem rgba(0, 0, 0, 0.08);
            }
            .report-title {
                color: #007bff;
                font-size: 2rem;
                margin-bottom: 1.5rem;
                border-bottom: 2px solid #ced4da;
                padding-bottom: 0.8rem;
                font-weight: 700;
            }
            .metric-label {
                font-weight: 600;
                color: #495057;
                font-size: 1.15rem;
            }
            .metric-value {
                color: #7f8c8d;
                font-size: 1.3rem;
            }
            .sentiment-box {
                padding: 1.5rem;
                border-radius: 0.8rem;
                margin-top: 2rem;
                text-align: center;
                font-size: 2rem;
                font-weight: 700;
                box-shadow: 0 0.2rem 0.6rem rgba(0,0,0,0.1);
            }
            .positive {
            background-color: #d4edda; /* Light green */
            color: #155724; /* Dark green text */
            border: 1px solid #28a745; /* Green border */
            }
            .negative {
            background-color: #f8d7da; /* Light red */
            color: #721c24; /* Dark red text */
            border: 1px solid #dc3545; /* Red border */
            }
            .neutral {
            background-color: #e2e3e5; /* Light grey */
            color: #383d41; /* Dark grey text */
            border: 1px solid #6c757d; /* Grey border */
            }
            .stButton>button { /* Styling for the Analyze button */
            background-color: #007bff; /* Professional blue button */
            color: white;
            border-radius: 0.5rem;
            padding: 0.8rem 1.8rem; /* Increased padding */
            font-size: 1.2rem; /* Larger font */
            font-weight: 600; /* Bolder */
            border: none;
            box-shadow: 0 0.2rem 0.5rem rgba(0,0,0,0.1);
            transition: background-color 0.3s ease, transform 0.2s ease; /* Added transform for subtle hover */
            }
            .stButton>button:hover {
                background-color: #0056b3; /* Darker blue on hover */
                transform: translateY(-2px); /* Subtle lift effect */
                cursor: pointer;
            }
            /* Styling for radio buttons */
            .stRadio > label > div {
                font-size: 1.1rem;
                font-weight: 500;
                color: #343a40;
            }
            /* Styling for text area and text input */
            .stTextArea > label > div, .stTextInput > label > div {
                font-size: 1.1rem;
                font-weight: 500;
                color: #343a40;
            }
            </style>
            """,
            unsafe_allow_html=True,
            )
        </style>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='report-section'>"
            "<h2 class='report-title'>Sentiment Analysis</h2>"
            f"<p><span class='metric-label'>Polarity Score:</span> <span class='metric-value'>{polarity:.2f}</span></p>"
            f"<p><span class='metric-label'>Subjectivity Score:</span> <span class='metric-value'>{subjectivity:.2f}</span></p>"
            "<div class='sentiment-box " + sentiment.lower() + "'>" + sentiment + "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='report-section'>"
            "<h2 class='report-title'>Readability Analysis</h2>"
            f"<p><span class='metric-label'>Fog Index:</span> <span class='metric-value'>{fog_index:.2f}</span></p>"
            f"<p><span class='metric-label'>Average Sentence Length:</span> <span class='metric-value'>{average_sentence_length:.2f}</span></p>"
            f"<p><span class='metric-label'>Percentage of Complex Words:</span> <span class='metric-value'>{percentage_complex_words:.2f}%</span></p>"
            f"<p><span class='metric-label'>Complex Word Count:</span> <span class='metric-value'>{complex_word_count}</span></p>"
            f"<p><span class='metric-label'>Word Count:</span> <span class='metric-value'>{word_count}</span></p>"
            f"<p><span class='metric-label'>Average Word Length:</span> <span class='metric-value'>{average_word_length:.2f}</span></p>"
            f"<p><span class='metric-label'>Syllables per Word:</span> <span class='metric-value'>{average_syllables_per_word:.2f}</span></p>"
            f"<p><span class='metric-label'>Personal Pronoun Count:</span> <span class='metric-value'>{personal_pronoun_count}</span></p>"
             f"<p><span class='metric-label'>Stop Word Count:</span> <span class='metric-value'>{stop_word_count}</span></p>"
            "</div>",
            unsafe_allow_html=True,
        )

        # Interpretation of Results
        st.subheader("Interpretation:")
        st.write(
            "Polarity ranges from -1 (negative) to 1 (positive). Subjectivity ranges from 0 (objective) to 1 (subjective)."
        )
        st.write(
            "A Fog Index of 7-12 is generally considered readable for a wide audience. Higher values indicate more difficult text."
        )
        st.write(
            "Complex words are those with 3 or more syllables.  A higher count can make text harder to read."
        )
        st.write(
            "A higher number of personal pronouns can indicate a more subjective and personal writing style."
        )
        st.markdown(
            """
            <div style='padding: 1.25rem; border-radius: 0.75rem; background-color: #e9ecef; border: 1px solid #dee2e6;'>
                <p style='color:#495057; font-size: 1.1rem;'>
                <b>Disclaimer:</b> This analysis is based on simplified calculations and lexicons.  It may not be as accurate as more sophisticated methods.  The accuracy of sentiment analysis, in particular, is limited by the simple word matching approach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Metric Definitions and Benefits")  # Added this heading
        st.write(
            "<ul style='list-style-type:disc; padding-left: 2rem;'> "  # Use a bulleted list for better formatting
            "<li><span class='metric-label'>Fog Index:</span>"
            "<span class='metric-value'> A readability formula that estimates the years of formal education a person needs to understand the text.  A higher Fog Index indicates more difficult reading material.</span>"
            "<span style='font-weight: bold;'> Benefit:</span> Helps ensure your writing is accessible to your target audience.</li>"
            "<li><span class='metric-label'>Average Sentence Length:</span>"
            "<span class='metric-value'> The average number of words per sentence. Longer sentences can make text more complex.</span>"
            "<span style='font-weight: bold;'> Benefit:</span>  Indicates the complexity of sentence structure and helps in making text concise.</li>"
            "<li><span class='metric-label'>Percentage of Complex Words:</span>"
            "<span class='metric-value'> The percentage of words with three or more syllables. A higher percentage suggests more difficult vocabulary.</span>"
            "<span style='font-weight: bold;'> Benefit:</span>  Highlights the use of difficult vocabulary, which can affect readability.</li>"
            "<li><span class='metric-label'>Complex Word Count:</span>"
            "<span class='metric-value'>  The total number of words with three or more syllables.</span>"
            "<span style='font-weight: bold;'> Benefit:</span>  Provides a direct count of difficult words.</li>"
            "<li><span class='metric-label'>Word Count:</span>"
            "<span class='metric-value'> The total number of words in the text (excluding stop words and punctuation).</span>"
            "<span style='font-weight: bold;'> Benefit:</span> Basic metric for analyzing text length and complexity.</li>"
            "<li><span class='metric-label'>Average Word Length:</span>"
            "<span class='metric-value'> The average number of characters per word. Longer words can contribute to complexity.</span>"
             "<span style='font-weight: bold;'> Benefit:</span> Indicates word complexity; longer words can make text more challenging.</li>"
            "<li><span class='metric-label'>Syllables per Word:</span>"
            "<span class='metric-value'> The average number of syllables per word. More syllables generally mean more complex words.</span>"
            "<span style='font-weight: bold;'> Benefit:</span>  Another measure of word complexity, directly related to readability.</li>"
            "<li><span class='metric-label'>Personal Pronoun Count:</span>"
            "<span class='metric-value'> The number of personal pronouns (e.g., I, you, he, she, we, they).</span>"
            "<span style='font-weight: bold;'> Benefit:</span> Can indicate the writing style's tone (e.g., personal vs. impersonal).</li>"
            "<li><span class='metric-label'>Stop Word Count:</span>"
            "<span class='metric-value'> The number of common words (e.g., the, is, in, a) that are often removed before text analysis.</span>"
            "<span style='font-weight: bold;'> Benefit:</span>  Indicates the amount of less meaningful words in the text.  While stop words are important for sentence structure, a very high proportion can sometimes indicate wordiness or redundancy.</li>"
            "</ul>",
            unsafe_allow_html=True,
        )



if __name__ == "__main__":
    main()


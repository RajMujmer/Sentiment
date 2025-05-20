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
    working_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = working_dir/StopWords.txt
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
    # Load stop words directly, like loading a model.  Specify the full path.
    stop_words_file = "stop_words.txt"  # <--- CHANGE THIS PATH IF NEEDED
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
    text: str, stop_words: List[str]
) -> Tuple[float, float]:
    """
    Calculates polarity and subjectivity of a text.

    Args:
        text (str): The input text.
        stop_words (List[str]): A list of stop words.

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
    st.title("Enhanced Sentiment and Readability Analyzer")

    # Input type selection
    input_type = st.radio(
        "Choose Input Type:", ["Text", "URL", "File"]
    )  # Added File option

    # Input text area or URL input
    text = ""
    if input_type == "Text":
        text = st.text_area("Enter the text to analyze:", height=200)
    elif input_type == "URL":
        url = st.text_input("Enter the URL to analyze:")
    elif input_type == "File":  # File Upload
        uploaded_file = st.file_uploader("Upload a text file", type="txt")
        if uploaded_file is not None:
            try:
                text = uploaded_file.read().decode(
                    "utf-8"
                )  # Read as string
            except UnicodeDecodeError:
                text = uploaded_file.read().decode("latin-1")
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return

    # Load word lists, including stop words.
    positive_words, negative_words, stop_words = get_word_lists()  # Load the words

    # Analyze button
    if st.button("Analyze"):
        if input_type == "URL" and not url:
            st.error("Please enter a URL.")
            return
        elif input_type == "Text" and not text:
            st.error("Please enter the text to analyze")
            return
        elif input_type == "File" and not uploaded_file:
            st.error("Please upload a text file")
            return

        if input_type == "URL":
            text = scrape_text_from_url(url)
            if text is None:  # Error occurred during scraping
                return

        # Calculate metrics
        polarity, subjectivity = calculate_polarity_subjectivity(text, stop_words)
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

        sentiment = analyze_sentiment(polarity)

        # Display results with styled sections
        st.markdown(
            """
            <style>
            .report-section {
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                border-radius: 0.75rem;
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                box-shadow: 0 0.25rem 0.5rem rgba(0, 0, 0, 0.05);
            }
            .report-title {
                color: #2c3e50;
                font-size: 1.85rem;
                margin-bottom: 1.25rem;
                border-bottom: 2px solid #bdc3c7;
                padding-bottom: 0.75rem;
            }
            .metric-label {
                font-weight: bold;
                color: #2c3e50;
                font-size: 1.1rem;
            }
            .metric-value {
                color: #7f8c8d;
                font-size: 1.25rem;
            }
            .sentiment-box {
                padding: 1rem;
                border-radius: 0.5rem;
                margin-top: 1rem;
                text-align: center;
                font-size: 1.5rem;
                font-weight: bold;
            }
            .positive {
                background-color: #e6f4e5;
                color: #388e3c;
                border: 2px solid #81c784;
            }
            .negative {
                background-color: #fde0d3;
                color: #d32f2f;
                border: 2px solid #e57373;
            }
            .neutral {
                background-color: #f5f5f5;
                color: #5e5e5e;
                border: 2px solid #9e9e9e;
            }
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
            <div style='padding: 1.25rem; border-radius: 0.75rem; background-color: #e0f7fa; border: 1px solid #b2ebf2;'>
                <p style='color: #00838f; font-size: 1.1rem;'>
                    <b>Disclaimer:</b> This analysis is based on simplified calculations and lexicons.  It may not be as accurate as more sophisticated methods.  The accuracy of sentiment analysis, in particular, is limited by the simple word matching approach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )



if __name__ == "__main__":
    main()

import polars as pl
import re
from num2words import num2words
import langid
import concurrent
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from deep_translator import GoogleTranslator
from spellchecker import SpellChecker
from symspellpy.symspellpy import SymSpell, Verbosity
import os
from dotenv import load_dotenv
import logging
import argparse

def clean_missing_values(df: pl.DataFrame, column_name: str) -> tuple[pl.DataFrame, int]:
    """
    Remove rows from a DataFrame where the specified column has missing values,
    and return the cleaned DataFrame and the number of missing values removed.
    
    Args:
        df (pl.DataFrame): The DataFrame to clean.
        column_name (str): Column to check for missing values.
        
    Returns:
        tuple[pl.DataFrame, int]: Cleaned DataFrame and number of missing values removed.
    """
    
    # Drop rows where the specified column is null
    df_clean = df.drop_nulls(subset=[column_name])

    nb_missing_values = df[column_name].null_count()
    
    return df_clean,nb_missing_values

def remove_duplicates(df: pl.DataFrame, subset_columns: list) -> tuple[pl.DataFrame, int]:
    """
    Remove duplicate rows from a DataFrame based on specified columns,
    and return the cleaned DataFrame and the number of duplicates removed.
    
    Args:
        df (pl.DataFrame): The DataFrame to clean.
        subset_columns (list): List of columns to consider for duplicates.
        
    Returns:
        tuple[pl.DataFrame, int]: DataFrame with duplicates removed and number of duplicates found.
    """
    # Nombre de lignes avant suppression
    initial_count = df.height

    # Supprimer les doublons selon les colonnes spécifiées
    df_clean = df.unique(subset=subset_columns)

    # Nombre de doublons supprimés
    nb_duplicates = initial_count - df_clean.height

    return df_clean, nb_duplicates

def remove_special_characters(df: pl.DataFrame, column_name: str, keep: str = "") -> pl.DataFrame:
    """
    Remove special characters from a specified text column using regex.

    Args:
        df (pl.DataFrame): Input Polars DataFrame.
        column_name (str): Name of the text column to clean.
        keep (str): Optional string of characters to preserve (e.g., ".," to keep dots and commas).

    Returns:
        pl.DataFrame: New DataFrame with cleaned text in the specified column.
    """


    # Pattern to remove emails
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

    # Pattern to remove unwanted characters
    chars_pattern = rf"[^\w\s{re.escape(keep)}]"

    # Pattern to remove hashtags (#word)
    hashtag_pattern = r"#\S+"

    # Pattern to replace apostrophes with a space
    apostrophe_pattern = r"[’']"

    # Pattern to remove url
    url_pattern = r"https?://\S+|www\.\S+"

    def clean_text(text):
        # 1. Remove emails
        text = re.sub(email_pattern, "", text)
        # 2. Remove URLs
        text = re.sub(url_pattern, "", text)
        # 3. Remove hashtags
        text = re.sub(hashtag_pattern, "", text)
        # 4. Replace apostrophes with a space
        text = re.sub(apostrophe_pattern, " ", text)
        # 5. Remove unwanted characters
        text = re.sub(chars_pattern, "", text)
        # 6. Clean multiple spaces
        text = re.sub(r"\s+", " ", text).strip()
        return text

    df_cleaned = df.with_columns(
        pl.col(column_name).map_elements(clean_text).alias(column_name)
    )

    return df_cleaned

def numbers_to_words(df: pl.DataFrame, column_name: str) -> pl.DataFrame:
    """
    Convert all numbers in a text column into words using num2words.

    Args:
        df (pl.DataFrame): Input DataFrame.
        column_name (str): Name of the text column to process.
        lang (str): Language code (e.g., 'en' or 'fr').

    Returns:
        pl.DataFrame: New DataFrame with numbers replaced by words.
    """
    def convert_numbers(text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return text

        def replace_number(m):
            num_text = num2words(int(m.group()))
            left = ' ' if m.start() > 0 and text[m.start()-1].isalnum() else ''
            right = ' ' if m.end() < len(text) and text[m.end():m.end()+1].isalnum() else ''
            return f"{left}{num_text}{right}"

        return re.sub(r'\d+', replace_number, text)

    df_converted = df.with_columns(
        pl.col(column_name).map_elements(convert_numbers).alias(column_name)
    )

    return df_converted

def detect_language_parallel(df: pl.DataFrame, column_name: str, num_threads: int = 4) -> tuple[pl.DataFrame, int]:
    """
    Detect the language of a text column in a Polars DataFrame using langid in parallel.

    Args:
        df (pl.DataFrame): Input DataFrame.
        column_name (str): Name of the text column to process.
        num_threads (int): Number of threads to use for parallel processing (default=4).

    Returns:
        tuple[pl.DataFrame, int]: 
            - DataFrame with an added column 'detected_lang' containing language codes.
            - Number of sentences not detected as English ('en').
    """
    def detect_lang(text: str) -> str:
        """Return the language code of a single text using langid."""
        if not isinstance(text, str) or not text.strip():
            return None
        lang, _ = langid.classify(text)
        return lang

    # Convert the Polars column to a Python list
    texts = df[column_name].to_list()

    # Parallel processing with ThreadPoolExecutor
    all_langs = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for result in tqdm(executor.map(detect_lang, texts), total=len(texts), desc="Language detection"):
            all_langs.append(result)

    # Return new DataFrame with added column
    df_result = df.with_columns(pl.Series("detected_lang", all_langs))

    nb_non_english = sum(lang != "en" for lang in all_langs if lang is not None)

    return df_result,nb_non_english

def translate_non_english_threadsafe(df: pl.DataFrame,
                                     column_name: str,
                                     detected_lang_col: str = "detected_lang",
                                     num_threads: int = 4) -> pl.DataFrame:
    """
    Thread-safe translation: one translator per thread.
    """
    def translate_one(text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            return text
        try:
            translator = GoogleTranslator(source='auto', target='en')  # local traductor
            return translator.translate(text)
        except Exception as e:
            return f"[ERROR: {e}]"

    indices_to_translate = []
    texts_to_translate = []
    for i, (text, lang) in enumerate(zip(df[column_name].to_list(), df[detected_lang_col].to_list())):
        if lang != 'en':
            indices_to_translate.append(i)
            texts_to_translate.append(text)

    translated_texts = df[column_name].to_list()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for idx, translation in zip(
            indices_to_translate,
            tqdm(executor.map(translate_one, texts_to_translate),
                 total=len(texts_to_translate),
                 desc="Translating non-English reviews")
        ):
            translated_texts[idx] = translation

    return df.with_columns(pl.Series(column_name, translated_texts))

def preprocess_pipeline(input_csv: str, column_name: str, output_csv: str):
    """
    Apply the full preprocessing pipeline to the given CSV file.
    """
    df = pl.read_csv(input_csv)
    logger.info(f"DataFrame {os.path.splitext(os.path.basename(input_csv))[0]} loaded : {df.shape[0]} rows x {df.shape[1]} columns")
    df,nb_missing_values = clean_missing_values(df, column_name)
    logger.info(f"{nb_missing_values} missing reviews detected and cleaned.")
    df,nb_duplicates = remove_duplicates(df, column_name)
    logger.info(f"{nb_duplicates} duplicated reviews detected and cleaned.")
    df = numbers_to_words(df, column_name)
    logger.info(f"Numerical numbers converted to string numbers.")
    df = remove_special_characters(df, column_name)
    logger.info(f" Special characters removed.")
    df,nb_to_translate = detect_language_parallel(df, column_name, NUM_THREAD)
    logger.info(f"{nb_to_translate} reviews are potentially not in english.")
    df = translate_non_english_threadsafe(df, column_name, "detected_lang", NUM_THREAD)
    logger.info(f"{nb_to_translate} have been translated in english.")
    df.write_csv(output_csv)
    logger.info(f"Cleaned Dataframe saved at {output_csv}")

if __name__ == "__main__":
     
    # Simple loger for pipeline execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logging.getLogger("langid").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)

    # Parse parameters
    parser = argparse.ArgumentParser(prog="pipeline_anomalies_processing.py", 
                                     description="Argument parsers for anomalies preprocessing pipeline",
                                     epilog="Exemple : python pipeline_anomalies_processing.py --origin_path ../data/dataset/original/test.csv --col review --output_path ../data/processed/test_cleaned.csv")
    parser.add_argument(
        "--origin_path",
        type=str,
        required=True,
        help="It is the path of the original dataset."
    )
    parser.add_argument(
        "--col",
        type=str,
        required=True,
        help="It is the name of the colmun that contains the reviews in your original dataset."
    )
    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="It is the path of your output dataset."
    )
    args = parser.parse_args()
    logging.info("Parameters loaded with sucess.")

    # Global variables
    load_dotenv(dotenv_path="../.env")
    NUM_THREAD = int(os.environ.get("NUM_THREADS"))
    logging.info(f"NUM_THREAD fixed to {NUM_THREAD}")

    # Running the complete pipeline
    preprocess_pipeline(args.origin_path,args.col,args.output_path)
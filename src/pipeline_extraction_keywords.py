import nltk
import polars as pl
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import spacy
from tqdm import tqdm
from typing import Dict, List
import concurrent.futures
import os
from dotenv import load_dotenv
import logging
import json

nltk.download("stopwords", quiet=True)
nltk.download("punkt", quiet=True)
#nltk.download('punkt_tab')

NEGATIONS = {"not", "no", "never", "none", "cannot", "can't", "don't", 
             "doesn't", "isn't", "wasn't", "weren't", "wouldn't", "shouldn't", "couldn't"}


def remove_stopwords(df: pl.DataFrame, column_name: str) -> pl.DataFrame:
    """
    Remove English stopwords from a given text column in a Polars DataFrame.

    Parameters
    ----------
    df : pl.DataFrame
        Input DataFrame containing text data.
    column_name : str
        Name of the column containing the text to process.

    Returns
    -------
    pl.DataFrame
        A new DataFrame with stopwords removed from the specified column.
    """
    stop_words = set(stopwords.words("english"))

    def clean_text(text: str) -> str:
        if not isinstance(text, str):
            return text
        tokens = word_tokenize(text.lower())
        filtered = [word for word in tokens if re.match(r"^[A-Za-z-]+$", word) 
                    and (word not in stop_words or word in NEGATIONS)]
        return " ".join(filtered)

    return df.with_columns(
        pl.col(column_name).map_elements(clean_text, return_dtype=pl.Utf8).alias(column_name)
    )

# Load SpaCy (disable unnecessary components for faster performance)
nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])

def lemmatize_and_clean_texts(
    texts: List[str],
    batch_size: int = 2000,
    n_process: int = 4
) -> List[str]:
    """
    Lemmatize a list of texts using spaCy with multiprocessing
    and clean them for keyword matching.
    
    Cleaning:
    - Replace " - " with "-" to handle multi-word keywords like "pet-friendly".
    - Strip leading/trailing whitespace.
    """
    clean_texts = [(t if isinstance(t, str) else "") for t in texts]
    lemmatized = []
    for doc in nlp.pipe(clean_texts, batch_size=batch_size, n_process=n_process):
        text = " ".join([token.lemma_ for token in doc])
        text = text.replace(" - ", "-").strip()
        lemmatized.append(text)
    return lemmatized


def lemmatize_column_fast(
    df: pl.DataFrame, 
    col_name: str, 
    new_col_name: str = None, 
    chunk_size: int = 5000, 
    n_process: int = 4
) -> pl.DataFrame:
    """
    Lemmatize a Polars DataFrame column efficiently in batches with multiprocessing.
    """
    new_col_name = new_col_name or f"{col_name}_lemmatized"
    texts = df.select(col_name).to_series().to_list()
    lemmatized_chunks = []

    for i in tqdm(range(0, len(texts), chunk_size), desc=f"Lemmatizing {col_name}"):
        chunk = texts[i:i + chunk_size]
        lemmatized_chunks.extend(lemmatize_and_clean_texts(chunk, n_process=n_process))

    return df.with_columns(pl.Series(name=new_col_name, values=lemmatized_chunks))


def lemmatize_categories(
    categories: Dict[str, List[str]]
) -> Dict[str, List[str]]:
    """
    Lemmatize all keywords in category dictionary.
    """
    return {
        category: lemmatize_and_clean_texts(keywords, batch_size=100, n_process=1)
        for category, keywords in categories.items()
    }

import re
import concurrent.futures
from typing import Dict, List
import polars as pl
from tqdm import tqdm

def extract_all_categories(
    df: pl.DataFrame,
    col_name: str,
    categories: Dict[str, List[str]],
    exclusions: Dict[str, List[str]] = None,
    n_process: int = 4,
    id_col: str = "id"
) -> pl.DataFrame:
    """
    Extract reviews matching category keywords, keeping reviews if at least one keyword remains
    after temporarily removing exclusion phrases.

    Args:
        df (pl.DataFrame): Input dataframe.
        col_name (str): Column containing the text.
        categories (Dict[str, List[str]]): {category: [lemmatized keywords]}.
        exclusions (Dict[str, List[str]]): {category: [phrases to exclude]}.
        n_process (int): Number of threads.
        id_col (str): Column containing unique IDs.

    Returns:
        pl.DataFrame: DataFrame with columns [id, review, keywords_found, category].
    """

    texts = df.select([id_col, col_name]).to_pandas()
    exclusions = exclusions or {}

    def normalize_keyword(kw: str) -> str:
        return kw.strip().replace(" - ", "-")

    def make_regex(kw: str) -> str:
        kw = normalize_keyword(kw)
        if " " in kw or "-" in kw:
            return re.escape(kw).replace("\\-", "[-\\s]").replace("\\ ", "\\s+")
        else:
            return r"\b" + re.escape(kw) + r"\b"

    def process_category(category: str, keywords: List[str], excluded_phrases: List[str]):
        results = []
        for _, row in texts.iterrows():
            text = row[col_name]
            review_id = row[id_col]
            if not isinstance(text, str):
                continue

            temp_text = text
            # Temporarily remove the exclusion phrases
            if excluded_phrases:
                for ex in excluded_phrases:
                    temp_text = re.sub(make_regex(ex), " ", temp_text, flags=re.IGNORECASE)

            # Check if at least one keyword remains
            matched_keywords = [kw for kw in keywords if re.search(make_regex(kw), temp_text, flags=re.IGNORECASE)]

            if matched_keywords:
                results.append((review_id, text, ", ".join(matched_keywords), category))

        return results

    # Parallel processing
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_process) as executor:
        futures = {executor.submit(process_category, cat, kws, exclusions.get(cat, [])): cat
                   for cat, kws in categories.items()}
        for fut in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Keyword extraction"):
            all_results.extend(fut.result())

    if not all_results:
        return pl.DataFrame(schema={
            id_col: pl.Int64,
            "review": pl.Utf8,
            "keywords_found": pl.Utf8,
            "category": pl.Utf8
        })

    df_filtered = pl.DataFrame({
        id_col: [r[0] for r in all_results],
        "review": [r[1] for r in all_results],
        "keywords_found": [r[2] for r in all_results],
        "category": [r[3] for r in all_results]
    })

    logger.info(f"Extracted {df_filtered.shape[0]} matching reviews across {len(categories)} categories.")
    return df_filtered

def process_pipeline(input_csv: str, column_name: str, output_csv: str, nb_process:int):

    df = pl.read_csv(input_csv)
    logger.info(f"DataFrame {os.path.splitext(os.path.basename(input_csv))[0]} loaded : {df.shape[0]} rows x {df.shape[1]} columns")
    
    # Load categories
    with open("../data/categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)

    # Load exclusions
    with open("../data/exclusions.json", "r", encoding="utf-8") as f:
        exclusions = json.load(f)

    logger.info("Keywords and excluded words loaded")

    df_clean = remove_stopwords(df, column_name)
    logger.info("Stop words have been removed")

    lemmatized_categories = lemmatize_categories(categories)
    lemmatized_exclusions = lemmatize_categories(exclusions)
    logger.info("Keywords and excluded words have been lemmatized")

    df_lem = lemmatize_column_fast(df_clean, column_name, n_process=nb_process)
    logger.info("DataFrame has been lemmatized")

    df_keywords = extract_all_categories(
        df_lem, 
        col_name = f"{column_name}_lemmatized",
        categories=lemmatized_categories,
        exclusions=lemmatized_exclusions,
        n_process=nb_process
    )
    logger.info("Keywords extraction finished")

    # Save
    df_keywords.write_csv(output_csv)
    logger.info(f"DataFrame saved to {output_csv}")

if __name__ == "__main__":

    # Simple loger for pipeline execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Global variables
    load_dotenv(dotenv_path="../.env")
    NUM_THREAD = int(os.environ.get("NUM_THREADS"))
    logger.info(f"NUM_THREAD fixed to {NUM_THREAD}")

    input_path="../data/original/dataset/data_booking.csv"
    name_column = "review"
    output_path = "../data/processed/data_categorized/key_words_data_booking.csv"
    logger.info("Beginning of the pipeline:")
    process_pipeline(input_path,name_column,output_path,NUM_THREAD)
    logger.info("End of the pipeline")
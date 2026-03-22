"""
WellFit Data Loader Module

This module provides functions to load CSV-based reference data for the WellFit system.
CSV files are the single source of truth for static data.

Architecture Rules:
- CSV files are read directly (not stored in database)
- No business logic in this module
- Only reads, validates, and returns data
- Uses platform-independent paths
"""

import pandas as pd
from pathlib import Path
import sys


def get_data_dir() -> Path:
    """
    Get the absolute path to the data/processed directory.
    
    Returns:
        Path: Absolute path to data/processed directory
    """
    # Get the project root (parent of logic directory)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "processed"
    
    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")
    
    return data_dir


def load_csv(filename: str) -> pd.DataFrame:
    """
    Load a CSV file from the data/processed directory.
    
    Args:
        filename: Name of the CSV file to load
        
    Returns:
        pd.DataFrame: Loaded data
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
        Exception: If the file cannot be read
    """
    data_dir = get_data_dir()
    file_path = data_dir / filename
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise Exception(f"Failed to read {filename}: {str(e)}")


def load_exercises() -> pd.DataFrame:
    """
    Load comprehensive exercise data.
    
    Returns:
        pd.DataFrame: Exercise data with columns for exercise details
    """
    return load_csv("exercises_comprehensive.csv")


def load_food_nutrition() -> pd.DataFrame:
    """
    Load comprehensive food nutrition data.
    
    Returns:
        pd.DataFrame: Food nutrition data with nutritional information
    """
    return load_csv("food_nutrition_comprehensive.csv")


def load_food_prices() -> pd.DataFrame:
    """
    Load comprehensive food price data.
    
    Returns:
        pd.DataFrame: Food price data
    """
    return load_csv("food_prices_comprehensive.csv")


def load_pain_keywords() -> pd.DataFrame:
    """
    Load comprehensive pain keywords data.
    
    Returns:
        pd.DataFrame: Pain keywords and related information
    """
    return load_csv("pain_keywords_comprehensive.csv")


def load_exercise_contraindications() -> pd.DataFrame:
    """
    Load exercise contraindications data.
    
    Returns:
        pd.DataFrame: Exercise contraindications
    """
    return load_csv("exercise_contraindications.csv")


def load_exercise_safety() -> pd.DataFrame:
    """
    Load exercise safety data.
    
    Returns:
        pd.DataFrame: Exercise safety information
    """
    return load_csv("exercise_safety_comprehensive.csv")


def load_recovery_exercises() -> pd.DataFrame:
    """
    Load recovery exercises data.
    
    Returns:
        pd.DataFrame: Recovery exercises information
    """
    return load_csv("recovery_exercises_comprehensive.csv")


def load_all_data() -> dict:
    """
    Load all CSV datasets and return them in a dictionary.
    
    Returns:
        dict: Dictionary with dataset names as keys and DataFrames as values
        
    Keys:
        - exercises: Comprehensive exercise data
        - food_nutrition: Food nutrition data
        - food_prices: Food price data
        - pain_keywords: Pain keywords data
        - exercise_contraindications: Exercise contraindications
        - exercise_safety: Exercise safety information
        - recovery_exercises: Recovery exercises
    """
    datasets = {
        'exercises': load_exercises(),
        'food_nutrition': load_food_nutrition(),
        'food_prices': load_food_prices(),
        'pain_keywords': load_pain_keywords(),
        'exercise_contraindications': load_exercise_contraindications(),
        'exercise_safety': load_exercise_safety(),
        'recovery_exercises': load_recovery_exercises()
    }
    
    return datasets


if __name__ == "__main__":
    """
    Test block to verify all CSV files load successfully.
    Prints dataset names and their shapes.
    """
    print("=" * 60)
    print("WellFit Data Loader - Testing All Datasets")
    print("=" * 60)
    print()
    
    try:
        # Load all datasets
        data = load_all_data()
        
        # Print information about each dataset
        print(f"Successfully loaded {len(data)} datasets:\n")
        
        for name, df in data.items():
            print(f"  {name:30s} : {df.shape[0]:5d} rows × {df.shape[1]:3d} columns")
        
        print()
        print("=" * 60)
        print("SUCCESS: All CSV files loaded successfully!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

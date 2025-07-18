#!/usr/bin/env python3
"""Download required NLTK data for the application."""
import nltk
import sys

def download_nltk_data():
    """Download required NLTK data packages."""
    packages = ['punkt_tab', 'punkt', 'stopwords']
    
    print("Downloading NLTK data packages...")
    
    for package in packages:
        try:
            nltk.data.find(f'tokenizers/{package}')
            print(f"✓ {package} already downloaded")
        except LookupError:
            try:
                print(f"  Downloading {package}...")
                nltk.download(package, quiet=False)
                print(f"✓ {package} downloaded successfully")
            except Exception as e:
                print(f"✗ Failed to download {package}: {e}")
    
    print("\nNLTK data download complete!")

if __name__ == "__main__":
    download_nltk_data()
#!/usr/bin/env python3
"""
Review Analysis Runner Script

This script analyzes the reviews_devset.json file and outputs:
- Count of positive/neutral/negative reviews
- Number of profane reviews  
- List of banned customers

Usage:
    python run_analysis.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.review_analyzer import main

if __name__ == "__main__":
    main() 
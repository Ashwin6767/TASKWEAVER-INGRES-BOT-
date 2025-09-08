#!/usr/bin/env python3
"""
Test script for keyword search functionality in groundwater plugin
"""

import sys
import os

# Add the plugin directory to path
sys.path.append(os.path.dirname(__file__))

from groundwater_plugin import keyword_search_data, extract_relevant_data, answer_question, load_all_reports

def test_keyword_search():
    print("Testing Keyword Search Functionality")
    print("=" * 50)
    
    try:
        # Load data
        df = load_all_reports()
        print(f"Loaded {len(df)} total records")
        print(f"Columns available: {list(df.columns)}")
        print()
        
        # Test keyword searches
        test_keywords = ["Maharashtra", "Mumbai", "well", "level", "water"]
        
        for keyword in test_keywords:
            print(f"Searching for keyword: '{keyword}'")
            results = keyword_search_data([keyword], df)
            print(f"Found {len(results)} matching records")
            
            if not results.empty:
                # Show sample of matches
                print("Sample results:")
                for col in results.columns[:5]:  # Show first 5 columns
                    if results[col].dtype == 'object':
                        unique_vals = results[col].dropna().unique()[:3]
                        print(f"  {col}: {', '.join(map(str, unique_vals))}")
            print("-" * 30)
        
        # Test extract_relevant_data function
        print("\nTesting extract_relevant_data:")
        questions = [
            "What is the groundwater level in Maharashtra?",
            "Show me wells near Mumbai",
            "Water quality in Karnataka"
        ]
        
        for question in questions:
            print(f"\nQuestion: {question}")
            relevant_data, keywords = extract_relevant_data(question)
            print(f"Extracted keywords: {keywords}")
            print(f"Found {len(relevant_data)} relevant records")
        
        # Test full answer_question function
        print("\n" + "=" * 50)
        print("Testing Full Question Answering:")
        
        test_questions = [
            "What is the average groundwater level in Maharashtra?",
            "Show me data about wells",
            "Which areas have the highest water levels?",
            "Compare groundwater between states"
        ]
        
        for question in test_questions:
            print(f"\nQ: {question}")
            answer = answer_question(question)
            print(f"A: {answer}")
            print("-" * 40)
            
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_keyword_search()

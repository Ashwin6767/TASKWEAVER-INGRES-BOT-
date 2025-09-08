from groundwater_plugin import load_all_reports, answer_question

# Test the data loading
print("=" * 50)
print("TESTING DATA LOADING")
print("=" * 50)

try:
    df = load_all_reports()
    print(f"\nDataframe shape: {df.shape}")
    print(f"\nColumn names (first 10): {list(df.columns)[:10]}")
    
    # Check if we have key columns
    key_columns = ['S.No', 'STATE', 'DISTRICT']
    for col in key_columns:
        if col in df.columns:
            print(f"\n{col} values (first 5): {df[col].dropna().unique()[:5]}")
    
    # Show first few rows of key columns
    print(f"\nFirst 3 data rows:")
    display_cols = [col for col in ['S.No', 'STATE', 'DISTRICT', 'ASSESSMENT UNIT'] if col in df.columns]
    if display_cols:
        print(df[display_cols].head(3))
    
    print("\n" + "=" * 50)
    print("TESTING QUESTION ANSWERING")
    print("=" * 50)
    
    # Test questions
    questions = [
        "What states are available in the data?",
        "Show me data for Andhra Pradesh",
        "What districts are in the dataset?",
        "Tell me about groundwater in Karnataka"
    ]
    
    for q in questions:
        print(f"\nQ: {q}")
        answer = answer_question(q)
        print(f"A: {answer[:200]}..." if len(answer) > 200 else f"A: {answer}")
        print("-" * 30)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

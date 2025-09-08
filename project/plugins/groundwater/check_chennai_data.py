from groundwater_plugin import load_all_reports
import pandas as pd

# Load data and check what we have for Chennai
df = load_all_reports()
print("Total records:", len(df))

# Search for Chennai data
chennai_data = df[df['DISTRICT'].str.contains('Chennai', case=False, na=False)]
print(f"\nChennai records found: {len(chennai_data)}")

if not chennai_data.empty:
    print("\nChennai data columns:")
    print(chennai_data.columns.tolist())
    
    print("\nChennai data sample:")
    print(chennai_data.head())
    
    # Show numeric columns with data
    numeric_cols = chennai_data.select_dtypes(include=['number']).columns
    print(f"\nNumeric columns with data:")
    for col in numeric_cols:
        non_null = chennai_data[col].dropna()
        if len(non_null) > 0:
            print(f"- {col}: {non_null.iloc[0]:.2f}" if pd.notna(non_null.iloc[0]) else f"- {col}: No data")

# Also check Tamil Nadu data
tn_data = df[df['STATE'].str.contains('TAMIL NADU', case=False, na=False)]
print(f"\nTamil Nadu records: {len(tn_data)}")
if not tn_data.empty:
    print("Tamil Nadu districts:")
    print(tn_data['DISTRICT'].unique()[:10])  # Show first 10 districts

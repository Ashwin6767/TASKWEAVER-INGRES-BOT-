from groundwater_plugin import load_all_reports
import pandas as pd

# Load data and get Chennai specific data
df = load_all_reports()
chennai_data = df[df['DISTRICT'].str.contains('Chennai', case=False, na=False)]

print("DETAILED CHENNAI GROUNDWATER DATA")
print("=" * 50)

# Key columns that have actual data
key_columns = [
    'S.No', 'STATE', 'DISTRICT', 'Rainfall (mm)', 
    'Total Geographical Area (ha)',
    'Ground Water Recharge (ham)',
    'Annual Ground water Recharge (ham)',
    'Annual Extractable Ground water Resource (ham)',
    'Ground Water Extraction for all uses (ha.m)',
    'Stage of Ground Water Extraction (%)',
    'Net Annual Ground Water Availability for Future Use (ham)',
    'Total Ground Water Availability in the area (ham)',
    'SourceFile'
]

for i, row in chennai_data.iterrows():
    year = row['SourceFile'].replace('CentralReport', '').replace('.xlsx', '')
    print(f"\nCHENNAI DATA FOR {year}:")
    print("-" * 30)
    
    for col in key_columns:
        if col in chennai_data.columns:
            value = row[col]
            if pd.notna(value) and col not in ['S.No', 'STATE', 'DISTRICT', 'SourceFile']:
                print(f"{col}: {value}")

print("\n" + "=" * 50)
print("SUMMARY ACROSS ALL YEARS:")
print("=" * 50)

# Calculate averages and trends
numeric_cols = ['Rainfall (mm)', 'Annual Ground water Recharge (ham)', 
                'Annual Extractable Ground water Resource (ham)',
                'Ground Water Extraction for all uses (ha.m)',
                'Stage of Ground Water Extraction (%)',
                'Total Ground Water Availability in the area (ham)']

for col in numeric_cols:
    if col in chennai_data.columns:
        data = chennai_data[col].dropna()
        if len(data) > 0:
            print(f"\n{col}:")
            print(f"  Average: {data.mean():.2f}")
            print(f"  Range: {data.min():.2f} to {data.max():.2f}")
            print(f"  Latest (2024-25): {data.iloc[-1]:.2f}" if len(data) > 0 else "  Latest: No data")

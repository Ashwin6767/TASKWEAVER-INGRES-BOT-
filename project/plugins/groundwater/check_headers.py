import pandas as pd
import glob

files = glob.glob('CentralReport*.xlsx')
df = pd.read_excel(files[0], header=None)

print('Finding header row:')
for i in range(20):
    row_str = ' '.join([str(x) for x in df.iloc[i].values if pd.notna(x)])
    if 'S.No' in row_str and 'STATE' in row_str:
        print(f'Row {i}: {row_str}')
        print(f'Full row {i}:')
        print(df.iloc[i].values[:20])  # First 20 columns
        break

print('\nTesting proper loading:')
df_proper = pd.read_excel(files[0], header=7)  # Assuming row 7 is header
df_proper = df_proper.dropna(how='all')
print(f'Columns: {list(df_proper.columns)[:10]}')
print(f'First data row: {df_proper.iloc[0].values[:5]}')

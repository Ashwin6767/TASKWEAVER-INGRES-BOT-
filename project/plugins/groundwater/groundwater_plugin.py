import pandas as pd
import os
import glob
import re

def load_all_reports():
    # Find all Excel files matching the pattern in the current directory
    folder = os.path.dirname(__file__)
    files = glob.glob(os.path.join(folder, "CentralReport*.xlsx"))
    dfs = []
    for file in files:
        df = pd.read_excel(file)
        df['SourceFile'] = os.path.basename(file)  # Optional: track source
        dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        raise FileNotFoundError("No CentralReport Excel files found in the plugins directory.")

def get_average_groundwater_level(state):
    df = load_all_reports()
    if 'State' not in df.columns or 'GroundwaterLevel' not in df.columns:
        raise ValueError("Excel files must have 'State' and 'GroundwaterLevel' columns.")
    state_data = df[df['State'].str.lower() == state.lower()]
    if state_data.empty:
        return f"No data found for state: {state}"
    avg_level = state_data['GroundwaterLevel'].mean()
    return avg_level

def answer_question(question):
    if "average" in question.lower() and "groundwater" in question.lower():
        df = load_all_reports()
        # Try to match any state, district, or city in the data
        for col in ['State', 'District', 'Location', 'City', 'Area', 'Place', 'Region']:
            if col in df.columns:
                for value in df[col].dropna().unique():
                    if re.search(rf'\b{re.escape(str(value))}\b', question, re.IGNORECASE):
                        filtered = df[df[col].str.lower() == str(value).lower()]
                        if not filtered.empty and 'GroundwaterLevel' in filtered.columns:
                            avg = filtered['GroundwaterLevel'].mean()
                            return f"The average groundwater level in {value} is {avg} meters."
        return "Sorry, I can only answer questions about average groundwater levels for locations present in the data."
    return "Sorry, I can only answer questions about average groundwater levels for locations present in the data."

# Example usage (for testing):
if __name__ == "__main__":
    q = "What is the average groundwater level in Maharashtra?"
    print(answer_question(q))

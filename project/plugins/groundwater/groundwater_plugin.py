import pandas as pd
import os
import glob
import re
import json
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

def configure_gemini():
    """
    Configure Gemini API with the API key from TaskWeaver config
    """
    if not GEMINI_AVAILABLE:
        return False
    
    try:
        # Try to read API key from TaskWeaver config
        config_path = os.path.join(os.path.dirname(__file__), "../../taskweaver_config.json")
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                api_key = config.get("llm.api_key")
                if api_key and api_key != "your api key":
                    genai.configure(api_key=api_key)
                    return True
        
        # Fallback to environment variable
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            return True
            
        return False
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return False

def load_all_reports():
    """
    Find all Excel files matching the pattern in the current directory and load them properly
    """
    folder = os.path.dirname(__file__)
    files = glob.glob(os.path.join(folder, "CentralReport*.xlsx"))
    dfs = []
    
    for file in files:
        try:
            # Read with header at row 7 (0-indexed), which contains the main headers
            df = pd.read_excel(file, header=7)
            
            # Clean up the dataframe
            # Remove completely empty rows
            df = df.dropna(how='all')
            
            # Remove rows where S.No is NaN (these are usually sub-headers or empty rows)
            if 'S.No' in df.columns:
                df = df[df['S.No'].notna()]
                # Convert S.No to numeric, keeping only valid numeric entries
                df = df[pd.to_numeric(df['S.No'], errors='coerce').notna()]
                # Convert S.No to integer for better handling
                df['S.No'] = pd.to_numeric(df['S.No'], errors='coerce').astype('Int64')
            
            # Clean up column names - remove extra spaces and make them more readable
            df.columns = [str(col).strip() if pd.notna(col) else f'Unnamed_{i}' 
                         for i, col in enumerate(df.columns)]
            
            # Remove columns that are entirely NaN
            df = df.dropna(axis=1, how='all')
            
            # Add source file information
            df['SourceFile'] = os.path.basename(file)
            dfs.append(df)
            print(f"Successfully loaded {len(df)} records from {os.path.basename(file)}")
                
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        print(f"Total records loaded: {len(combined_df)}")
        print(f"Available columns: {list(combined_df.columns)[:10]}...")  # Show first 10 columns
        return combined_df
    else:
        raise FileNotFoundError("No CentralReport Excel files found or could be parsed in the plugins directory.")

def keyword_search_data(keywords, df=None):
    """
    Search for keywords across all columns and return matching rows
    """
    if df is None:
        df = load_all_reports()
    
    if isinstance(keywords, str):
        keywords = [keywords]
    
    matching_rows = []
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        # Search across all string columns
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                mask = df[col].astype(str).str.lower().str.contains(keyword_lower, na=False)
                matches = df[mask]
                if not matches.empty:
                    matching_rows.append(matches)
    
    if matching_rows:
        # Combine all matches and remove duplicates
        combined = pd.concat(matching_rows, ignore_index=True)
        return combined.drop_duplicates()
    else:
        return pd.DataFrame()

def extract_relevant_data(question, max_rows=50):
    """
    Extract relevant data based on the question using keyword search
    """
    df = load_all_reports()
    
    # Extract potential keywords from the question
    # Remove common stop words but keep location-related words
    stop_words = {'what', 'is', 'the', 'in', 'of', 'for', 'and', 'or', 'but', 'a', 'an', 'how', 'where', 'when', 'why', 'tell', 'me', 'about', 'show', 'give'}
    words = re.findall(r'\b[a-zA-Z]+\b', question.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Add specific location mappings for common alternate names
    location_mappings = {
        'chennai': ['chennai', 'madras', 'tamil nadu'],
        'mumbai': ['mumbai', 'bombay', 'maharashtra'],
        'bangalore': ['bangalore', 'bengaluru', 'karnataka'],
        'hyderabad': ['hyderabad', 'telangana', 'andhra pradesh'],
        'delhi': ['delhi', 'new delhi', 'ncr'],
        'kolkata': ['kolkata', 'calcutta', 'west bengal']
    }
    
    # Expand keywords based on mappings
    expanded_keywords = keywords.copy()
    for keyword in keywords:
        for key, alternatives in location_mappings.items():
            if keyword in alternatives:
                expanded_keywords.extend(alternatives)
    
    # Remove duplicates
    expanded_keywords = list(set(expanded_keywords))
    
    # Search for matches
    relevant_data = keyword_search_data(expanded_keywords, df)
    
    # If no direct matches, try broader searches
    if relevant_data.empty and keywords:
        # Try searching with just the main location terms
        location_keywords = [kw for kw in keywords if len(kw) > 3]  # Longer words more likely to be locations
        if location_keywords:
            relevant_data = keyword_search_data(location_keywords, df)
    
    # Limit the number of rows to avoid overwhelming the response
    if len(relevant_data) > max_rows:
        relevant_data = relevant_data.head(max_rows)
    
    return relevant_data, expanded_keywords

def send_to_gemini(question, data_context):
    """
    Send question and data context to Gemini API for intelligent response
    """
    if not GEMINI_AVAILABLE:
        return "Gemini API not available. Please install google-generativeai package."
    
    if not configure_gemini():
        return "Gemini API key not configured. Please set your API key in taskweaver_config.json or GOOGLE_API_KEY environment variable."
    
    try:
        # Convert data to a readable format for the AI
        if data_context.empty:
            context_text = "No specific data found for this query."
        else:
            # Create detailed summary with actual numbers
            context_text = "SPECIFIC GROUNDWATER DATA:\n\n"
            
            # Location information
            if 'STATE' in data_context.columns and 'DISTRICT' in data_context.columns:
                for _, row in data_context.iterrows():
                    state = row.get('STATE', 'Unknown')
                    district = row.get('DISTRICT', 'Unknown')
                    year = row.get('SourceFile', '').replace('CentralReport', '').replace('.xlsx', '')
                    
                    context_text += f"📍 {district}, {state} ({year}):\n"
                    
                    # Key measurements with actual values
                    key_metrics = {
                        'Annual Ground water Recharge (ham)': 'Yearly water refill from rain',
                        'Annual Extractable Ground water Resource (ham)': 'Safely extractable water',
                        'Ground Water Extraction for all uses (ha.m)': 'Current water usage',
                        'Stage of Ground Water Extraction (%)': 'Extraction intensity',
                        'Total Ground Water Availability in the area (ham)': 'Total available groundwater',
                        'Net Annual Ground Water Availability for Future Use (ham)': 'Water available for future use'
                    }
                    
                    for metric, description in key_metrics.items():
                        if metric in data_context.columns:
                            value = row.get(metric)
                            if pd.notna(value) and value != 0:
                                if 'ham' in metric:
                                    context_text += f"  • {description}: {value:.1f} hectare-meters\n"
                                elif '%' in metric:
                                    context_text += f"  • {description}: {value:.1f}%\n"
                                else:
                                    context_text += f"  • {description}: {value:.1f}\n"
                    context_text += "\n"
            
            # Add trend analysis if multiple years
            if len(data_context) > 1:
                context_text += "TRENDS ANALYSIS:\n"
                numeric_cols = ['Annual Ground water Recharge (ham)', 'Total Ground Water Availability in the area (ham)']
                for col in numeric_cols:
                    if col in data_context.columns:
                        values = data_context[col].dropna()
                        if len(values) > 1:
                            trend = "increasing" if values.iloc[-1] > values.iloc[0] else "decreasing"
                            context_text += f"• {col}: {trend} from {values.iloc[0]:.1f} to {values.iloc[-1]:.1f}\n"
        
        prompt = f"""
        You are a helpful groundwater expert. A user has asked: "{question}"
        
        Based on the specific groundwater data below, provide a detailed, practical response with actual numbers and clear insights.
        
        GUIDELINES:
        1. Use the ACTUAL NUMBERS provided - don't say "data varies" when you have specific values
        2. Explain what the numbers mean in practical terms
        3. Point out trends if data spans multiple years
        4. Use simple language but be specific with measurements
        5. If the data shows concerning trends, mention them
        6. Include units (hectare-meters = ham) and explain what they represent if needed
        
        {context_text}
        
        Provide a comprehensive answer with specific numbers and practical insights.
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"

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
    """
    Enhanced question answering with keyword search and Gemini integration
    """
    try:
        # First, try to extract relevant data based on keywords
        relevant_data, keywords = extract_relevant_data(question)
        
        # If we have GEMINI_AVAILABLE and relevant data, use AI for better response
        if GEMINI_AVAILABLE and not relevant_data.empty:
            return send_to_gemini(question, relevant_data)
        
        # Enhanced fallback for when Gemini isn't available
        if not relevant_data.empty:
            # Create detailed user-friendly summary with actual data
            summary = f"📍 **GROUNDWATER DATA FOUND:**\n\n"
            
            # Show locations found
            if 'STATE' in relevant_data.columns and 'DISTRICT' in relevant_data.columns:
                for _, row in relevant_data.iterrows():
                    state = row.get('STATE', 'Unknown')
                    district = row.get('DISTRICT', 'Unknown') 
                    year = row.get('SourceFile', '').replace('CentralReport', '').replace('.xlsx', '')
                    
                    summary += f"🏘️ **{district}, {state}** ({year}):\n"
                    
                    # Key water data with actual numbers
                    if 'Annual Ground water Recharge (ham)' in relevant_data.columns:
                        recharge = row.get('Annual Ground water Recharge (ham)')
                        if pd.notna(recharge) and recharge > 0:
                            summary += f"   💧 **Water Refill from Rain**: {recharge:.1f} hectare-meters per year\n"
                    
                    if 'Total Ground Water Availability in the area (ham)' in relevant_data.columns:
                        total_water = row.get('Total Ground Water Availability in the area (ham)')
                        if pd.notna(total_water) and total_water > 0:
                            summary += f"   🗄️ **Total Available Water**: {total_water:.1f} hectare-meters\n"
                    
                    if 'Annual Extractable Ground water Resource (ham)' in relevant_data.columns:
                        extractable = row.get('Annual Extractable Ground water Resource (ham)')
                        if pd.notna(extractable) and extractable > 0:
                            summary += f"   ⚡ **Safely Extractable Water**: {extractable:.1f} hectare-meters per year\n"
                    
                    if 'Ground Water Extraction for all uses (ha.m)' in relevant_data.columns:
                        extraction = row.get('Ground Water Extraction for all uses (ha.m)')
                        if pd.notna(extraction) and extraction > 0:
                            summary += f"   🚰 **Current Water Usage**: {extraction:.1f} hectare-meters per year\n"
                    
                    if 'Stage of Ground Water Extraction (%)' in relevant_data.columns:
                        stage = row.get('Stage of Ground Water Extraction (%)')
                        if pd.notna(stage) and stage > 0:
                            summary += f"   📊 **Extraction Level**: {stage:.1f}% of available resources\n"
                    
                    summary += "\n"
            
            # Add trend analysis if multiple records
            if len(relevant_data) > 1:
                summary += "📈 **TRENDS**:\n"
                key_cols = ['Annual Ground water Recharge (ham)', 'Total Ground Water Availability in the area (ham)']
                for col in key_cols:
                    if col in relevant_data.columns:
                        values = relevant_data[col].dropna()
                        if len(values) >= 2:
                            change = values.iloc[-1] - values.iloc[0]
                            trend = "↗️ Increasing" if change > 0 else "↘️ Decreasing" if change < 0 else "➡️ Stable"
                            col_simple = "Water Refill" if "Recharge" in col else "Total Water"
                            summary += f"   {trend} {col_simple}: {values.iloc[0]:.1f} to {values.iloc[-1]:.1f}\n"
            
            # Add explanation
            summary += "\n💡 **What this means**:\n"
            summary += "• Hectare-meters (ham) = volume of water over 1 hectare, 1 meter deep\n"
            summary += "• Higher recharge = more rainwater refilling underground water\n"
            summary += "• Extraction level shows how intensively water is being used\n"
            
            return summary
        
        # If no relevant data found, provide helpful guidance
        df = load_all_reports()
        available_states = df['STATE'].dropna().unique() if 'STATE' in df.columns else []
        available_districts = df['DISTRICT'].dropna().unique() if 'DISTRICT' in df.columns else []
        
        guidance = f"🔍 I couldn't find specific data matching your query, but I have groundwater information for:\n\n"
        
        if len(available_states) > 0:
            guidance += f"🗺️ **Available States**: {', '.join(available_states[:8])}\n"
        
        if len(available_districts) > 0:
            guidance += f"🏘️ **Available Areas**: {', '.join(available_districts[:12])}\n"
        
        guidance += f"\n💬 Try asking about:\n"
        guidance += f"• 'Groundwater in [state name]'\n"
        guidance += f"• 'Water conditions in [district name]'\n"
        guidance += f"• 'Rainfall in [area name]'\n"
        guidance += f"• 'Water availability in [region]'"
        
        return guidance
        
    except Exception as e:
        return f"⚠️ I encountered an issue processing your question: {str(e)}\n\nPlease try asking about groundwater conditions in a specific state or district."

# Example usage (for testing):
if __name__ == "__main__":
    # Test examples
    test_questions = [
        "What is the average groundwater level in Maharashtra?",
        "Show me data for wells near Mumbai",
        "Which areas have declining groundwater levels?",
        "Compare groundwater between different districts",
        "What is the trend in Karnataka groundwater data?"
    ]
    
    for q in test_questions:
        print(f"\nQuestion: {q}")
        print(f"Answer: {answer_question(q)}")
        print("-" * 50)

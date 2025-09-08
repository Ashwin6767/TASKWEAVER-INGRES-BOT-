# Groundwater Data Analysis Plugin

This plugin provides intelligent groundwater data analysis capabilities for TaskWeaver, integrating keyword search with AI-powered insights.

## Features

- **Keyword Search**: Search across multiple Excel files containing groundwater data
- **AI Integration**: Uses Google Gemini API for intelligent data interpretation
- **User-Friendly**: Provides layman-accessible explanations of technical data
- **Multi-Year Analysis**: Analyzes trends across multiple years of data
- **Location-Based Queries**: Supports state, district, and region-specific queries

## Data Sources

The plugin analyzes Central Groundwater Board reports from:
- 2019-20
- 2021-22
- 2022-23
- 2023-24
- 2024-25

## Usage Examples

- "ground water data for chennai"
- "water availability in kerala"
- "rainfall trends in maharashtra"
- "which areas have declining groundwater"

## Configuration

Ensure your `taskweaver_config.json` includes a valid Google Gemini API key:
```json
{
  "llm.api_key": "your_gemini_api_key_here"
}
```

## Files

- `groundwater_plugin.py`: Main plugin implementation
- `CentralReport*.xlsx`: Groundwater data files from Central Groundwater Board


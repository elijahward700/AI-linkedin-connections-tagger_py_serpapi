# LinkedIn Interest Tagger

A Python tool that automatically tags your LinkedIn connections with relevant professional interests using OpenAI's GPT-4 and SerpAPI.

## Features

- Automatically analyzes LinkedIn connections
- Uses SerpAPI to gather profile information
- Tags connections with relevant professional interests using GPT-4
- Processes first 5 connections by default (configurable)
- Handles CSVs with or without notes
- Supports quoted file paths

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- SerpAPI key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/linkedin-interest-tagger.git
cd linkedin-interest-tagger
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your API keys:
```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_key
```

## Usage

1. Export your LinkedIn connections:
   - Go to LinkedIn
   - Navigate to "My Network" > "Connections"
   - Click "Manage my network" > "Connections"
   - Click "Export connections"
   - Download the CSV file

2. Run the script:
```bash
python linkedin_tagger.py
```

3. When prompted, enter the path to your LinkedIn connections CSV file.

4. The script will:
   - Process the first 5 connections
   - Gather profile information using SerpAPI
   - Analyze and tag interests using GPT-4
   - Save results to `linkedin_connections_with_interests.csv`

## Output

The script generates a CSV file (`linkedin_connections_with_interests.csv`) containing:
- Original connection information
- Additional profile data
- Tagged professional interests

## Notes

- The script processes only the first 5 connections by default to manage API usage
- Make sure your `.env` file contains valid API keys
- The script automatically handles CSVs with or without notes
- File paths can be entered with or without quotes

## License

MIT License 
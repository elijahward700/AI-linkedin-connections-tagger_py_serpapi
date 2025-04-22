import os
import pandas as pd
from openai import OpenAI
import logging
from dotenv import load_dotenv
import json
from typing import List, Dict
from serpapi_method import process_profiles as process_profiles_serpapi

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('linkedin_tagger.log'),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Define available interests
INTERESTS = [
    "Strategy", "Operations", "Entrepreneurship", "Leadership", "Management",
    "Marketing", "Sales", "Investing", "Personal Finance", "Corporate Finance",
    "Financial Planning", "Venture Capital", "Economics", "Artificial Intelligence",
    "Blockchain", "Cybersecurity", "Software Development", "Data Science",
    "Cloud Computing", "Remote Work", "Career Development", "Workplace Culture",
    "Job Hunting", "Networking", "Freelancing", "Mental Health", "Physical Fitness",
    "Nutrition", "Mindfulness", "Work-Life Balance", "Sleep", "Productivity",
    "Time Management", "Goal Setting", "Habits", "Self-Discipline", "Motivation",
    "Lifelong Learning", "Online Courses", "Reading", "Writing", "Public Speaking",
    "Critical Thinking", "Design", "Storytelling", "Content Creation", "Innovation",
    "Art", "Media", "Diversity & Inclusion", "Social Impact", "Ethics",
    "Global Trends", "Politics", "Sustainability", "Space Exploration",
    "Climate Change", "Biotech", "Futurism", "Quantum Computing",
    "Emerging Technologies"
]

def get_interests_from_profile(profile_text: str, person_info: Dict) -> List[str]:
    """
    Use OpenAI's API to analyze the profile and return relevant interests.
    """
    try:
        # Truncate profile text to reduce token count
        max_tokens = 2000
        truncated_text = profile_text[:max_tokens]
        
        prompt = f"""
        Based on the following LinkedIn profile information, select at least 5 most relevant interests from the provided list.
        Only select from these interests: {', '.join(INTERESTS)}
        
        Person's information:
        Name: {person_info['first_name']} {person_info['last_name']}
        Company: {person_info['company']}
        Position: {person_info['position']}
        
        Profile content:
        {truncated_text}
        
        Return the interests as a JSON array of strings, selecting the most relevant interests based on the profile information.
        """

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a professional career analyst. Your task is to analyze LinkedIn profiles and identify relevant professional interests and expertise areas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )

        # Extract and parse the interests from the response
        interests_text = response.choices[0].message.content
        interests = json.loads(interests_text)
        return interests[:10]  # Limit to 10 interests maximum

    except Exception as e:
        logging.error(f"Error getting interests for {person_info['first_name']} {person_info['last_name']}: {str(e)}")
        return []

def validate_csv_structure(df: pd.DataFrame) -> bool:
    """
    Validate that the CSV has the required columns for processing.
    """
    required_columns = ['First Name', 'Last Name', 'Company', 'Position']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        logging.error(f"CSV is missing required columns: {', '.join(missing_columns)}")
        return False
    return True

def read_linkedin_csv(file_path: str) -> pd.DataFrame:
    """
    Read LinkedIn CSV file, automatically handling notes if present.
    """
    try:
        # First, try reading without skipping rows
        df = pd.read_csv(file_path)
        
        # Check if the first few rows might be notes
        # Notes typically have fewer columns or contain text like "Notes" or "Export"
        first_row = df.iloc[0]
        if len(first_row) < 4 or any('note' in str(val).lower() for val in first_row):
            # Try reading again, skipping the first row
            df = pd.read_csv(file_path, skiprows=1)
            
            # Check if the second row might also be notes
            second_row = df.iloc[0]
            if len(second_row) < 4 or any('note' in str(val).lower() for val in second_row):
                # Skip both rows
                df = pd.read_csv(file_path, skiprows=2)
        
        return df
    
    except Exception as e:
        logging.error(f"Error reading CSV file: {str(e)}")
        raise

def main():
    """
    Main function to run the LinkedIn profile interest tagger.
    """
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OpenAI API key not found. Please set it in your .env file.")
    
    if not os.getenv('SERPAPI_API_KEY'):
        raise ValueError("SerpAPI key not found. Please set it in your .env file.")

    # Get input file from user and strip any quotes
    input_file = input("Enter the path to your LinkedIn connections CSV file: ").strip().strip("'\"")
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")
    
    output_file = 'linkedin_connections_with_interests.csv'
    
    # Read and validate the CSV file
    df = read_linkedin_csv(input_file)
    if not validate_csv_structure(df):
        raise ValueError("Invalid CSV structure. Please ensure your CSV contains the required columns: First Name, Last Name, Company, Position")
    
    # Limit to first 5 connections
    df = df.head(5)
    logging.info(f"Processing first 5 profiles using SerpAPI method")
    
    # Process profiles using SerpAPI
    process_profiles_serpapi(df, output_file)
    
    logging.info(f"Process completed. Results saved to {output_file}")

if __name__ == "__main__":
    main() 
import os
import requests
import logging
import time
import pandas as pd
import json
from typing import Dict, List
from openai import OpenAI

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

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

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
        Example response format: ["Leadership", "Management", "Strategy", "Innovation", "Career Development"]
        """

        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a professional career analyst. Your task is to analyze LinkedIn profiles and identify relevant professional interests and expertise areas. Always return a valid JSON array of strings."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={ "type": "json_object" }
        )

        # Extract and parse the interests from the response
        interests_text = response.choices[0].message.content
        try:
            # Try to parse as JSON object first
            interests_data = json.loads(interests_text)
            if isinstance(interests_data, dict) and "interests" in interests_data:
                interests = interests_data["interests"]
            else:
                # If not a dict with "interests" key, try parsing as array directly
                interests = json.loads(interests_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract interests from text
            interests = []
            for interest in INTERESTS:
                if interest.lower() in interests_text.lower():
                    interests.append(interest)
            if not interests:
                interests = ["Profile inaccessible"]

        return interests[:10]  # Limit to 10 interests maximum

    except Exception as e:
        logging.error(f"Error getting interests for {person_info['first_name']} {person_info['last_name']}: {str(e)}")
        return ["Profile inaccessible"]

def get_linkedin_profile_data(url: str) -> str:
    """
    Get LinkedIn profile data using SerpAPI's Google Search API.
    """
    try:
        # Extract the profile ID from the URL
        profile_id = url.split('/in/')[-1].split('/')[0]
        
        # SerpAPI endpoint for Google Search
        api_url = "https://serpapi.com/search"
        
        params = {
            "engine": "google",  # Using Google Search engine
            "api_key": os.getenv('SERPAPI_API_KEY'),
            "q": f"site:linkedin.com/in/{profile_id}",  # Search for the specific LinkedIn profile
            "hl": "en",  # Language
            "gl": "us",  # Country
            "num": 10,   # Number of results to return
            "filter": 0  # Don't filter similar results
        }
        
        response = requests.get(api_url, params=params)
        
        # Check for rate limiting
        if response.status_code == 429:
            logging.warning("Rate limit reached. Waiting before retry...")
            time.sleep(60)  # Wait for 1 minute
            return get_linkedin_profile_data(url)  # Retry
        
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant profile information
        profile_info = []
        
        if 'organic_results' in data:
            for result in data['organic_results']:
                if 'title' in result:
                    profile_info.append(result['title'])
                if 'snippet' in result:
                    profile_info.append(result['snippet'])
                if 'link' in result and profile_id in result['link']:
                    # This is likely the main profile result
                    if 'about_this_result' in result:
                        profile_info.append(result['about_this_result'].get('description', ''))
        
        # If we found any information, return it
        if profile_info:
            return ' '.join(profile_info).strip()
        
        logging.warning("No profile information found in search results")
        return ""
    
    except Exception as e:
        logging.error(f"Error getting profile data from SerpAPI: {str(e)}")
        return ""

def process_profiles(df: pd.DataFrame, output_file: str) -> None:
    """
    Process profiles using SerpAPI method.
    """
    try:
        # Add new column for interests if it doesn't exist
        if 'Interests' not in df.columns:
            df['Interests'] = ''
        
        logging.info(f"Processing {len(df)} profiles")
        
        # Process each profile
        for index, row in df.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            logging.info(f"Processing profile for {name}")
            
            # Get profile data using SerpAPI
            profile_text = get_linkedin_profile_data(row['URL'])
            
            if profile_text:
                # Get interests using OpenAI
                person_info = {
                    'first_name': row['First Name'],
                    'last_name': row['Last Name'],
                    'company': row['Company'],
                    'position': row['Position']
                }
                
                interests = get_interests_from_profile(profile_text, person_info)
                
                # Update DataFrame
                df.at[index, 'Interests'] = ', '.join(interests)
                
                # Save progress after each profile
                df.to_csv(output_file, index=False)
                
                # Add delay to respect rate limits
                time.sleep(2)
            else:
                logging.warning(f"Could not fetch profile content for {name}")
                df.at[index, 'Interests'] = "Profile inaccessible"
        
        logging.info("SerpAPI processing completed successfully")
        
    except Exception as e:
        logging.error(f"Error processing profiles with SerpAPI: {str(e)}")
        raise 
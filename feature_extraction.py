# -*- coding: utf-8 -*-
"""feature_extraction.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1ACLQdAT7pW8mbUO8qQ9tQFPfDAASkOZA
"""

import pandas as pd
from textblob import TextBlob
import re
from datetime import datetime

# Load the CSV file
comments_df = pd.read_csv('filtered_comments.csv')

# Define functions for feature extraction
def extract_sentiment_and_polarity(comment):
    """Analyze the sentiment of the comment and return sentiment and polarity score."""
    blob = TextBlob(comment)
    polarity = blob.sentiment.polarity
    sentiment = "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"
    return sentiment, polarity

def extract_keywords(comment):
    """Extract keywords from the comment based on capitalized words or stock symbols."""
    words = re.findall(r'\b[A-Z]{2,}\b', comment)  # Finds words with all uppercase letters, often stock symbols
    return ', '.join(words) if words else None

def calculate_comment_length(comment):
    """Calculate the length of the comment."""
    return len(comment)

def extract_time_features(created_utc):
    """Extract day of the week and time of day from the timestamp."""
    date = datetime.fromtimestamp(created_utc)
    day_of_week = date.strftime("%A")  # Full weekday name
    time_of_day = date.strftime("%H:%M")  # Time in hours and minutes
    return day_of_week, time_of_day

# Apply feature extraction to the DataFrame
comments_df[['sentiment', 'polarity_score']] = comments_df['comment'].apply(
    lambda x: pd.Series(extract_sentiment_and_polarity(x))
)
comments_df['keywords'] = comments_df['comment'].apply(extract_keywords)
comments_df['comment_length'] = comments_df['comment'].apply(calculate_comment_length)
comments_df[['day_of_week', 'time_of_day']] = comments_df['created_utc'].apply(
    lambda x: pd.Series(extract_time_features(x))
)
comments_df['date'] = comments_df['created_utc'].apply(
    lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d')
)

# Display the updated DataFrame
print(comments_df.head())

# Save the updated DataFrame to a new CSV file if needed
comments_df.to_csv('filtered_comments_with_features.csv', index=False)


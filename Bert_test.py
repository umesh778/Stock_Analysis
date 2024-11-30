import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
from nltk.sentiment import SentimentIntensityAnalyzer
from datetime import datetime
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import subjectivity
from nltk.sentiment import SentimentAnalyzer
from nltk.sentiment.util import *
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
#
#
# Data needs to be merged in a way where we can get sentiment from reddit and news, and match it with stock
# The length difference wont allow us to use train_split accurately
#
#


# Function to convert date to unix
def date_to_unix(date_str, date_format="%Y-%m-%d %H:%M:%S"):
    dt = datetime.strptime(date_str, date_format)
    return dt.timestamp()

# Function for sentiment analysis using Twitter-RoBERTa
def predict_roberta_sentiment(comment):
    inputs = tokenizer(comment, return_tensors="pt", truncation=True, padding=True, max_length=512)
    outputs = model(**inputs)
    probabilities = softmax(outputs.logits, dim=-1).detach().numpy()[0]
    sentiment_score = probabilities[2] - probabilities[0]  # Positive - Negative
    return sentiment_score

# Load Twitter-RoBERTa model and tokenizer
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

# 1. Load Data
reddit_data = pd.read_csv('C:/Users/ash/PycharmProjects/636-dataproject/data/combined_reddit.csv')  # Scraped Reddit posts
stock_data = pd.read_csv('C:/Users/ash/PycharmProjects/636-dataproject/data/combined_prices.csv')  # Historical stock data
news_data = pd.read_csv('C:/Users/ash/PycharmProjects/636-dataproject/data/combine_news.csv')  # News headlines

# 2. Preprocessing
# Reddit and News Sentiment
reddit_data['RobertaSentiment'] = reddit_data['comment'].apply(lambda x: predict_roberta_sentiment(x))
news_data['RobertaSentiment'] = news_data['Summary'].apply(lambda x: predict_roberta_sentiment(x))
stock_data['Volume'] = stock_data['Volume'].apply(lambda x: float(x.replace(",", "")))

#news_data['WeightedSentiment'] = news_data['RobertaSentiment'] * news_data['score']
reddit_data['WeightedSentiment'] = reddit_data['RobertaSentiment'] * reddit_data['score']

#delt with some length and 0 issues
stock_data['Open'] = stock_data['Open'].fillna(0)
stock_data['Close'] = stock_data['Close'].fillna(0)
stock_data['Volume'] = stock_data['Volume'].fillna(0)

#test lengths
print(len(reddit_data['WeightedSentiment']), len(news_data['RobertaSentiment']))

# Stock Data Features
scaler = StandardScaler()
stock_data_scaled = scaler.fit_transform(stock_data[['Open', 'Close', 'Volume']])

# Convert stock data to categorical labels based on a threshold
threshold = 0
stock_labels = np.where(stock_data_scaled[:, 1] > threshold, 'Increase', 'Decrease')

# 3. Feature Engineering

#in an attempt to fix length error, reshape the data
min_length = min(len(reddit_data['WeightedSentiment']), len(news_data['RobertaSentiment']))
reddit_sentiment_trimmed = reddit_data['WeightedSentiment'].values[:min_length].reshape(-1, 1)
news_sentiment_trimmed = news_data['RobertaSentiment'].values[:min_length].reshape(-1, 1)

combined_features = np.hstack([reddit_sentiment_trimmed, news_sentiment_trimmed])

# Ensure the sizes match
#same attempt to fix length error
min_length = min(len(combined_features), len(stock_labels))
combined_features = combined_features[:min_length]
stock_labels = stock_labels[:min_length]

# 4. Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(combined_features, stock_labels, test_size=0.3, random_state=42)

# Convert the data into the format required by NaiveBayesClassifier, Naive uses dictionaries
train_data = [({f'feature_{i}': X_train[j][i] for i in range(len(X_train[j]))}, y_train[j]) for j in range(len(X_train))]
test_data = [({f'feature_{i}': X_test[j][i] for i in range(len(X_test[j]))}, y_test[j]) for j in range(len(X_test))]

# 5. Train the NaiveBayesClassifier
classifier = NaiveBayesClassifier.train(train_data)

# 6. Evaluation
#uses nltk
accuracy = nltk.classify.accuracy(classifier, test_data)
print(f"Accuracy: {accuracy}")

# Print the classification report
y_pred = [classifier.classify({f'feature_{i}': x[i] for i in range(len(x))}) for x in X_test]
print(classification_report(y_test, y_pred))

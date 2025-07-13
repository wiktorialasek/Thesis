import pandas as pd
import numpy as np
import requests
import zipfile
import io
import os
from datetime import timedelta
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix

# 1. Load tweets data
tweets = pd.read_csv('tweets_TRUMP.csv')

# Keep only text and timestamp
if {'text', 'timestamp'}.issubset(tweets.columns):
    tweets = tweets[['text', 'timestamp']]
else:
    # adjust column names if necessary
    tweets = tweets.iloc[:, :2]
    tweets.columns = ['text', 'timestamp']

# Convert to datetime (UTC)
tweets['timestamp'] = pd.to_datetime(tweets['timestamp'], utc=True)

# 2. Assign stock_label based on keywords
def assign_label(text):
    t = str(text).lower()
    if any(k in t for k in ['dollar', '$', 'usd', 'greenback']):
        return 'dollar'
    if any(k in t for k in ['euro', 'eur', '€']):
        return 'euro'
    if any(k in t for k in ['s&p', 's&p500', 'sp500', '^gspc']):
        return 'sp500'
    return None

tweets['stock_label'] = tweets['text'].apply(assign_label)
tweets = tweets.dropna(subset=['stock_label'])

# 3. Download market data from GitHub
base_url = 'https://github.com/philipperemy/FX-1-Minute-Data/raw/master'
zip_map = {
    'euro': 'EURUSD.zip',
    'dollar': 'USDOLLAR.zip',
    'sp500': 'SPXUSD.zip',
}

os.makedirs('market_data', exist_ok=True)

for label, zip_name in zip_map.items():
    url = f"{base_url}/{zip_name}"
    dest_path = os.path.join('market_data', zip_name)
    if not os.path.exists(dest_path.replace('.zip', '.csv')):
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall('market_data')

# Load market data as DataFrames
data = {}
for label, zip_name in zip_map.items():
    csv_name = zip_name.replace('.zip', '.csv')
    df = pd.read_csv(os.path.join('market_data', csv_name))
    # guess date column name
    if 'Date' in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'], utc=True)
    elif 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'], utc=True)
    else:
        df['datetime'] = pd.to_datetime(df.iloc[:,0], utc=True)
    data[label] = df.sort_values('datetime')

# 4. Compute price changes
def compute_changes(df, times):
    df = df.sort_values('datetime')
    results = {}
    for col, t in times.items():
        merged = pd.merge_asof(pd.DataFrame({'target': t}), df, left_on='target', right_on='datetime', direction='backward')
        results[col] = merged['Close'].values
    return results

intervals = {
    'price_now': tweets['timestamp'],
    'p_1min': tweets['timestamp'] + timedelta(minutes=1),
    'p_5min': tweets['timestamp'] + timedelta(minutes=5),
    'p_10min': tweets['timestamp'] + timedelta(minutes=10),
    'p_1h': tweets['timestamp'] + timedelta(hours=1),
    'p_1d': tweets['timestamp'] + timedelta(days=1),
}

for label in ['euro', 'dollar', 'sp500']:
    mask = tweets['stock_label'] == label
    idx = mask[mask].index
    if len(idx) == 0:
        continue
    subset = tweets.loc[idx]
    res = compute_changes(data[label], {k:v.loc[idx] for k,v in intervals.items()})
    for col, values in res.items():
        tweets.loc[idx, col] = values

# next day open
for label in ['euro', 'dollar', 'sp500']:
    df = data[label]
    df['date'] = df['datetime'].dt.date
    open_prices = df.groupby('date')['Open'].first()
    mask = tweets['stock_label'] == label
    next_days = tweets.loc[mask, 'timestamp'].dt.date + pd.Timedelta(days=1)
    tweets.loc[mask, 'p_next_open'] = open_prices.reindex(next_days).values

# 5. Percent changes
tweets['change_1min'] = (tweets['p_1min'] - tweets['price_now']) / tweets['price_now'] * 100
tweets['change_5min'] = (tweets['p_5min'] - tweets['price_now']) / tweets['price_now'] * 100
tweets['change_10min'] = (tweets['p_10min'] - tweets['price_now']) / tweets['price_now'] * 100
tweets['change_1h'] = (tweets['p_1h'] - tweets['price_now']) / tweets['price_now'] * 100
tweets['change_1d'] = (tweets['p_1d'] - tweets['price_now']) / tweets['price_now'] * 100
tweets['change_next_open'] = (tweets['p_next_open'] - tweets['price_now']) / tweets['price_now'] * 100

# 6. Labeling
max_change = tweets[['change_1min','change_5min','change_10min','change_1h','change_1d','change_next_open']].max(axis=1)
min_change = tweets[['change_1min','change_5min','change_10min','change_1h','change_1d','change_next_open']].min(axis=1)

conditions = [max_change > 0.5, min_change < -0.5]
choices = ['increase', 'decrease']
tweets['label'] = np.select(conditions, choices, default='neutral')

# 7. Text classification model
vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
X = vectorizer.fit_transform(tweets['text'])
y = tweets['label']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

clf = LogisticRegression(max_iter=1000)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

acc = accuracy_score(y_test, y_pred)
prec = precision_score(y_test, y_pred, average='weighted')
rec = recall_score(y_test, y_pred, average='weighted')
cm = confusion_matrix(y_test, y_pred)

print('Accuracy:', acc)
print('Precision:', prec)
print('Recall:', rec)
print('Confusion Matrix:\n', cm)

# Save result
tweets.to_csv('tweets_with_market.csv', index=False)

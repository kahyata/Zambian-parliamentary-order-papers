import pandas as pd
import re
from datetime import datetime
import nltk
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

df_path = '../datasets/parliament_questions.csv'
output_path = '../datasets/parliament_questions_features.csv'

df = pd.read_csv(df_path)
df = df[df['question_text'].str.strip().astype(bool)]

def parse_date_from_title(title_str):
    if not isinstance(title_str, str):
        return None
    title_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', title_str)
    title_str = title_str.replace(',', '')
    try:
        return datetime.strptime(title_str, '%A %d %B %Y')
    except:
        return None

def extract_features(row):
    features = {}
    
    # Date features from document_title
    date_obj = parse_date_from_title(row['document_title'])
    if date_obj:
        features['day_of_week'] = date_obj.strftime('%A')
        features['day'] = int(date_obj.day)
        features['month'] = int(date_obj.month)
        features['year'] = int(date_obj.year)
    else:
        features['day_of_week'] = None
        features['day'] = None
        features['month'] = None
        features['year'] = None
    
    # Metadata
    features['document_title'] = row.get('document_title')
    features['document_type'] = row.get('document_type')
    features['session'] = row.get('session')
    features['question_number'] = row.get('question_number')
    features['asked_by'] = row.get('asked_by')
    features['minister'] = row.get('minister')
    features['section'] = row.get('section')
    
    return pd.Series(features)

features_df = df.apply(extract_features, axis=1)

# Ensure integers for date columns
features_df['day'] = features_df['day'].fillna(0).astype(int)
features_df['month'] = features_df['month'].fillna(0).astype(int)
features_df['year'] = features_df['year'].fillna(0).astype(int)

features_df.to_csv(output_path, index=False)
print("Feature table saved to:", output_path)
print(features_df.head().T)

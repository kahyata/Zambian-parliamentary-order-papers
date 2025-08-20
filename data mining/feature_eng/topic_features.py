import pandas as pd
import re

class TopicFeatureEngine:
    """Extracts only essential topic features"""
    
    def __init__(self):
        # Simplified sector keywords
        self.sector_keywords = {
            'infrastructure': ['road', 'bridge', 'construction', 'building', 'highway', 'housing', 'urban development'],
            'energy': ['electricity', 'power', 'energy', 'fuel', 'solar', 'hydro', 'coal', 'petroleum', 'zesco'],
            'health': ['health', 'hospital', 'clinic', 'medical', 'doctor', 'disease', 'medicine', 'patient'],
            'mines': ['mining', 'copper', 'mineral', 'mine', 'extraction', 'emerald', 'quarry'],
            'waste_management': ['waste', 'garbage', 'sanitation', 'sewage', 'pollution', 'drainage', 'refuse'],
            'agriculture': ['farming', 'agriculture', 'crop', 'farmer', 'livestock', 'maize', 'fertilizer', 'irrigation'],
            'manufacturing': ['manufacturing', 'factory', 'industry', 'production', 'industrial', 'processing'],
            'tourism': ['tourism', 'tourist', 'hotel', 'wildlife', 'victoria falls', 'safari', 'resort'],
            'technology': ['technology', 'digital', 'internet', 'computer', 'ict', 'broadband', 'fiber'],
            'transport': ['transport', 'road', 'railway', 'airport', 'bus', 'taxi', 'logistics'],
            'education': ['education', 'school', 'university', 'teacher', 'student', 'curriculum', 'scholarship'],
            'finance': ['finance', 'budget', 'money', 'kwacha', 'tax', 'revenue', 'banking', 'loan']
        }
        
    def extract_topic_features(self, df):
        """Extract only essential topic features"""
        print("Extracting essential topic features...")
        
        if 'question_text' not in df.columns:
            return df
            
        # Clean text
        df['question_text_clean'] = df['question_text'].str.lower().fillna('')
        
        # Simple sector classification
        for sector, keywords in self.sector_keywords.items():
            pattern = '|'.join(keywords)
            df[f'topic_{sector}'] = df['question_text_clean'].str.contains(
                pattern, na=False
            ).astype(int)
        
        # Remove multi_sector_question
        df['sector_count'] = df[[f'topic_{sector}' for sector in self.sector_keywords.keys()]].sum(axis=1)
        
        # Clean up temporary column
        if 'question_text_clean' in df.columns:
            df = df.drop('question_text_clean', axis=1)
        
        return df
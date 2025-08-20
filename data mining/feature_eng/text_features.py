import pandas as pd

class TextFeatureEngine:
    """No text features - all removed as requested"""
    
    def __init__(self):
        pass
        
    def extract_text_features(self, df):
        """No text features extracted"""
        print("Skipping text features (removed as requested)...")
        return df
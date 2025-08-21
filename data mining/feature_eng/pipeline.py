from .temporal_features import TemporalFeatureEngine
from .text_features import TextFeatureEngine
from .topic_features import TopicFeatureEngine
from .demographic_features import DemographicFeatureEngine
from .network_features import NetworkFeatureEngine
from .performance_features import PerformanceFeatureEngine

class FeatureEngineeringPipeline:
    """Simplified pipeline with essential features only"""
    
    def __init__(self):
        self.temporal_engine = TemporalFeatureEngine()
        self.text_engine = TextFeatureEngine()
        self.topic_engine = TopicFeatureEngine()
        self.demographic_engine = DemographicFeatureEngine()
        self.network_engine = NetworkFeatureEngine()
        self.performance_engine = PerformanceFeatureEngine()
        
    def engineer_features(self, df, feature_types='all'):
        """
        Main method to engineer essential features only
        """
        print(f"Starting simplified feature engineering pipeline...")
        print(f"Input dataset shape: {df.shape}")
        
        # Make a copy to avoid modifying original
        df_features = df.copy()
        
        # Apply feature engineering based on requested types
        if feature_types == 'all':
            feature_types = ['temporal', 'topic', 'demographic']
            # Remove 'text', 'network', 'performance' from default features
            
        if 'temporal' in feature_types:
            df_features = self.temporal_engine.extract_temporal_features(df_features)
            
        if 'text' in feature_types:
            df_features = self.text_engine.extract_text_features(df_features)
            
        if 'topic' in feature_types:
            df_features = self.topic_engine.extract_topic_features(df_features)
            
        if 'demographic' in feature_types:
            df_features = self.demographic_engine.extract_demographic_features(df_features)
            
        # Skip network and performance features
        print("Skipping text, network and performance features...")
            
        print(f"Simplified feature engineering complete!")
        print(f"Output dataset shape: {df_features.shape}")
        
        return df_features
    
    def get_feature_summary(self, df):
        """Generate summary of essential features only"""
        feature_categories = {
            'Temporal Features': [col for col in df.columns if col in [
                'formatted_date', 'formatted_time', 'parliament_session'
            ]],
            'Topic Features': [col for col in df.columns if col.startswith('topic_') or col == 'sector_count'],
            'Demographic Features': [col for col in df.columns if col in ['mp_gender', 'constituency']]
        }
        
        print("\n" + "="*60)
        print("ESSENTIAL FEATURE ENGINEERING SUMMARY")
        print("="*60)
        
        for category, features in feature_categories.items():
            if features:
                print(f"\n{category} ({len(features)} features):")
                for feature in sorted(features):
                    print(f"  • {feature}")
        
        print(f"\nTotal Features: {len(df.columns)}")
        print(f"Dataset Shape: {df.shape}")
        
        return feature_categories

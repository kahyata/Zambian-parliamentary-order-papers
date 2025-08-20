import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
from collections import Counter, defaultdict
from textstat import flesch_reading_ease, flesch_kincaid_grade
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.sentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True) 
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

class TemporalFeatureEngine:
    """Extracts time-based patterns from parliamentary questions"""
    
    def __init__(self):
        self.features = {}
        
    def extract_temporal_features(self, df):
        """Extract comprehensive temporal features"""
        print("Extracting temporal features...")
        
        # Ensure date column exists and is datetime
        if 'date' not in df.columns:
            print("Warning: No date column found. Skipping temporal features.")
            return df
            
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Basic time features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        
        # Parliamentary session patterns
        df['parliamentary_year'] = df['year'] - df['year'].min() + 1
        df['session_quarter'] = ((df['month'] - 1) // 3) + 1
        
        # Question timing patterns
        df = df.sort_values('date')
        df['question_sequence'] = df.groupby('date').cumcount() + 1
        df['questions_per_day'] = df.groupby('date')['question_number'].transform('count')
        
        # MP activity patterns
        df['mp_questions_total'] = df.groupby('asked_by')['question_number'].transform('count')
        df['mp_questions_this_year'] = df.groupby(['asked_by', 'year'])['question_number'].transform('count')
        df['mp_activity_rate'] = df['mp_questions_this_year'] / df.groupby('year')['question_number'].transform('count')
        
        # Minister workload patterns
        df['minister_questions_total'] = df.groupby('minister')['question_number'].transform('count')
        df['minister_questions_this_month'] = df.groupby(['minister', 'year', 'month'])['question_number'].transform('count')
        
        # Seasonal patterns
        df['is_budget_season'] = df['month'].isin([10, 11, 12]).astype(int)  # Budget preparation months
        df['is_election_year'] = (df['year'] % 5 == 1).astype(int)  # Zambia elections every 5 years
        
        return df

class TextFeatureEngine:
    """Extracts linguistic and semantic features from question text"""
    
    def __init__(self):
        self.sia = SentimentIntensityAnalyzer()
        self.stop_words = set(stopwords.words('english'))
        self.tfidf = TfidfVectorizer(max_features=100, stop_words='english')
        
    def extract_text_features(self, df):
        """Extract comprehensive text features"""
        print("Extracting text features...")
        
        if 'question_text' not in df.columns:
            print("Warning: No question_text column found. Skipping text features.")
            return df
            
        # Clean and prepare text
        df['question_text'] = df['question_text'].fillna('')
        
        # Basic text statistics
        df['text_length'] = df['question_text'].str.len()
        df['word_count'] = df['question_text'].apply(lambda x: len(str(x).split()))
        df['sentence_count'] = df['question_text'].apply(lambda x: len(sent_tokenize(str(x))))
        df['avg_word_length'] = df['question_text'].apply(
            lambda x: np.mean([len(word) for word in str(x).split()]) if str(x).split() else 0
        )
        
        # Readability scores
        df['flesch_score'] = df['question_text'].apply(
            lambda x: flesch_reading_ease(str(x)) if str(x).strip() else 0
        )
        df['flesch_grade'] = df['question_text'].apply(
            lambda x: flesch_kincaid_grade(str(x)) if str(x).strip() else 0
        )
        
        # Sentiment analysis
        sentiment_scores = df['question_text'].apply(
            lambda x: self.sia.polarity_scores(str(x))
        )
        df['sentiment_positive'] = [score['pos'] for score in sentiment_scores]
        df['sentiment_negative'] = [score['neg'] for score in sentiment_scores]
        df['sentiment_neutral'] = [score['neu'] for score in sentiment_scores]
        df['sentiment_compound'] = [score['compound'] for score in sentiment_scores]
        
        # Question type classification
        df['is_yes_no_question'] = df['question_text'].str.contains(
            r'\b(is|are|will|would|can|could|should|do|does|did)\b', case=False, na=False
        ).astype(int)
        
        df['is_how_question'] = df['question_text'].str.contains(
            r'\bhow\b', case=False, na=False
        ).astype(int)
        
        df['is_why_question'] = df['question_text'].str.contains(
            r'\bwhy\b', case=False, na=False
        ).astype(int)
        
        df['is_what_question'] = df['question_text'].str.contains(
            r'\bwhat\b', case=False, na=False
        ).astype(int)
        
        df['is_when_question'] = df['question_text'].str.contains(
            r'\bwhen\b', case=False, na=False
        ).astype(int)
        
        df['is_where_question'] = df['question_text'].str.contains(
            r'\bwhere\b', case=False, na=False
        ).astype(int)
        
        # Urgency indicators
        df['urgency_score'] = df['question_text'].apply(self._calculate_urgency)
        
        # Topic complexity
        df['contains_numbers'] = df['question_text'].str.contains(r'\d+', na=False).astype(int)
        df['contains_percentages'] = df['question_text'].str.contains(r'\d+%', na=False).astype(int)
        df['contains_money'] = df['question_text'].str.contains(
            r'(kwacha|K\d|million|billion|budget|fund)', case=False, na=False
        ).astype(int)
        
        return df
    
    def _calculate_urgency(self, text):
        """Calculate urgency score based on keywords"""
        urgency_words = ['urgent', 'immediate', 'crisis', 'emergency', 'critical', 
                        'serious', 'alarming', 'concern', 'problem', 'issue']
        text_lower = str(text).lower()
        return sum(1 for word in urgency_words if word in text_lower)

class TopicFeatureEngine:
    """Extracts topic and domain-specific features"""
    
    def __init__(self):
        self.sector_keywords = {
            'health': ['health', 'hospital', 'clinic', 'medical', 'doctor', 'nurse', 'disease', 'medicine'],
            'education': ['school', 'education', 'teacher', 'student', 'university', 'college', 'learning'],
            'infrastructure': ['road', 'bridge', 'construction', 'infrastructure', 'transport', 'airport'],
            'agriculture': ['farming', 'agriculture', 'crop', 'farmer', 'livestock', 'food', 'harvest'],
            'mining': ['mining', 'copper', 'mineral', 'mine', 'extraction', 'geology'],
            'water': ['water', 'borehole', 'well', 'sanitation', 'sewage', 'drainage'],
            'energy': ['electricity', 'power', 'energy', 'fuel', 'solar', 'hydro', 'coal'],
            'security': ['police', 'security', 'crime', 'safety', 'law', 'order'],
            'finance': ['budget', 'money', 'kwacha', 'tax', 'revenue', 'expenditure', 'finance'],
            'governance': ['government', 'ministry', 'policy', 'administration', 'governance']
        }
        
    def extract_topic_features(self, df):
        """Extract topic and sector-specific features"""
        print("Extracting topic features...")
        
        if 'question_text' not in df.columns:
            return df
            
        # Sector classification
        for sector, keywords in self.sector_keywords.items():
            pattern = '|'.join(keywords)
            df[f'topic_{sector}'] = df['question_text'].str.contains(
                pattern, case=False, na=False
            ).astype(int)
        
        # Multi-sector questions
        sector_cols = [f'topic_{sector}' for sector in self.sector_keywords.keys()]
        df['multi_sector_question'] = (df[sector_cols].sum(axis=1) > 1).astype(int)
        df['sector_count'] = df[sector_cols].sum(axis=1)
        
        # Dominant sector per question
        df['dominant_sector'] = df[sector_cols].idxmax(axis=1)
        df['dominant_sector'] = df['dominant_sector'].str.replace('topic_', '')
        
        # Geographic focus
        geographic_indicators = ['district', 'province', 'constituency', 'community', 'area', 'region']
        df['has_geographic_focus'] = df['question_text'].str.contains(
            '|'.join(geographic_indicators), case=False, na=False
        ).astype(int)
        
        return df

class DemographicFeatureEngine:
    """Extracts MP demographic and constituency features"""
    
    def __init__(self):
        # Common Zambian names patterns for gender inference
        self.male_names = {
            'mr', 'hon', 'captain', 'major', 'colonel', 'dr', 'prof',
            'abraham', 'andrew', 'anthony', 'boniface', 'brian', 'charles', 'christopher',
            'collins', 'cornelius', 'daniel', 'david', 'emmanuel', 'felix', 'francis',
            'george', 'gilbert', 'humphrey', 'isaac', 'jackson', 'james', 'john',
            'joseph', 'julius', 'kenneth', 'lawrence', 'leonard', 'lovemore', 'michael',
            'moses', 'mulenga', 'mutale', 'mwamba', 'nathan', 'nicholas', 'patrick',
            'paul', 'peter', 'richard', 'robert', 'samuel', 'stephen', 'thomas',
            'william', 'vincent', 'zebron'
        }
        
        self.female_names = {
            'mrs', 'ms', 'miss', 'madam', 'dr', 'prof',
            'alice', 'angela', 'barbara', 'beatrice', 'bridget', 'catherine', 'charity',
            'christine', 'deborah', 'dora', 'dorothy', 'edith', 'elizabeth', 'esther',
            'evelyn', 'faith', 'florence', 'grace', 'helen', 'jane', 'janet', 'joyce',
            'judith', 'julia', 'margaret', 'maria', 'mary', 'mercy', 'miriam', 'monica',
            'mutinta', 'nancy', 'patricia', 'priscilla', 'rebecca', 'ruth', 'sarah',
            'susan', 'sylvia', 'veronica', 'victoria'
        }
        
        # Zambian constituencies and provinces mapping
        self.province_constituencies = {
            'Central': ['Kabwe Central', 'Kapiri Mposhi', 'Mkushi North', 'Mkushi South', 'Mumbwa', 'Serenje'],
            'Copperbelt': ['Chililabombwe', 'Chingola', 'Kalulushi', 'Kitwe Central', 'Luanshya', 'Mufulira', 'Ndola Central'],
            'Eastern': ['Chipata Central', 'Lundazi', 'Mambwe', 'Nyimba', 'Petauke Central', 'Vubwi'],
            'Luapula': ['Kawambwa', 'Mansa Central', 'Milenge', 'Mwansabombwe', 'Mwense', 'Nchelenge', 'Samfya'],
            'Lusaka': ['Chongwe', 'Kafue', 'Lusaka Central', 'Matero', 'Munali', 'Rufunsa'],
            'Muchinga': ['Chinsali', 'Isoka', 'Kanchibiya', 'Lavushimanda', 'Nakonde', 'Shiwangandu'],
            'Northern': ['Kasama Central', 'Luwingu', 'Mbala', 'Mporokoso', 'Mpulungu', 'Senga Hill'],
            'North-Western': ['Kabompo', 'Manyinga', 'Mufumbwe', 'Mwinilunga', 'Solwezi Central', 'Zambezi'],
            'Southern': ['Choma', 'Kalomo', 'Livingstone', 'Mazabuka Central', 'Monze Central', 'Namwala'],
            'Western': ['Kaoma Central', 'Limulunga', 'Lukulu', 'Mongu Central', 'Nalolo', 'Senanga']
        }
        
    def extract_demographic_features(self, df):
        """Extract MP demographic and constituency features"""
        print("Extracting demographic and constituency features...")
        
        if 'asked_by' not in df.columns:
            print("Warning: No asked_by column found. Skipping demographic features.")
            return df
        
        # Extract constituency from MP name
        df['mp_name'] = df['asked_by'].str.strip()
        df['constituency'] = df['mp_name'].apply(self._extract_constituency)
        df['mp_cleaned_name'] = df['mp_name'].apply(self._clean_mp_name)
        
        # Infer MP gender from ORIGINAL name (before cleaning)
        df['mp_gender'] = df['mp_name'].apply(self._infer_gender)
        
        # Map constituency to province
        df['province'] = df['constituency'].apply(self._map_to_province)
        
        # Regional categorization
        df['is_urban_constituency'] = df['constituency'].apply(self._is_urban).astype(int)
        df['is_mining_region'] = df['province'].isin(['Copperbelt', 'North-Western']).astype(int)
        df['is_border_province'] = df['province'].isin(['Eastern', 'Muchinga', 'Northern', 'North-Western', 'Western']).astype(int)
        
        # MP name characteristics
        df['has_title'] = df['mp_name'].str.contains(r'\b(Hon|Mr|Mrs|Ms|Dr|Prof|Captain|Major|Colonel)\b', case=False, na=False).astype(int)
        df['name_length'] = df['mp_cleaned_name'].str.len()
        df['has_multiple_names'] = (df['mp_cleaned_name'].str.count(' ') >= 2).astype(int)
        
        return df
    
    def _extract_constituency(self, mp_name):
        """Extract constituency from MP name format 'Name (Constituency)'"""
        if pd.isna(mp_name):
            return 'Unknown'
        
        # Look for parentheses pattern
        match = re.search(r'\(([^)]+)\)', str(mp_name))
        if match:
            return match.group(1).strip()
        
        # If no parentheses, try to identify known constituencies in the name
        name_parts = str(mp_name).lower().split()
        for province, constituencies in self.province_constituencies.items():
            for constituency in constituencies:
                if any(part in constituency.lower() for part in name_parts):
                    return constituency
        
        return 'Unknown'
    
    def _clean_mp_name(self, mp_name):
        """Clean MP name by removing titles and constituency info"""
        if pd.isna(mp_name):
            return ''
        
        # Remove constituency in parentheses
        name = re.sub(r'\([^)]+\)', '', str(mp_name)).strip()
        
        # Remove common titles
        titles = ['Hon', 'Mr', 'Mrs', 'Ms', 'Dr', 'Prof', 'Captain', 'Major', 'Colonel']
        for title in titles:
            name = re.sub(rf'\b{title}\.?\s*', '', name, flags=re.IGNORECASE)
        
        return name.strip()
    
    def _infer_gender(self, original_mp_name):
        """Infer gender from original MP name using titles first"""
        if not original_mp_name or pd.isna(original_mp_name):
            return 'Unknown'
        
        name_lower = str(original_mp_name).lower()
        
        # First priority: Check titles (most reliable)
        if re.search(r'\b(mr|mister)\b', name_lower):
            return 'Male'
        elif re.search(r'\b(mrs|miss|ms|madam)\b', name_lower):
            return 'Female'
        
        # Second priority: Check for other gendered titles
        if re.search(r'\b(captain|major|colonel)\b', name_lower):
            return 'Male'  # Military titles typically male in Zambian context
        
        # Third priority: Check name parts against known names
        name_parts = name_lower.split()
        male_matches = sum(1 for part in name_parts if part in self.male_names)
        female_matches = sum(1 for part in name_parts if part in self.female_names)
        
        if male_matches > female_matches:
            return 'Male'
        elif female_matches > male_matches:
            return 'Female'
        
        # Fourth priority: Check for gendered endings in Zambian names
        clean_parts = [part for part in name_parts if part not in ['hon', 'dr', 'prof']]
        if clean_parts:
            last_name = clean_parts[-1]
            # Many Zambian female names end in 'a' but not all words ending in 'a'
            if last_name.endswith('a') and len(last_name) > 2 and not last_name.endswith(('ka', 'wa', 'za')):
                return 'Female'
        
        return 'Unknown'
    
    def _map_to_province(self, constituency):
        """Map constituency to province"""
        if pd.isna(constituency) or constituency == 'Unknown':
            return 'Unknown'
        
        for province, constituencies in self.province_constituencies.items():
            if constituency in constituencies:
                return province
            # Partial matching for variations
            if any(const.lower() in str(constituency).lower() for const in constituencies):
                return province
        
        return 'Unknown'
    
    def _is_urban(self, constituency):
        """Determine if constituency is urban based on name patterns"""
        if pd.isna(constituency):
            return False
        
        urban_indicators = ['central', 'town', 'city', 'urban']
        constituency_lower = str(constituency).lower()
        return any(indicator in constituency_lower for indicator in urban_indicators)

class NetworkFeatureEngine:
    """Extracts relationship and network features"""
    
    def __init__(self):
        pass
        
    def extract_network_features(self, df):
        """Extract MP-Minister network and collaboration features"""
        print("Extracting network features...")
        
        # MP-Minister interaction patterns
        mp_minister_pairs = df.groupby(['asked_by', 'minister']).size().reset_index(name='interaction_count')
        df = df.merge(
            mp_minister_pairs.rename(columns={'interaction_count': 'mp_minister_interactions'}),
            on=['asked_by', 'minister'],
            how='left'
        )
        
        # MP specialization metrics
        mp_minister_diversity = df.groupby('asked_by')['minister'].nunique().reset_index(name='minister_diversity')
        df = df.merge(mp_minister_diversity, on='asked_by', how='left')
        
        # Minister question load distribution
        minister_mp_diversity = df.groupby('minister')['asked_by'].nunique().reset_index(name='mp_diversity')
        df = df.merge(minister_mp_diversity, on='minister', how='left')
        
        # Collaboration indicators (MPs asking similar questions)
        # This is a simplified version - could be enhanced with text similarity
        df['mp_rank_by_activity'] = df.groupby('asked_by')['question_number'].transform('count').rank(ascending=False)
        df['minister_rank_by_workload'] = df.groupby('minister')['question_number'].transform('count').rank(ascending=False)
        
        # Regional representation patterns
        if 'province' in df.columns:
            df['province_questions_total'] = df.groupby('province')['question_number'].transform('count')
            df['province_mp_count'] = df.groupby('province')['asked_by'].transform('nunique')
            df['province_avg_questions_per_mp'] = df['province_questions_total'] / df['province_mp_count']
        
        # Gender representation patterns
        if 'mp_gender' in df.columns:
            df['gender_questions_total'] = df.groupby('mp_gender')['question_number'].transform('count')
            df['is_female_mp'] = (df['mp_gender'] == 'Female').astype(int)
        
        return df

class PerformanceFeatureEngine:
    """Extracts performance and accountability features"""
    
    def __init__(self):
        pass
        
    def extract_performance_features(self, df):
        """Extract accountability and performance tracking features"""
        print("Extracting performance features...")
        
        # Question follow-up patterns (simplified)
        df = df.sort_values(['asked_by', 'date'])
        df['mp_question_interval'] = df.groupby('asked_by')['date'].diff().dt.days
        df['mp_avg_question_interval'] = df.groupby('asked_by')['mp_question_interval'].transform('mean')
        
        # Persistence indicators
        df['mp_consistent_questioner'] = (df['mp_questions_total'] >= df['mp_questions_total'].median()).astype(int)
        
        # Minister pressure indicators
        df['minister_high_pressure'] = (
            df['minister_questions_total'] >= df['minister_questions_total'].quantile(0.75)
        ).astype(int)
        
        # Seasonal activity patterns
        df['end_of_year_activity'] = df['month'].isin([11, 12]).astype(int)
        df['start_of_year_activity'] = df['month'].isin([1, 2, 3]).astype(int)
        
        return df

class FeatureEngineeringPipeline:
    """Main pipeline orchestrating all feature engineering"""
    
    def __init__(self):
        self.temporal_engine = TemporalFeatureEngine()
        self.text_engine = TextFeatureEngine()
        self.topic_engine = TopicFeatureEngine()
        self.demographic_engine = DemographicFeatureEngine()  # Added demographic engine
        self.network_engine = NetworkFeatureEngine()
        self.performance_engine = PerformanceFeatureEngine()
        
    def engineer_features(self, df, feature_types='all'):
        """
        Main method to engineer features
        
        Args:
            df: Input dataframe with parliamentary questions
            feature_types: 'all' or list of ['temporal', 'text', 'topic', 'demographic', 'network', 'performance']
        """
        print(f"Starting feature engineering pipeline...")
        print(f"Input dataset shape: {df.shape}")
        
        # Make a copy to avoid modifying original
        df_features = df.copy()
        
        # Apply feature engineering based on requested types
        if feature_types == 'all':
            feature_types = ['temporal', 'text', 'topic', 'demographic', 'network', 'performance']
            
        if 'temporal' in feature_types:
            df_features = self.temporal_engine.extract_temporal_features(df_features)
            
        if 'text' in feature_types:
            df_features = self.text_engine.extract_text_features(df_features)
            
        if 'topic' in feature_types:
            df_features = self.topic_engine.extract_topic_features(df_features)
            
        if 'demographic' in feature_types:  # Added demographic feature extraction
            df_features = self.demographic_engine.extract_demographic_features(df_features)
            
        if 'network' in feature_types:
            df_features = self.network_engine.extract_network_features(df_features)
            
        if 'performance' in feature_types:
            df_features = self.performance_engine.extract_performance_features(df_features)
            
        print(f"Feature engineering complete!")
        print(f"Output dataset shape: {df_features.shape}")
        print(f"New features added: {df_features.shape[1] - df.shape[1]}")
        
        return df_features
    
    def get_feature_summary(self, df):
        """Generate summary of engineered features"""
        feature_categories = {
            'Temporal Features': [col for col in df.columns if any(word in col.lower() 
                                for word in ['year', 'month', 'day', 'quarter', 'session', 'activity_rate'])],
            'Text Features': [col for col in df.columns if any(word in col.lower() 
                            for word in ['text_', 'word_', 'sentence_', 'sentiment_', 'flesch', 'is_', 'urgency'])],
            'Topic Features': [col for col in df.columns if col.startswith('topic_') or 'sector' in col.lower()],
            'Demographic Features': [col for col in df.columns if any(word in col.lower() 
                                   for word in ['mp_', 'constituency', 'province', 'gender', 'urban', 'mining', 'border'])],  # Added demographic
            'Network Features': [col for col in df.columns if any(word in col.lower() 
                               for word in ['interaction', 'diversity', 'rank', 'female_mp'])],
            'Performance Features': [col for col in df.columns if any(word in col.lower() 
                                   for word in ['interval', 'consistent', 'pressure', 'end_of', 'start_of'])]
        }
        
        print("\n" + "="*60)
        print("FEATURE ENGINEERING SUMMARY")
        print("="*60)
        
        for category, features in feature_categories.items():
            if features:
                print(f"\n{category} ({len(features)} features):")
                for feature in features:
                    print(f"  • {feature}")
        
        print(f"\nTotal Features: {len(df.columns)}")
        print(f"Dataset Shape: {df.shape}")
        
        return feature_categories

def main():
    """Example usage of the feature engineering pipeline"""
    
    # Load your parliamentary questions dataset
    try:
        # Adjust path as needed
        df = pd.read_csv('datasets/parliament_questions.csv')
        print(f"Loaded dataset with {len(df)} questions")
    except FileNotFoundError:
        print("Dataset not found. Please ensure parliament_questions.csv exists in datasets folder.")
        return
    
    # Initialize the pipeline
    pipeline = FeatureEngineeringPipeline()
    
    # Engineer all features
    df_with_features = pipeline.engineer_features(df)
    
    # Generate feature summary
    feature_summary = pipeline.get_feature_summary(df_with_features)
    
    # Save enhanced dataset
    output_path = 'datasets/parliament_questions_with_features.csv'
    df_with_features.to_csv(output_path, index=False)
    print(f"\nEnhanced dataset saved to: {output_path}")
    
    # Optional: Create a sample analysis
    print("\n" + "="*60)
    print("SAMPLE FEATURE ANALYSIS")
    print("="*60)
    
    # Show most active MPs
    if 'mp_questions_total' in df_with_features.columns:
        top_mps = df_with_features.groupby('asked_by')['mp_questions_total'].first().nlargest(5)
        print(f"\nTop 5 Most Active MPs:")
        for mp, count in top_mps.items():
            print(f"  • {mp}: {count} questions")
    
    # Show sector distribution
    topic_cols = [col for col in df_with_features.columns if col.startswith('topic_')]
    if topic_cols:
        sector_totals = df_with_features[topic_cols].sum().sort_values(ascending=False)
        print(f"\nTop 5 Question Topics:")
        for sector, count in sector_totals.head().items():
            sector_name = sector.replace('topic_', '').title()
            print(f"  • {sector_name}: {count} questions")
    
    # Show gender and constituency distribution
    if 'mp_gender' in df_with_features.columns:
        gender_counts = df_with_features['mp_gender'].value_counts()
        print(f"\nMP Gender Distribution:")
        for gender, count in gender_counts.items():
            print(f"  • {gender}: {count} questions")
    
    if 'province' in df_with_features.columns:
        province_counts = df_with_features['province'].value_counts()
        print(f"\nTop 5 Provinces by Questions:")
        for province, count in province_counts.head().items():
            print(f"  • {province}: {count} questions")
    
    # Show temporal patterns
    if 'year' in df_with_features.columns:
        yearly_counts = df_with_features['year'].value_counts().sort_index()
        print(f"\nQuestions by Year:")
        for year, count in yearly_counts.items():
            print(f"  • {year}: {count} questions")

if __name__ == "__main__":
    main()
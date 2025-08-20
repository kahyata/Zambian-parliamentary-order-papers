import pandas as pd
import re

# Known Zambian female MPs database
KNOWN_FEMALE_MPS = {
    'mrs. mutinta mazoka': 'Female',
    'mrs. inonge wina': 'Female', 
    'ms. elizabeth phiri': 'Female',
    'mrs. sylvia masebo': 'Female',
    'mrs. dorothy kashiba': 'Female',
    'mrs. emeldah mwamba': 'Female',
    'mrs. beatrice mpanga': 'Female',
    'ms. princess kasune': 'Female',
    'mrs. mwamba mwamba': 'Female',
    'mrs. mwansa kapeya': 'Female',
    'mrs. victoria kalima': 'Female',
    'mrs. jean kapata': 'Female',
    'mrs. margaret mwanakatwe': 'Female',
    'mrs. charlotte scott': 'Female',
    'mrs. joyce sicheele': 'Female',
    'mrs. mary fulano': 'Female',
    'mrs. lillian siyuni': 'Female',
    'mrs. agness limbu': 'Female',
    'mrs. beatrice mofya': 'Female',
    'mrs. evelyn muleya': 'Female'
}

# Title mappings - updated with military ranks and proper case handling
TITLE_GENDER_MAPPING = {
    'mr': 'Male',
    'mister': 'Male',
    'mr.': 'Male',
    'brig': 'Male',
    'gen': 'Male',
    'brig.': 'Male',
    'gen.': 'Male',
    'dr': 'Unknown',  # Doctor could be either gender
    'dr.': 'Unknown',
    'prof': 'Unknown',  # Professor could be either gender
    'prof.': 'Unknown',
    'hon': 'Unknown',  # Honorable could be either gender
    'hon.': 'Unknown',
    'mrs': 'Female',
    'mrs.': 'Female',
    'miss': 'Female',
    'ms': 'Female',
    'ms.': 'Female',
    'madam': 'Female',
    'maam': 'Female',
    'madame': 'Female'
}

class DemographicFeatureEngine:
    """Extracts gender from titles and constituency from parentheses"""
    
    def __init__(self):
        self.known_female_mps = KNOWN_FEMALE_MPS
        self.title_gender_mapping = TITLE_GENDER_MAPPING
        
    def extract_demographic_features(self, df):
        """Extract gender and constituency from MP names"""
        print("Extracting demographic features...")
        
        if 'asked_by' not in df.columns:
            print("Warning: No asked_by column found.")
            return df
        
        # Extract gender and constituency
        df['mp_gender'] = df['asked_by'].apply(self._extract_gender_from_name)
        df['constituency'] = df['asked_by'].apply(self._extract_constituency_from_name)
        
        print(f"Gender distribution: {df['mp_gender'].value_counts().to_dict()}")
        
        # Show sample of extracted data for verification
        if len(df) > 0:
            print("\nSample of extracted demographics:")
            sample = df[['asked_by', 'mp_gender', 'constituency']].head(5)
            for _, row in sample.iterrows():
                print(f"  {row['asked_by']} -> Gender: {row['mp_gender']}, Constituency: {row['constituency']}")
        
        return df
    
    def _extract_gender_from_name(self, mp_name):
        """Extract gender from MP name using titles"""
        if not mp_name or pd.isna(mp_name):
            return 'Unknown'
        
        # Convert to lowercase for consistent matching
        clean_name = str(mp_name).strip().lower()
        
        # Check known MP database (most reliable)
        if clean_name in self.known_female_mps:
            return self.known_female_mps[clean_name]
        
        # Check titles in the name
        title_gender = self._detect_gender_from_title(clean_name)
        if title_gender != 'Unknown':
            return title_gender
        
        return 'Unknown'
    
    def _detect_gender_from_title(self, mp_name):
        """Detect gender from titles in the MP name"""
        # Look for titles at the beginning of the name or anywhere
        words = mp_name.split()
        
        # Check first word for title
        if words:
            first_word = words[0].lower().strip('.,()')
            if first_word in self.title_gender_mapping:
                gender = self.title_gender_mapping[first_word]
                if gender != 'Unknown':
                    return gender
        
        # Check all words for titles (in case title is not at start)
        for word in words:
            clean_word = word.lower().strip('.,()')
            if clean_word in self.title_gender_mapping:
                gender = self.title_gender_mapping[clean_word]
                if gender != 'Unknown':
                    return gender
        
        # Also check for title patterns with spaces (like "mr ")
        for title, gender in self.title_gender_mapping.items():
            if gender != 'Unknown' and re.search(rf'\b{re.escape(title)}\b', mp_name):
                return gender
        
        return 'Unknown'
    
    def _extract_constituency_from_name(self, mp_name):
        """Extract constituency from parentheses in MP name like 'Mr Nyambose (Chasefu)'"""
        if pd.isna(mp_name):
            return 'Unknown'
        
        name_str = str(mp_name)
        
        # Look for content in parentheses - most common pattern
        match = re.search(r'\(([^)]+)\)', name_str)
        if match:
            constituency = match.group(1).strip()
            # Basic validation to ensure it's not a title or honorific
            if (len(constituency) > 2 and 
                not any(title in constituency.lower() 
                       for title in ['mr', 'mrs', 'ms', 'dr', 'brig', 'gen', 'hon', 'prof'])):
                return constituency
        
        # Alternative pattern: look for constituency after comma or dash
        alternative_patterns = [
            r',\s*([^,()-]+)$',  # After comma at end
            r'-\s*([^,()-]+)$',  # After dash at end
            r'\bof\s+([^,()-]+)$',  # "of ConstituencyName"
        ]
        
        for pattern in alternative_patterns:
            match = re.search(pattern, name_str, re.IGNORECASE)
            if match:
                constituency = match.group(1).strip()
                if len(constituency) > 2 and not any(title in constituency.lower() 
                                                   for title in ['mr', 'mrs', 'ms', 'dr']):
                    return constituency
        
        return 'Unknown'
    
    def _clean_mp_name(self, mp_name):
        """Clean MP name by removing constituency and titles for display"""
        if pd.isna(mp_name):
            return ''
        
        # Remove constituency in parentheses
        name = re.sub(r'\([^)]+\)', '', str(mp_name)).strip()
        
        # Remove common titles from beginning
        titles = ['Mr', 'Mrs', 'Ms', 'Miss', 'Madam', 'Dr', 'Prof', 'Hon', 
                 'Brig', 'Gen', 'Brig.', 'Gen.', 'Dr.', 'Prof.', 'Hon.']
        
        for title in titles:
            name = re.sub(rf'^{re.escape(title)}\.?\\s*', '', name, flags=re.IGNORECASE)
        
        return name.strip()
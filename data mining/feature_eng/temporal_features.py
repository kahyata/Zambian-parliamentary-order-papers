import pandas as pd
import re
from datetime import datetime

class TemporalFeatureEngine:
    """Extracts time, date, and session features with proper formatting"""
    
    def __init__(self):
        pass
        
    def extract_temporal_features(self, df):
        """Extract time, date, and session features"""
        print("Extracting temporal features...")
        
        # Extract and format date if available
        if 'date' in df.columns:
            df['formatted_date'] = df['date'].apply(self._format_date)
        elif 'document_title' in df.columns:
            # Try to extract date from document title
            df['formatted_date'] = df['document_title'].apply(self._extract_and_format_date_from_title)
        
        # Extract session if available
        if 'session' in df.columns:
            df['parliament_session'] = df['session'].apply(self._extract_session)
        
        return df
    
    def _extract_and_format_date_from_title(self, title):
        """Extract and format date from document title in dd/mm/yy format"""
        if pd.isna(title) or not isinstance(title, str):
            return 'Unknown'
        
        # Try to extract date from titles like "Friday, 1st August, 2025" OR "5th December, 2023"
        date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+),?\s+(\d{4})', title, re.IGNORECASE)
        if date_match:
            day, month_name, year = date_match.groups()
            try:
                # Convert month name to number
                month_dict = {
                    'january': 1, 'february': 2, 'march': 3, 'april': 4,
                    'may': 5, 'june': 6, 'july': 7, 'august': 8,
                    'september': 9, 'october': 10, 'november': 11, 'december': 12
                }
                month = month_dict.get(month_name.lower(), 1)
                # Format as dd/mm/yy (last 2 digits of year)
                return f"{int(day):02d}/{int(month):02d}/{year[-2:]}"
            except Exception as e:
                print(f"Error parsing date '{title}': {e}")
                pass
        
        return 'Unknown'
    
    def _format_date(self, date_value):
        """Format date as dd/mm/yy (2-digit year)"""
        if pd.isna(date_value):
            return 'Unknown'
        
        try:
            # Handle string dates
            if isinstance(date_value, str):
                # First try the specific format "5th December, 2023"
                date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+),?\s+(\d{4})', date_value, re.IGNORECASE)
                if date_match:
                    day, month_name, year = date_match.groups()
                    month_dict = {
                        'january': 1, 'february': 2, 'march': 3, 'april': 4,
                        'may': 5, 'june': 6, 'july': 7, 'august': 8,
                        'september': 9, 'october': 10, 'november': 11, 'december': 12
                    }
                    month = month_dict.get(month_name.lower())
                    if month:
                        return f"{int(day):02d}/{int(month):02d}/{year[-2:]}"
                
                # Try to parse various other date formats
                date_formats = [
                    '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%Y/%m/%d',
                    '%d %B %Y', '%B %d, %Y', '%A, %d %B %Y', '%d-%b-%Y', '%d/%b/%Y'
                ]
                
                for fmt in date_formats:
                    try:
                        date_obj = datetime.strptime(date_value, fmt)
                        # Format as dd/mm/yy (2-digit year)
                        return date_obj.strftime('%d/%m/%y')
                    except ValueError:
                        continue
                
                # If no format matches, try to extract date-like patterns
                date_match = re.search(r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})\b', date_value)
                if date_match:
                    day, month, year = date_match.groups()
                    # Convert year to 2-digit format if it's 4 digits
                    if len(year) == 4:
                        year = year[-2:]
                    return f"{int(day):02d}/{int(month):02d}/{year}"
            
            # Handle datetime objects
            elif isinstance(date_value, (datetime, pd.Timestamp)):
                # Format as dd/mm/yy (2-digit year)
                return date_value.strftime('%d/%m/%y')
            
        except Exception as e:
            print(f"Error formatting date {date_value}: {e}")
        
        return 'Unknown'
    
    def _extract_session(self, session_value):
        """Extract parliamentary session information"""
        if pd.isna(session_value):
            return 'Unknown'
        
        if isinstance(session_value, str):
            # Common session patterns
            session_patterns = [
                r'(\d+(?:st|nd|rd|th)\s+Session)',
                r'(Session\s+\d+)',
                r'(National Assembly Session)',
                r'(Parliamentary Session)',
                r'(\d{4}[-/]\d{2,4})',  # Year ranges like 2023-2024
            ]
            
            for pattern in session_patterns:
                match = re.search(pattern, session_value, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
        
        return session_value
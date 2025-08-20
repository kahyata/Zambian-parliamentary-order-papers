import pandas as pd
import json
from pathlib import Path
import re

class JSONDataHandler:
    """Handles loading and processing of parliamentary questions JSON data"""
    
    def __init__(self, datasets_folder='datasets'):
        self.datasets_folder = Path(datasets_folder)
    
    def load_and_combine_datasets(self):
        """Load all JSON files and combine into a single DataFrame"""
        all_records = []
        
        if not self.datasets_folder.exists():
            raise FileNotFoundError(f"Datasets folder '{self.datasets_folder}' not found")
        
        json_files = list(self.datasets_folder.glob('*.json'))
        
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in '{self.datasets_folder}' folder")
        
        for json_file in json_files:
            print(f"Loading {json_file.name}...")
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Extract records from this file
                records = self._extract_records_from_file(data, json_file.name)
                all_records.extend(records)
                print(f"  Extracted {len(records)} questions")
                
            except Exception as e:
                print(f"  Error loading {json_file.name}: {e}")
                continue
        
        if all_records:
            df = pd.DataFrame(all_records)
            # Clean question text
            if 'question_text' in df.columns:
                df['question_text'] = df['question_text'].apply(self._clean_question_text)
            return df
        else:
            return pd.DataFrame()
    
    def _extract_records_from_file(self, data, filename):
        """Extract question records from a single JSON file with the given structure"""
        records = []
        
        # Check if this is the expected structure
        if not isinstance(data, dict) or 'questions' not in data:
            print(f"  Warning: Unexpected structure in {filename}")
            return records
        
        metadata = data.get('metadata', {})
        questions = data.get('questions', [])
        
        for question in questions:
            if not isinstance(question, dict):
                continue
                
            record = {
                'source_file': filename,
                'document_title': metadata.get('title', ''),
                'source_url': metadata.get('source_url', ''),
                'document_type': metadata.get('document_type', ''),
                'session': metadata.get('session', ''),
                'question_number': question.get('question_number', ''),
                'asked_by': question.get('asked_by', ''),
                'minister': question.get('minister', ''),
                'section': question.get('section', '')
            }
            
            # Extract question text from parts or question_text field
            question_text = self._extract_question_text(question)
            record['question_text'] = question_text
            
            # Extract date from title if available
            date_from_title = self._extract_date_from_title(metadata.get('title', ''))
            if date_from_title:
                record['date'] = date_from_title
            
            records.append(record)
        
        return records
    
    def _extract_question_text(self, question):
        """Extract question text from parts array or question_text field"""
        # First check if there's a direct question_text field
        if 'question_text' in question and question['question_text']:
            return question['question_text']
        
        # Otherwise, combine parts
        parts = question.get('parts', [])
        if parts and isinstance(parts, list):
            # Combine all parts into a single question text
            full_text = ' '.join([str(part) for part in parts if part])
            return full_text.strip()
        
        return ''
    
    def _extract_date_from_title(self, title):
        """Extract date from document title"""
        if not title:
            return None
        
        # Try to extract date from titles like "Friday, 1st August, 2025"
        date_patterns = [
            r'(\d{1,2}(?:st|nd|rd|th)?\s+\w+,\s+\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _clean_question_text(self, text):
        """Clean question text by removing xao/xao strings and other artifacts"""
        if pd.isna(text) or not isinstance(text, str):
            return text
        
        # Remove xao/xao patterns
        text = re.sub(r'xao/xao', '', text, flags=re.IGNORECASE)
        
        # Remove other common artifacts and clean up
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespace
        text = text.strip()
        
        return text
    
    def detect_column_mapping(self, df):
        """Detect and suggest column mappings for common question fields"""
        column_mapping = {}
        available_columns = df.columns.tolist()
        
        # Common field patterns in parliamentary questions data
        field_patterns = {
            'question_text': ['text', 'question', 'content', 'body', 'query'],
            'question_number': ['number', 'id', 'ref', 'reference', 'no', 'num'],
            'asked_by': ['author', 'mp', 'member', 'asker', 'questioner', 'raised_by'],
            'minister': ['ministry', 'respondent', 'answered_by', 'responsible', 'ministerial'],
            'date': ['time', 'timestamp', 'sitting_date', 'created', 'asked_date'],
            'constituency': ['area', 'region', 'district', 'location', 'electoral_area'],
            'session': ['period', 'term', 'sitting', 'assembly', 'parliamentary_session'],
            'answer_text': ['response', 'reply', 'answer', 'minister_response']
        }
        
        for target_field, patterns in field_patterns.items():
            if target_field not in available_columns:
                for pattern in patterns:
                    # Check for exact matches first
                    if pattern in available_columns:
                        column_mapping[target_field] = pattern
                        break
                    
                    # Check for partial matches (case-insensitive)
                    for actual_col in available_columns:
                        if pattern in actual_col.lower():
                            column_mapping[target_field] = actual_col
                            break
                    if target_field in column_mapping:
                        break
        
        return column_mapping
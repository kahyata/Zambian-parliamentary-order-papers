import json
import os
import pandas as pd
from datetime import datetime
import re

def extract_question_details(question):
    """Extract structured details from a question dictionary"""
    details = {
        'question_number': question.get('question_number', ''),
        'asked_by': question.get('asked_by', ''),
        'minister': question.get('minister', ''),
        'section': question.get('section', ''),
        'question_text': ' '.join(question.get('parts', [])),
        'parts_count': len(question.get('parts', []))
    }
    return details

def parse_date(date_str):
    """Robust date parsing with multiple format support"""
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Clean up date string
    date_str = re.sub(r'[^\w\s,]', '', date_str).strip()
    
    # Try multiple date formats
    date_formats = [
        '%A, %d %B, %Y', '%A, %d %b, %Y', 
        '%A, %d %B %Y', '%A, %d %b %Y',
        '%A %d %B %Y', '%A %d %b %Y',
        '%d %B %Y', '%d %b %Y'
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def process_json_file(filepath):
    """Process a single JSON file and return a DataFrame"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if data['status'] != 'success':
        return pd.DataFrame()
    
    metadata = data['metadata']
    questions = data['questions']
    
    # Extract and parse date
    date_obj = parse_date(metadata.get('date', ''))
    
    rows = []
    for question in questions:
        q_details = extract_question_details(question)
        row = {
            'document_title': metadata.get('title', ''),
            'source_url': metadata.get('source_url', ''),
            'document_type': metadata.get('document_type', ''),
            'session': metadata.get('session', ''),
            'date': date_obj,
            'year': date_obj.year if date_obj else None,
            **q_details
        }
        rows.append(row)
    
    return pd.DataFrame(rows)

def process_all_datasets():
    """Process all JSON files in the datasets folder"""
    dataset_files = [f for f in os.listdir('datasets') 
                    if f.endswith('.json') and f != 'all_parliament_questions.json']
    
    if not dataset_files:
        print("No JSON files found in the datasets folder")
        return pd.DataFrame()
    
    all_dfs = []
    for filename in dataset_files:
        filepath = os.path.join('datasets', filename)
        try:
            df = process_json_file(filepath)
            if not df.empty:
                all_dfs.append(df)
                print(f"Processed {filename} with {len(df)} questions")
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    if not all_dfs:
        return pd.DataFrame()
    
    # Combine all DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    # Clean and standardize data
    combined_df['asked_by'] = combined_df['asked_by'].str.strip()
    combined_df['minister'] = combined_df['minister'].str.strip()
    combined_df['section'] = combined_df['section'].str.strip()
    
    # Convert date column to datetime if not already
    if 'date' in combined_df.columns:
        combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
    
    # Sort by date (newest first)
    if 'date' in combined_df.columns:
        combined_df.sort_values(by='date', ascending=False, inplace=True)
    
    return combined_df

def save_to_excel(df, filename='parliament_questions.xlsx'):
    """Save DataFrame to Excel file with multiple sheets"""
    if df.empty:
        print("No data to save")
        return
    
    # Create a Pandas Excel writer
    writer = pd.ExcelWriter(os.path.join('datasets', filename), engine='xlsxwriter')
    
    # Save main data
    df.to_excel(writer, sheet_name='All Questions', index=False)
    
    # Create summary statistics with date range handling
    if 'date' in df.columns and not df['date'].isnull().all():
        min_date = df['date'].min()
        max_date = df['date'].max()
        date_range = f"{min_date.date()} to {max_date.date()}" if pd.notnull(min_date) and pd.notnull(max_date) else "N/A"
    else:
        date_range = "N/A"
    
    summary_stats = pd.DataFrame({
        'Total Questions': [len(df)],
        'Date Range': [date_range],
        'Unique MPs': [df['asked_by'].nunique()],
        'Unique Ministers': [df['minister'].nunique()],
        'Documents Processed': [df['document_title'].nunique()]
    }).transpose()
    
    summary_stats.to_excel(writer, sheet_name='Summary', header=False)
    
    # Create by-year summary
    if 'year' in df.columns:
        year_summary = df.groupby('year').agg({
            'question_number': 'count',
            'asked_by': pd.Series.nunique,
            'minister': pd.Series.nunique
        }).rename(columns={
            'question_number': 'Total Questions',
            'asked_by': 'Unique MPs',
            'minister': 'Unique Ministers'
        })
        year_summary.to_excel(writer, sheet_name='By Year')
    
    # Create top MPs summary
    if 'asked_by' in df.columns:
        top_mps = df['asked_by'].value_counts().head(20)
        top_mps.to_excel(writer, sheet_name='Top MPs')
    
    # Create top ministers summary
    if 'minister' in df.columns:
        top_ministers = df['minister'].value_counts().head(20)
        top_ministers.to_excel(writer, sheet_name='Top Ministers')
    
    # Save the file
    writer.close()
    print(f"Data saved to {filename} with multiple sheets")

if __name__ == "__main__":
    # Process all datasets
    questions_df = process_all_datasets()
    
    if not questions_df.empty:
        # Save to Excel with multiple sheets
        save_to_excel(questions_df)
        
        # Also save to CSV
        csv_path = os.path.join('datasets', 'parliament_questions.csv')
        questions_df.to_csv(csv_path, index=False)
        print(f"Data also saved to {csv_path}")
        
        # Print some summary info
        print("\nSummary Statistics:")
        print(f"- Total questions: {len(questions_df)}")
        
        if 'date' in questions_df.columns:
            min_date = questions_df['date'].min()
            max_date = questions_df['date'].max()
            if pd.notnull(min_date) and pd.notnull(max_date):
                print(f"- Date range: {min_date.date()} to {max_date.date()}")
            else:
                print("- Date range: N/A")
        
        print(f"- Unique MPs: {questions_df['asked_by'].nunique()}")
        print(f"- Unique ministers: {questions_df['minister'].nunique()}")
    else:
        print("No data was processed. Check your datasets folder.")
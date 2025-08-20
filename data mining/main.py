import pandas as pd
import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from feature_eng.pipeline import FeatureEngineeringPipeline
    from feature_eng.json_utils import JSONDataHandler
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def main():
    try:
        print("Starting parliamentary questions analysis...")
        
        # Initialize data handler
        data_handler = JSONDataHandler('datasets')
        
        # Load and combine datasets
        df = data_handler.load_and_combine_datasets()
        
        if df.empty:
            print("No data available for processing.")
            return
        
        print(f"Loaded {len(df)} records")
        print(f"Available columns: {list(df.columns)}")
        
        # Show sample data for debugging
        print(f"\nSample of raw data:")
        sample_cols = ['question_number', 'asked_by', 'minister', 'question_text']
        sample_cols = [col for col in sample_cols if col in df.columns]
        sample_data = df[sample_cols].head(5)
        
        for _, row in sample_data.iterrows():
            print(f"  Q{row.get('question_number', '')}: {row.get('asked_by', '')} -> {row.get('minister', '')}")
            if 'question_text' in row and pd.notna(row['question_text']):
                text_preview = row['question_text'][:100] + "..." if len(row['question_text']) > 100 else row['question_text']
                print(f"     Text: {text_preview}")
        
        # Detect and apply column mappings
        column_mapping = data_handler.detect_column_mapping(df)
        if column_mapping:
            print(f"Applying column mappings: {column_mapping}")
            df = df.rename(columns=column_mapping)
        
        # Check essential columns
        essential_columns = ['question_text', 'asked_by']
        missing_essential = [col for col in essential_columns if col not in df.columns]
        
        if missing_essential:
            print(f"Warning: Missing essential columns: {missing_essential}")
            print("Available columns:", list(df.columns))
            return
        
        # Initialize pipeline
        pipeline = FeatureEngineeringPipeline()
        
        # Process features
        print("Engineering features...")
        df_features = pipeline.engineer_features(df)
        
        # Show results
        pipeline.get_feature_summary(df_features)
        
        # Show detailed sample of processed data
        print(f"\nDetailed sample of processed data:")
        sample_cols = ['question_number', 'asked_by', 'minister', 'mp_gender', 'constituency']
        sample_cols = [col for col in sample_cols if col in df_features.columns]
        sample_data = df_features[sample_cols].head(10)
        
        for _, row in sample_data.iterrows():
            gender_symbol = "♂" if row.get('mp_gender') == 'Male' else "♀" if row.get('mp_gender') == 'Female' else "?"
            print(f"  Q{row.get('question_number', '')}: {gender_symbol} {row.get('asked_by', '')} [{row.get('constituency', '')}] -> {row.get('minister', '')}")
        
        # Save results
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, 'parliamentary_questions_with_features.csv')
        df_features.to_csv(output_path, index=False)
        print(f"\nResults saved to: {output_path}")
        
        # Show final statistics
        if 'mp_gender' in df_features.columns:
            gender_stats = df_features['mp_gender'].value_counts()
            print(f"\nFinal Gender Statistics:")
            for gender, count in gender_stats.items():
                print(f"  {gender}: {count}")
        
        if 'constituency' in df_features.columns:
            constituency_count = df_features['constituency'].nunique()
            print(f"Unique constituencies: {constituency_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
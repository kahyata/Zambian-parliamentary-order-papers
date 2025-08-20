import json
import os
import glob

def count_questions_in_folder(folder_path="datasets"):
    """
    Count questions in all JSON files in the specified folder
    
    Args:
        folder_path (str): Path to the folder containing JSON files
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist!")
        return
    
    # Get all JSON files in the folder
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return
    
    print(f"Found {len(json_files)} JSON files in '{folder_path}'")
    print("=" * 60)
    
    total_questions = 0
    files_with_questions = 0
    files_without_questions = 0
    file_stats = []
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            filename = os.path.basename(json_file)
            question_count = 0
            
            # Check if the file has questions
            if "questions" in data and isinstance(data["questions"], list):
                question_count = len(data["questions"])
                total_questions += question_count
                
                if question_count > 0:
                    files_with_questions += 1
                else:
                    files_without_questions += 1
            else:
                files_without_questions += 1
            
            # Get metadata for reporting
            metadata = data.get("metadata", {})
            title = metadata.get("title", "Unknown title")
            date = metadata.get("date", "Unknown date")
            
            file_stats.append({
                "filename": filename,
                "question_count": question_count,
                "title": title,
                "date": date
            })
            
            print(f"{filename}: {question_count} questions - {title}")
                
        except json.JSONDecodeError:
            print(f"✗ ERROR: {os.path.basename(json_file)} - Invalid JSON format")
            files_without_questions += 1
        except Exception as e:
            print(f"✗ ERROR: {os.path.basename(json_file)} - {e}")
            files_without_questions += 1
    
    # Print summary
    print("=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    print(f"Total files processed: {len(json_files)}")
    print(f"Files with questions: {files_with_questions}")
    print(f"Files without questions: {files_without_questions}")
    print(f"Total questions found: {total_questions}")
    
    # Show files with most questions
    if files_with_questions > 0:
        print("\nTOP 5 FILES WITH MOST QUESTIONS:")
        print("-" * 40)
        sorted_files = sorted(file_stats, key=lambda x: x["question_count"], reverse=True)
        for i, file_info in enumerate(sorted_files[:5]):
            if file_info["question_count"] > 0:
                print(f"{i+1}. {file_info['filename']}: {file_info['question_count']} questions")
                print(f"   Title: {file_info['title']}")
                print(f"   Date: {file_info['date']}")
                print()
    
    return total_questions, files_with_questions, files_without_questions

def get_detailed_question_stats(folder_path="datasets"):
    """
    Get detailed statistics about questions in the folder
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist!")
        return
    
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return
    
    total_questions = 0
    question_types = {}
    ministers = {}
    askers = {}
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if "questions" in data and isinstance(data["questions"], list):
                for question in data["questions"]:
                    total_questions += 1
                    
                    # Count question types by parts
                    part_count = len(question.get("parts", []))
                    question_types[part_count] = question_types.get(part_count, 0) + 1
                    
                    # Count ministers
                    minister = question.get("minister", "Unknown")
                    ministers[minister] = ministers.get(minister, 0) + 1
                    
                    # Count askers
                    asker = question.get("asked_by", "Unknown")
                    askers[asker] = askers.get(asker, 0) + 1
                    
        except:
            continue
    
    print("\nDETAILED QUESTION STATISTICS:")
    print("=" * 40)
    print(f"Total questions analyzed: {total_questions}")
    
    print("\nQUESTION TYPES (by number of parts):")
    print("-" * 35)
    for parts, count in sorted(question_types.items()):
        print(f"Questions with {parts} parts: {count}")
    
    print("\nTOP 10 MINISTERS ASKED:")
    print("-" * 25)
    sorted_ministers = sorted(ministers.items(), key=lambda x: x[1], reverse=True)
    for i, (minister, count) in enumerate(sorted_ministers[:10]):
        print(f"{i+1}. {minister}: {count} questions")
    
    print("\nTOP 10 QUESTION ASKERS:")
    print("-" * 25)
    sorted_askers = sorted(askers.items(), key=lambda x: x[1], reverse=True)
    for i, (asker, count) in enumerate(sorted_askers[:10]):
        print(f"{i+1}. {asker}: {count} questions")

def export_question_counts_to_csv(folder_path="datasets", output_file="question_counts.csv"):
    """
    Export question counts to a CSV file
    """
    import csv
    
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist!")
        return
    
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['filename', 'question_count', 'title', 'date', 'source_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                question_count = len(data.get("questions", []))
                metadata = data.get("metadata", {})
                
                writer.writerow({
                    'filename': os.path.basename(json_file),
                    'question_count': question_count,
                    'title': metadata.get("title", ""),
                    'date': metadata.get("date", ""),
                    'source_url': metadata.get("source_url", "")
                })
                
            except:
                continue
    
    print(f"Question counts exported to {output_file}")

if __name__ == "__main__":
    # Count questions in all files
    total, with_questions, without_questions = count_questions_in_folder()
    
    # Get detailed statistics
    if with_questions > 0:
        get_detailed_question_stats()
        
        # Export to CSV
        export_question_counts_to_csv()
        
        print(f"\nAnalysis complete! Found {total} questions across {with_questions} files.")
    else:
        print("\nNo questions found in any files.")
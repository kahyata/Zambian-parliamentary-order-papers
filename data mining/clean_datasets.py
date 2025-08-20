import os
import json
import glob

def auto_clean_json_files(folder_path="datasets"):
    """
    Automatically delete JSON files without questions (no confirmation)
    """
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist!")
        return
    
    json_files = glob.glob(os.path.join(folder_path, "*.json"))
    
    if not json_files:
        print(f"No JSON files found in '{folder_path}'")
        return
    
    deleted_count = 0
    kept_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if the file has questions
            has_questions = (
                "questions" in data and 
                isinstance(data["questions"], list) and 
                len(data["questions"]) > 0
            )
            
            if not has_questions:
                os.remove(json_file)
                print(f"Deleted: {os.path.basename(json_file)} - No questions")
                deleted_count += 1
            else:
                kept_count += 1
                
        except Exception as e:
            print(f"Error processing {os.path.basename(json_file)}: {e}")
    
    print(f"\nCleanup complete!")
    print(f"Files kept: {kept_count}")
    print(f"Files deleted: {deleted_count}")

# Run the automatic cleanup
auto_clean_json_files()
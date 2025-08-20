import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urljoin
from datetime import datetime
import time

BASE_URL = "https://www.parliament.gov.zm"

def ensure_datasets_folder():
    """Create datasets folder if it doesn't exist"""
    if not os.path.exists('datasets'):
        os.makedirs('datasets')

def extract_year_from_title(title):
    """Extract year from paper title using different patterns"""
    patterns = [
        r'\d{1,2}(?:st|nd|rd|th) [A-Za-z]+, (\d{4})',  # "1st August, 2025"
        r'\b(20\d{2})\b',                              # Just the year
        r'(\d{2}) [A-Za-z]+, 20(\d{2})',               # "1 August, 25"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, title)
        if match:
            year = match.group(1)
            if len(year) == 2:  # Handle "25" -> "2025"
                return f"20{year}"
            return year
    return None

def extract_parliament_questions(url):
    """
    Extracts parliamentary questions from Zambia National Assembly order papers
    with precise targeting of the content structure.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Fetch the page with error handling
        response = requests.get(url, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract metadata
        title = soup.find('h1', id='page-title').get_text(strip=True) if soup.find('h1', id='page-title') else None
        metadata = {
            "title": title,
            "source_url": url,
            "document_type": "Order Paper"
        }
        
        # Locate the exact content container
        content_div = soup.find('div', class_='field-name-body')
        if not content_div:
            raise ValueError("Could not find the main content div")
        
        # Extract all text and process line by line
        text_content = content_div.get_text('\n')
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        questions = []
        current_question = None
        in_questions_section = False
        current_section = None
        
        # Extract metadata from content
        for line in lines[:20]:  # Check first 20 lines for metadata
            if "NATIONAL ASSEMBLY OF ZAMBIA" in line:
                metadata["parliament"] = line
            elif "SESSION OF THE" in line and "ASSEMBLY" in line:
                metadata["session"] = line
            elif "ORDER PAPER" in line and ("MONDAY" in line or "TUESDAY" in line or "WEDNESDAY" in line or 
                                          "THURSDAY" in line or "FRIDAY" in line):
                metadata["date"] = line.replace("ORDER PAPER - ", "")
            elif "AT" in line and "HOURS" in line:
                metadata["time"] = line
        
        # Process all lines for questions
        for line in lines:
            # Detect sections
            if "QUESTIONS FOR ORAL ANSWER" in line:
                in_questions_section = True
                current_section = line
                continue
                
            if ("MOTIONS" in line or "ORDERS OF THE DAY" in line or "HIS HONOUR THE VICE PRESIDENT'S QUESTION TIME" in line) and in_questions_section:
                break
                
            if in_questions_section:
                # New question detection with pattern matching
                question_match = re.match(r'^(\d+)\s+(.+?)\s+-\s+to ask the (.+?):?$', line)
                if question_match:
                    if current_question:
                        questions.append(current_question)
                        
                    current_question = {
                        "question_number": question_match.group(1),
                        "asked_by": question_match.group(2).strip(),
                        "minister": question_match.group(3).strip(),
                        "section": current_section,
                        "parts": []
                    }
                # Question parts (a), (b) etc.
                elif current_question and re.match(r'^\([a-z]\)', line.lower()):
                    current_question["parts"].append(line)
                # Continuation of previous part
                elif current_question and current_question["parts"]:
                    current_question["parts"][-1] += " " + line
                # Continuation of question line (if no parts yet)
                elif current_question and not current_question["parts"]:
                    if "to ask the" not in line:  # Avoid adding duplicate question lines
                        current_question["question_text"] = current_question.get("question_text", "") + " " + line
        
        # Add the last question if exists
        if current_question:
            questions.append(current_question)
        
        # Clean up the questions - remove question_text field if it's not needed
        for question in questions:
            if "question_text" in question and not question["question_text"].strip():
                del question["question_text"]
        
        return {
            "metadata": metadata,
            "questions": questions,
            "question_count": len(questions),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "url": url
        }

def get_order_paper_urls_all_pages(base_url, target_year=2006):
    """Extract all order paper URLs from pages 0 to 17 until target year is reached"""
    all_paper_links = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Scrape from page 0 to page 17
    for page_num in range(0, 18):  # 0 to 17 inclusive
        # Construct URL for each page
        if page_num == 0:
            page_url = base_url
        else:
            page_url = f"{base_url}?page={page_num}"
        
        print(f"Scraping page {page_num + 1}/18: {page_url}")
        
        try:
            response = requests.get(page_url, headers=headers, verify=False, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            page_links = []
            earliest_year_on_page = None
            
            for link in soup.select('a[href^="/node/"]'):
                title = link.get_text(strip=True)
                
                # Skip if not an order paper
                if not ("order-paper" in title.lower() or re.search(r"\d{1,2}(st|nd|rd|th) [A-Za-z]+, \d{4}", title)):
                    continue
                    
                # Extract year from title
                year = extract_year_from_title(title)
                
                # Skip if year couldn't be determined
                if not year:
                    continue
                
                year_int = int(year)
                
                # Track the earliest year on this page
                if earliest_year_on_page is None or year_int < earliest_year_on_page:
                    earliest_year_on_page = year_int
                
                # Skip if year is before target year
                if year_int < target_year:
                    continue
                    
                full_url = urljoin(BASE_URL, link['href'])
                page_links.append({
                    "url": full_url,
                    "title": title,
                    "year": year
                })
            
            all_paper_links.extend(page_links)
            print(f"  Found {len(page_links)} relevant papers on page {page_num + 1}")
            
            # Early termination: if the earliest year on this page is before target year,
            # and we've already collected some papers, we can stop
            if earliest_year_on_page and earliest_year_on_page < target_year and all_paper_links:
                print(f"  Reached target year {target_year} (earliest on page: {earliest_year_on_page}). Stopping pagination.")
                break
            
            # Be respectful to the server
            time.sleep(1)
            
        except Exception as e:
            print(f"Error processing page {page_num + 1}: {str(e)}")
            continue
    
    # Sort by year (newest first)
    all_paper_links.sort(key=lambda x: int(x['year']), reverse=True)
    
    print(f"\nTotal papers found: {len(all_paper_links)}")
    if all_paper_links:
        years = [int(paper['year']) for paper in all_paper_links]
        print(f"Year range: {min(years)} - {max(years)}")
    
    return all_paper_links

def process_all_papers(target_year=2006):
    """Process all order papers and save to datasets folder"""
    ensure_datasets_folder()
    list_url = "https://www.parliament.gov.zm/publications/order-paper-date"
    papers = get_order_paper_urls_all_pages(list_url, target_year)
    
    if not papers:
        print("No papers found matching the criteria")
        return
    
    all_results = []
    successful_count = 0
    
    for i, paper in enumerate(papers, 1):
        print(f"Processing {i}/{len(papers)}: {paper['title']} (Year: {paper['year']})")
        result = extract_parliament_questions(paper['url'])
        
        if result["status"] == "success":
            # Create filename with date if available, otherwise use title
            date_str = result['metadata'].get('date', '').replace(',', '').replace(' ', '_')
            if not date_str:
                # Fallback to using title with year
                safe_title = re.sub(r'[^\w\s-]', '', paper['title'])
                date_str = f"{safe_title.replace(' ', '_')}_{paper['year']}"
            
            filename = f"datasets/paper_{date_str}.json"
            
            # Ensure unique filename
            counter = 1
            original_filename = filename
            while os.path.exists(filename):
                base, ext = os.path.splitext(original_filename)
                filename = f"{base}_{counter}{ext}"
                counter += 1
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            all_results.append(result)
            successful_count += 1
            print(f"  ✓ Saved {len(result['questions'])} questions to {filename}")
        else:
            print(f"  ✗ Failed: {result['message']}")
        
        # Add delay between requests to be respectful
        time.sleep(2)
    
    # Save combined results
    combined_filename = 'datasets/all_parliament_questions.json'
    with open(combined_filename, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    # Generate summary statistics
    total_questions = sum(len(result['questions']) for result in all_results)
    
    print(f"\n{'='*60}")
    print(f"SCRAPING COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully processed: {successful_count}/{len(papers)} papers")
    print(f"Total questions extracted: {total_questions}")
    print(f"Combined results saved to: {combined_filename}")
    
    if all_results:
        years = []
        for result in all_results:
            if result['metadata'].get('date'):
                year_match = re.search(r'\d{4}', result['metadata']['date'])
                if year_match:
                    years.append(int(year_match.group()))
        
        if years:
            print(f"Date range covered: {min(years)} - {max(years)}")
    
    print(f"Individual papers saved in: ./datasets/ folder")

if __name__ == "__main__":
    # Set target_year to 2006 to get papers from 2006 to present
    process_all_papers(target_year=2006)
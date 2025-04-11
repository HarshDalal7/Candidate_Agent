import pandas as pd
import sqlite3

# Load the job descriptions CSV file with encoding specified
file_path = r"C:\Users\dalal\Downloads\DatasetAccenture\Dataset\[Usecase 5] AI-Powered Job Application Screening System\job_description.csv"
jd_data = pd.read_csv(file_path, encoding='ISO-8859-1')  # Fix for encoding issue

# Connect to the SQLite database
conn = sqlite3.connect('recruitment.db')
cursor = conn.cursor()

# Iterate through the job descriptions and store them in the database
for index, row in jd_data.iterrows():
    job_title = row['Job Title']
    job_description = row['Job Description']
    
    # Simplified summary (for demonstration purposes)
    summary = job_description[:150]  # Extract first 150 characters as summary
    
    # Insert into the database
    cursor.execute('''
    INSERT INTO job_descriptions (title, description, summary)
    VALUES (?, ?, ?)
    ''', (job_title, job_description, summary))

# Commit changes and close connection
conn.commit()
conn.close()

print("Job descriptions have been successfully stored in the database.")


import os
import sqlite3
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF files"""
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text

def process_cvs(cv_folder):
    """Process all CVs in a folder and store in database"""
    # Verify folder exists
    if not os.path.exists(cv_folder):
        raise FileNotFoundError(f"CV folder not found: {cv_folder}")
    
    conn = sqlite3.connect('recruitment.db')
    
    for filename in os.listdir(cv_folder):
        if filename.endswith('.pdf'):
            file_path = os.path.join(cv_folder, filename)
            
            # Extract candidate name from filename
            base_name = os.path.splitext(filename)[0]  # Correct filename parsing
            candidate_name = base_name.replace('_', ' ')
            candidate_email = f"{base_name.lower().replace(' ', '.')}@example.com"
            
            # Extract text from PDF
            try:
                cv_text = extract_text_from_pdf(file_path)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue
            
            # Insert into database
            conn.execute('''
            INSERT INTO candidates (name, email, cv_text, extracted_data)
            VALUES (?, ?, ?, ?)
            ''', (candidate_name, candidate_email, cv_text, "{}"))
    
    conn.commit()
    conn.close()

# Handle special characters in path
cv_folder = r"C:\Users\dalal\Downloads\DatasetAccenture\Dataset\[Usecase 5] AI-Powered Job Application Screening System\CVs1"

# Alternative path format if needed
# cv_folder = "C:/Users/dalal/Downloads/DatasetAccenture/Dataset/[Usecase 5] AI-Powered Job Application Screening System/CVs1"

process_cvs(cv_folder)
print("CV processing completed successfully!")

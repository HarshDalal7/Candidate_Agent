import os
import json
import sqlite3
import time
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key from environment and configure the API
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = input("Enter your Google API Key: ")
genai.configure(api_key=GOOGLE_API_KEY)

# Set the model identifier to the free 'gemma-3-27b-it' model
MODEL_NAME = "models/gemma-3-27b-it"
model = genai.GenerativeModel(MODEL_NAME)

def get_tied_candidate_details(job_id):
    """
    Retrieve details for all candidates tied at the maximum matching score for the given job_id.
    Returns a list of dictionaries containing candidate ID, name, score, reasoning, and cv_text.
    """
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT MAX(score) FROM matches WHERE jd_id = ?", (job_id,))
    max_score_row = cursor.fetchone()
    if max_score_row is None or max_score_row[0] is None:
        conn.close()
        return []
    max_score = max_score_row[0]
    
    query = """
    SELECT m.candidate_id, c.name, m.score, m.reasoning, c.cv_text
    FROM matches m
    JOIN candidates c ON m.candidate_id = c.id
    WHERE m.jd_id = ? AND m.score = ?
    ORDER BY c.id ASC
    """
    cursor.execute(query, (job_id, max_score))
    results = cursor.fetchall()
    conn.close()
    
    candidate_details = []
    for candidate_id, name, score, reasoning, cv_text in results:
        candidate_details.append({
            "id": candidate_id,
            "name": name,
            "score": score,
            "reasoning": reasoning,
            "cv_text": cv_text
        })
    return candidate_details

def resolve_tie_for_job(job_description, candidate_details, max_retries=3):
    """
    Given a job description and candidate details (list of dictionaries),
    generate an LLM prompt to rank the candidates by overall suitability and explain the top candidate.
    The function returns a JSON object with:
      - "ranking": a JSON array of candidate IDs in descending order (best candidate first)
      - "explanation": a brief explanation for why the top candidate is the best.
    """
    # Build candidate details block
    candidate_info_str = ""
    for candidate in candidate_details:
        # Prepare a short CV snippet (first 150 characters)
        snippet = candidate['cv_text'][:150].replace('\n', ' ').strip()
        candidate_info_str += (f"Candidate {candidate['id']}: {candidate['name']}, "
                               f"Matching Score: {candidate['score']}%, "
                               f"Explanation: \"{candidate['reasoning']}\". "
                               f"CV snippet: \"{snippet}\"\n")
    
    prompt = f"""
You are a seasoned HR expert responsible for selecting the best candidate for a critical Software Engineer position.
Several candidates have tied with the highest matching score according to our AI matching system.
Below are the details for the tied candidates:

{candidate_info_str}

Based on the above information, evaluate each candidate's technical skills, relevant experience, certifications, and any noted gaps.
Rank these candidates in order of overall suitability for the Software Engineer role, from best to worst.
Also, provide a concise explanation (up to 150 words) as to why the top candidate is the best.
Return only a JSON object with two keys:
 - "ranking": a JSON array of candidate IDs in descending order (best candidate first)
 - "explanation": a brief explanation for the top candidate.

For example:
{{
  "ranking": [27, 23, ...],
  "explanation": "Candidate 27 demonstrated superior technical expertise and hands-on experience..."
}}
"""
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            # Remove markdown formatting if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Attempt {attempt} failed with error: {e}")
            if attempt < max_retries:
                sleep_time = 2 ** attempt  # Exponential backoff
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    print("Max retries reached. Returning an empty result.")
    return {}

if __name__ == "__main__":
    job_id = 1  # For Job ID 1
    # Retrieve the job description for Job ID 1 from the database.
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM job_descriptions WHERE id = ?", (job_id,))
    job_description_row = cursor.fetchone()
    conn.close()
    if not job_description_row:
        print("No job description found for Job ID", job_id)
        exit()
    job_description = job_description_row[0]
    
    # Retrieve tied candidate details for Job ID 1
    candidate_details = get_tied_candidate_details(job_id)
    if not candidate_details:
        print("No tied candidate details found for Job ID", job_id)
        exit()
    
    print("Tied candidate details for Job ID", job_id)
    print(json.dumps(candidate_details, indent=2))
    
    # Resolve tie using the LLM prompt
    tie_break_result = resolve_tie_for_job(job_description, candidate_details)
    print("\nTie-break result for Job ID", job_id, ":\n", json.dumps(tie_break_result, indent=2))
    
    # Store the result in a JSON file (or this could be stored in your DB if desired)
    output = {
        "job_id": job_id,
        "job_description": job_description,
        "tied_candidates": candidate_details,
        "tie_break_result": tie_break_result
    }
    with open(f'tie_break_result_job_{job_id}.json', 'w') as f:
        json.dump(output, f, indent=2)
    print(f"Tie-break result saved to tie_break_result_job_{job_id}.json")

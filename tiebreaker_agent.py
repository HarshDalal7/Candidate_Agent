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

# Set the model identifier (adjust if needed)
MODEL_NAME = "models/gemma-3-27b-it"
model = genai.GenerativeModel(MODEL_NAME)

def get_tied_candidate_details(job_id):
    """
    Retrieve details for all candidates tied at the maximum matching score for the given job_id.
    Returns a list of dictionaries containing candidate ID, name, score, reasoning, and cv_text.
    """
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Get maximum matching score for the job
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
    generate an LLM prompt to rank tied candidates and provide an explanation for the top candidate.
    Returns a JSON object with keys:
      - "ranking": a JSON array of candidate IDs in descending order (best candidate first)
      - "explanation": a concise justification for why the top candidate is most suitable.
    """
    # Build the candidate details block
    candidate_info_str = ""
    for candidate in candidate_details:
        snippet = candidate['cv_text'][:150].replace('\n', ' ').strip()
        candidate_info_str += (
            f"Candidate {candidate['id']}: {candidate['name']}.\n"
            f"Matching Score: {candidate['score']}%.\n"
            f"Matching Explanation: {candidate['reasoning']}.\n"
            f"CV Snippet: {snippet}\n\n"
        )
    
    # Improved prompt instructing the LLM as a seasoned HR executive.
    prompt = f"""
You are a highly experienced HR executive tasked with selecting the most suitable candidate for a critical role.
Our advanced AI matching system has identified a group of candidates who tied with the highest matching score for this job.
Below are the candidate profiles, with each profile providing:
- Candidate ID and Name.
- Matching Score (as a percentage).
- AI-generated Matching Explanation summarizing technical proficiency, work experience, certifications, educational background, and identified gaps.
- A brief CV snippet.

Candidate Details:
{candidate_info_str}

Your task:
1. Evaluate all candidate profiles by considering both the quantitative matching scores and the qualitative insights.
2. Focus on key criteria such as technical expertise, depth of relevant experience, industry certifications, and overall alignment with the job requirements.
3. Rank the candidates in order of overall suitability for the role, with the most qualified candidate at the top.
4. Provide a succinct explanation (up to 150 words) justifying why the top-ranked candidate is the best choice.

Return your answer as a JSON object with two keys:
- "ranking": a JSON array of candidate IDs in descending order (best candidate first),
- "explanation": a concise justification for why the top candidate is most suitable.

For example:
{{
  "ranking": [27, 23, 45],
  "explanation": "Candidate 27 stands out with exceptional technical expertise, extensive relevant experience, and strong certifications, making them the ideal choice for the role."
}}

Do not include any additional text.
"""
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            result = json.loads(response_text)
            return result
        except Exception as e:
            print(f"Attempt {attempt} for tie resolution of job failed with error: {e}")
            if attempt < max_retries:
                sleep_time = 2 ** attempt
                print(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
    print("Max retries reached for tie resolution. Returning empty result.")
    return {}

def get_all_job_ids():
    """Retrieve all job IDs from the job_descriptions table."""
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM job_descriptions")
    job_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return job_ids

def process_specific_jobs(job_ids_to_process):
    """
    Re-run tie resolution for specific job IDs.
    Saves the result for each job in a separate JSON file.
    """
    overall_tie_break_results = {}

    for job_id in job_ids_to_process:
        print(f"[RE-RUN] Processing tie resolution for Job ID {job_id}...")

        # Retrieve job description for the job
        conn = sqlite3.connect('recruitment.db')
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM job_descriptions WHERE id = ?", (job_id,))
        job_description_row = cursor.fetchone()
        conn.close()
        
        if not job_description_row:
            print(f"No job description found for Job ID {job_id}. Skipping.")
            continue
        
        job_description = job_description_row[0]
        candidate_details = get_tied_candidate_details(job_id)
        
        if not candidate_details:
            print(f"No tied candidates found for Job ID {job_id}. Skipping.")
            continue

        print(f"Tied candidates found: {len(candidate_details)}")
        tie_break_result = resolve_tie_for_job(job_description, candidate_details)
        
        overall_tie_break_results[job_id] = {
            "job_description": job_description,
            "tied_candidates": candidate_details,
            "tie_break_result": tie_break_result
        }

        output_filename = f"final_tie_break_job_{job_id}.json"
        with open(output_filename, 'w') as f:
            json.dump(overall_tie_break_results[job_id], f, indent=2)
        print(f"[RE-RUN] Saved updated result for Job ID {job_id} to {output_filename}\n")

    return overall_tie_break_results

if __name__ == "__main__":
    # Re-run tie resolution for Job IDs that need corrections: 3, 4, 5, 13, 16
    jobs_to_fix = [13]
    results = process_specific_jobs(jobs_to_fix)
    print("Reprocessing complete for specified jobs.")

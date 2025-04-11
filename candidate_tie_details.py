import sqlite3
import json

def get_candidate_details_for_all_jobs():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    # Get all job ids from job_descriptions table
    cursor.execute("SELECT id FROM job_descriptions")
    job_ids = cursor.fetchall()
    
    result = {}
    
    for (job_id,) in job_ids:
        # Get maximum matching score for this job id from the matches table
        cursor.execute("SELECT MAX(score) FROM matches WHERE jd_id = ?", (job_id,))
        max_score_row = cursor.fetchone()
        if max_score_row is None or max_score_row[0] is None:
            # No matching records for this job id; store an empty list.
            result[job_id] = []
            continue
            
        max_score = max_score_row[0]
        
        # Retrieve candidate details for those tied at the maximum score,
        # by joining the matches and candidates table.
        query = """
        SELECT m.candidate_id, c.name, m.score, m.reasoning, c.cv_text
        FROM matches m
        JOIN candidates c ON m.candidate_id = c.id
        WHERE m.jd_id = ? AND m.score = ?
        ORDER BY c.id ASC
        """
        cursor.execute(query, (job_id, max_score))
        candidate_rows = cursor.fetchall()
        
        candidate_details = []
        for candidate_id, name, score, reasoning, cv_text in candidate_rows:
            candidate_details.append({
                "id": candidate_id,
                "name": name,
                "score": score,
                "reasoning": reasoning,
                "cv_text": cv_text
            })
        result[job_id] = candidate_details
    
    conn.close()
    return result

if __name__ == "__main__":
    candidate_details_all = get_candidate_details_for_all_jobs()
    
    # Print the candidate details for each job as JSON for easy copy/paste into your tie-breaker prompt.
    for job_id, details in candidate_details_all.items():
        print(f"Job ID {job_id} Tied Candidate Details:")
        print(json.dumps(details, indent=2))
        print("\n" + "="*80 + "\n")

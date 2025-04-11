import sqlite3

def get_tie_resolution_summary():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    
    query = """
    WITH max_scores AS (
      SELECT jd_id, MAX(score) AS max_score 
      FROM matches 
      GROUP BY jd_id
    )
    SELECT m.jd_id, ms.max_score, COUNT(*) AS candidate_count
    FROM matches m
    JOIN max_scores ms 
      ON m.jd_id = ms.jd_id AND m.score = ms.max_score
    GROUP BY m.jd_id, ms.max_score;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    summary = get_tie_resolution_summary()
    for job_id, max_score, candidate_count in summary:
        print(f"Job ID {job_id}: Highest Matching Score = {max_score}, Number of Candidates = {candidate_count}")

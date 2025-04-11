import os
import json
import csv

# Input/Output file paths (adjust if needed)
FINAL_JSON = "final_tie_break_all_jobs.json"
OUTPUT_CSV = "master_csv.csv"

def generate_csv_from_json(json_file=FINAL_JSON, output_csv=OUTPUT_CSV):
    if not os.path.exists(json_file):
        print(f"File '{json_file}' not found!")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    rows = []
    for job_id, job_data in data.items():
        # Retrieve the tie-break result object
        tie_break_result = job_data.get("tie_break_result", {})
        ranking = tie_break_result.get("ranking", [])
        reason = tie_break_result.get("explanation", "")
        
        # If there is a ranking, take the first candidate as the top candidate
        if ranking:
            top_candidate = ranking[0]
        else:
            top_candidate = "None"
        
        rows.append({
            "Job": job_id,
            "Top Candidate": top_candidate,
            "Reason": reason
        })
    
    # Write rows to CSV with columns: Job, Top Candidate, Reason
    fieldnames = ["Job", "Top Candidate", "Reason"]
    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"CSV file '{output_csv}' created successfully with {len(rows)} entries.")

if __name__ == "__main__":
    generate_csv_from_json()

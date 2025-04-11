import sqlite3

def init_db():
    # Connect to SQLite database (creates file if it doesn't exist)
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()

    # Create Job Descriptions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS job_descriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        summary TEXT
    )
    ''')

    # Create Candidates table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        cv_text TEXT NOT NULL,
        extracted_data TEXT
    )
    ''')

    # Optional: Drop the old matches table if it exists so the new schema takes effect
    cursor.execute("DROP TABLE IF EXISTS matches")

    # Create Matches table with the reasoning column
    cursor.execute('''
    CREATE TABLE matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jd_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        score REAL NOT NULL,
        shortlisted INTEGER DEFAULT 0,
        reasoning TEXT,
        FOREIGN KEY (jd_id) REFERENCES job_descriptions (id),
        FOREIGN KEY (candidate_id) REFERENCES candidates (id)
    )
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

# Initialize the database
if __name__ == "__main__":
    init_db()

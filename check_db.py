"""Check database contents."""

import sqlite3
from src.core.human_agents_db import HumanAgentsDatabase

def check_database():
    """Check the actual database contents."""
    db_manager = HumanAgentsDatabase()
    
    with db_manager.get_connection() as conn:
        cursor = conn.execute("SELECT id, name, specializations FROM human_agents LIMIT 5")
        rows = cursor.fetchall()
        
        print("Database contents:")
        for row in rows:
            print(f"  ID: {row['id']}")
            print(f"  Name: {row['name']}")
            print(f"  Specializations: {row['specializations']}")
            print()

if __name__ == "__main__":
    check_database()
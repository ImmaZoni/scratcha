import sqlite3
from datetime import datetime

def inspect_database():
    """Quick database inspection tool"""
    conn = sqlite3.connect('scratcher_data.db')
    
    try:
        # Get latest scrape time
        cursor = conn.execute('''
            SELECT MAX(scrape_time) as last_scrape,
                   COUNT(*) as total_records
            FROM scraper_data
        ''')
        last_scrape, record_count = cursor.fetchone()
        print(f"Last Scrape: {last_scrape or 'Never'}")
        print(f"Total Records: {record_count}\n")

        # Show table structure
        print("Table Structure:")
        cursor = conn.execute("PRAGMA table_info(scraper_data)")
        for column in cursor.fetchall():
            print(f"- {column[1]} ({column[2]})")
        
        # Show sample data
        if record_count > 0:
            print("\nRecent Entries (max 5):")
            cursor = conn.execute('''
                SELECT name, cost, odds, prize_amount, scrape_time 
                FROM scraper_data 
                ORDER BY scrape_time DESC 
                LIMIT 5
            ''')
            for row in cursor:
                print(f"\nGame: {row[0]}")
                print(f"Cost: ${row[1]:.2f}")
                print(f"Odds: 1 in {row[2]:.2f}")
                print(f"Prize: ${row[3]:,.2f}")
                print(f"Scraped: {row[4]}")
                
    except sqlite3.OperationalError as e:
        print(f"Database error: {str(e)}")
        print("Maybe the tables haven't been created yet?")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Scratcher Database Inspector\n" + "="*30)
    inspect_database()

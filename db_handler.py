import sqlite3
from contextlib import closing
from datetime import datetime

def init_db():
    """Initialize database and create tables with new schema"""
    with closing(sqlite3.connect('scratcher_data.db')) as conn:
        # Create analyzed results table (unchanged)
        conn.execute('''CREATE TABLE IF NOT EXISTS scratchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            remaining_prizes INTEGER,
            current_odds REAL,
            prize_pool REAL,
            ticket_cost REAL,
            value_retention REAL,
            UNIQUE(name, timestamp)
        )''')
        
        # Create new scraper raw data table with 20 prize tiers and image_url
        prize_columns = ',\n'.join(
            f'''prize{i}_amount REAL,
               prize{i}_total INTEGER,
               prize{i}_remaining INTEGER'''
            for i in range(1, 21)
        )
        
        create_table_sql = f'''CREATE TABLE IF NOT EXISTS scraper_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cost REAL NOT NULL,
            odds REAL NOT NULL,
            image_url TEXT,
            {prize_columns},
            scrape_time DATETIME NOT NULL,
            UNIQUE(name, scrape_time)
        )'''
        
        conn.execute(create_table_sql)
        conn.commit()

def store_scraper_data(data):
    """Store raw scraper data in new database structure"""
    try:
        with closing(sqlite3.connect('scratcher_data.db')) as conn:
            # Begin with the basic columns: add image_url here.
            columns = ['name', 'cost', 'odds', 'image_url']
            values = [data['name'], data['cost'], data['odds'], data['image_url']]
            
            # Sort prize tiers by amount descending.
            prize_tiers = sorted(zip(
                data['prize_amounts'], 
                data['total_prizes'], 
                data['remaining_prizes']
            ), reverse=True)
            
            # Add however many prize tiers this game has (up to 20).
            for i, (amount, total, remaining) in enumerate(prize_tiers[:20], 1):
                columns.extend([
                    f'prize{i}_amount',
                    f'prize{i}_total',
                    f'prize{i}_remaining'
                ])
                values.extend([amount, total, remaining])
            
            # Fill remaining prize tier columns with NULL.
            for i in range(len(prize_tiers) + 1, 21):
                columns.extend([
                    f'prize{i}_amount',
                    f'prize{i}_total',
                    f'prize{i}_remaining'
                ])
                values.extend([None, None, None])
            
            # Append the scrape_time column (this remains as the final column).
            columns.append('scrape_time')
            values.append(data['scrape_time'])
            
            # Build dynamic SQL query.
            placeholders = ','.join(['?' for _ in values])
            columns_str = ','.join(columns)
            
            query = f'''INSERT OR REPLACE INTO scraper_data 
                ({columns_str}) VALUES ({placeholders})'''
            
            conn.execute(query, values)
            conn.commit()
            print(f"Stored {len(prize_tiers)} prize tiers for {data['name']}")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        print(f"Failed query: {query}")
        print(f"Values: {values}")
    except Exception as e:
        print(f"Error storing data: {e}")

def store_analysis_data(data):
    """Store analysis results in the database"""
    try:
        with closing(sqlite3.connect('scratcher_data.db')) as conn:
            conn.execute('''INSERT INTO scratchers 
                (name, timestamp, remaining_prizes, current_odds, 
                 prize_pool, ticket_cost, value_retention)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (data['name'], 
                 datetime.utcnow().isoformat(),
                 data['remaining_winning_tickets'],
                 data['current_odds'],
                 data['prize_pool_remaining'],
                 data['ticket_cost'],
                 data['value_retention']))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error storing data: {e}")
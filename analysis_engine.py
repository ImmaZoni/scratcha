import sqlite3
import json
from datetime import datetime
import os
import pandas as pd
from db_handler import init_db

def calculate_ev(group):
    """Calculate expected value for a game"""
    try:
        ticket_cost = float(group["cost"].iloc[0])
        posted_odds = float(group["odds"].iloc[0])
        
        # Core calculations for EV
        total_winning = group["total_prizes"].sum()
        remaining_winning = group["remaining_prizes"].sum()
        
        # If no remaining prizes, EV is negative ticket cost
        if remaining_winning == 0:
            return -ticket_cost
            
        # Calculate current total tickets based on odds
        current_total = (total_winning * posted_odds) - (total_winning - remaining_winning)
        
        # Calculate EV using prize amounts and remaining prizes
        prize_values = group["prize_amount"].values
        remaining = group["remaining_prizes"].values
        total_ev = sum(p * r / current_total for p, r in zip(prize_values, remaining))
        net_ev = total_ev - ticket_cost
        
        return float(net_ev)
    except Exception as e:
        print(f"Error calculating EV: {str(e)}")
        return -ticket_cost  # Return negative ticket cost as fallback

def analyze_scratchers(sort_mode=1, big_win_threshold=None):
    """Core analysis function reading from database"""
    conn = sqlite3.connect('scratcher_data.db')
    
    try:
        # First, get all unique games with their latest scrape times
        latest_games_query = '''
            SELECT name, MAX(scrape_time) as latest_time
            FROM scraper_data
            GROUP BY name
        '''
        latest_games = pd.read_sql(latest_games_query, conn)
        print(f"\nFound {len(latest_games)} games with their latest scrape times")
        
        # Process each game using its own latest scrape time
        results = []
        for _, game_row in latest_games.iterrows():
            try:
                game_name = game_row['name']
                game_scrape_time = game_row['latest_time']
                
                print(f"\nProcessing game: {game_name}")
                print(f"Latest scrape time for this game: {game_scrape_time}")
                
                # Get all game data including prize tiers
                game_query = '''
                    SELECT *
                    FROM scraper_data 
                    WHERE name = ? AND scrape_time = ?
                '''
                game_data = pd.read_sql(game_query, conn, params=(game_name, game_scrape_time))
                
                if game_data.empty:
                    print(f"No data found for game: {game_name}")
                    continue
                
                # Extract prize tiers
                prize_tiers = get_prize_tiers(game_data.iloc[0])
                
                print(f"Prize tiers found: {len(prize_tiers)}")
                print(f"Cost: ${game_data['cost'].iloc[0]}")
                print(f"Odds: {game_data['odds'].iloc[0]}")
                
                # Calculate game metrics
                total_remaining = sum(tier['remaining'] for tier in prize_tiers)
                total_prizes = sum(tier['total'] for tier in prize_tiers)
                prize_pool = sum(tier['amount'] * tier['remaining'] for tier in prize_tiers)
                
                game_totals = calculate_game_totals(prize_tiers, float(game_data['odds'].iloc[0]))
                
                analysis = {
                    'name': game_name,
                    'cost': float(game_data['cost'].iloc[0]),
                    'current_odds': float(game_data['odds'].iloc[0]),
                    'jackpot': float(max(tier['amount'] for tier in prize_tiers)),
                    'prize_pool_remaining': float(prize_pool),
                    'net_ev': calculate_ev_new(
                        game_data['cost'].iloc[0],
                        game_data['odds'].iloc[0],
                        prize_tiers
                    ),
                    'ticket_data': {
                        'total_tickets': game_totals['total_tickets'],
                        'remaining_tickets': game_totals['remaining_tickets'],
                        'percent_remaining': game_totals['percent_remaining'],
                        'total_winning': game_totals['total_winning'],
                        'remaining_winning': game_totals['remaining_winning']
                    },
                    'prize_tiers': {
                        str(tier['amount']): {
                            'percentage': (tier['remaining'] / game_totals['remaining_winning']) * 100,
                            'remaining': int(tier['remaining']),
                            'total': int(tier['total']),
                            'claimed': int(tier['total'] - tier['remaining'])
                        }
                        for tier in prize_tiers
                        if game_totals['remaining_winning'] > 0
                    },
                    'image_url': game_data['image_url'].iloc[0]
                }
                
                results.append(analysis)
                print(f"Successfully processed game: {game_name}")
                print(f"Prize tiers: {len(analysis['prize_tiers'])}")
                print(f"Jackpot: ${analysis['jackpot']}")
                
            except Exception as e:
                print(f"Error processing game {game_name}: {str(e)}")
                continue
        
        print(f"\nSuccessfully analyzed {len(results)} games")
        return results
        
    except Exception as e:
        print(f"Database error: {str(e)}")
        return []
    finally:
        conn.close()

def calculate_ev_new(cost, odds, prize_tiers):
    """Calculate expected value with new prize tier structure"""
    try:
        cost = float(cost)
        odds = float(odds)
        
        game_totals = calculate_game_totals(prize_tiers, odds)
        
        if game_totals['remaining_winning'] == 0:
            return -cost
            
        if game_totals['remaining_tickets'] <= 0:
            return -cost
            
        # Calculate EV using remaining tickets as denominator
        total_ev = sum(
            tier['amount'] * tier['remaining'] / game_totals['remaining_tickets']
            for tier in prize_tiers
        )
        
        return float(total_ev - cost)
        
    except Exception as e:
        print(f"Error calculating EV: {str(e)}")
        return -cost

def calculate_prize_tiers(group, remaining_winning):
    """Calculate prize tier odds"""
    if remaining_winning == 0:
        return {}
    return {
        str(row["prize_amount"]): (row["remaining_prizes"] / remaining_winning) * 100
        for _, row in group.iterrows()
    }

def get_prize_tiers(game_data):
    """Extract prize tiers from game data, ignoring NULL values"""
    tiers = []
    for i in range(1, 21):
        amount = game_data[f'prize{i}_amount']
        total = game_data[f'prize{i}_total']
        remaining = game_data[f'prize{i}_remaining']
        
        # Only include non-NULL tiers
        if amount is not None and total is not None and remaining is not None:
            tiers.append({
                'amount': amount,
                'total': total,
                'remaining': remaining
            })
    
    return tiers

def calculate_game_totals(prize_tiers, odds):
    """Calculate total and remaining ticket counts"""
    total_winning = sum(tier['total'] for tier in prize_tiers)
    remaining_winning = sum(tier['remaining'] for tier in prize_tiers)
    
    # Total tickets = total winning tickets * odds
    total_tickets = int(float(total_winning * odds))
    claimed_winning = total_winning - remaining_winning
    
    # Estimate remaining tickets using same proportion
    remaining_tickets = int(float((remaining_winning / total_winning) * total_tickets))
    
    return {
        'total_tickets': int(total_tickets),
        'remaining_tickets': int(remaining_tickets),
        'total_winning': int(total_winning),
        'remaining_winning': int(remaining_winning),
        'claimed_winning': int(claimed_winning),
        'percent_remaining': (remaining_tickets / total_tickets) * 100 if total_tickets > 0 else 0
    }

def generate_website_data():
    """Generate all website data files"""
    try:
        os.makedirs('public/web_data', exist_ok=True)
        
        # Run analysis and get results directly as list
        print("\nStarting analysis...")
        current_data = analyze_scratchers()
        
        if not current_data:
            print("Warning: No games were analyzed!")
            return
        
        # Debug output for data validation
        print("\nValidating analysis results:")
        for game in current_data:
            print(f"Game: {game['name']}")
            print(f"Cost: ${game['cost']}")
            print(f"Odds: 1 in {game['current_odds']}")
            print(f"Prize tiers: {len(game['prize_tiers'])}")
            print("---")
        
        # Save current analysis
        with open('public/web_data/current_analysis.json', 'w') as f:
            json.dump(current_data, f, indent=2)
            print(f"\nWrote {len(current_data)} games to current_analysis.json")
        
        # Generate historical data
        conn = sqlite3.connect('scratcher_data.db')
        historical_data = {}
        
        print("\nGenerating historical data...")
        for game in current_data:
            game_name = game['name']
            history = pd.read_sql('''
                SELECT 
                    timestamp as date,
                    remaining_prizes,
                    prize_pool as prize_pool_remaining
                FROM scratchers 
                WHERE name = ? 
                ORDER BY timestamp
            ''', conn, params=(game_name,))
            historical_data[game_name] = history.to_dict('records')
            print(f"Added historical data for {game_name}: {len(history)} records")
        
        with open('public/web_data/historical.json', 'w') as f:
            json.dump(historical_data, f, indent=2)
            print(f"\nWrote historical data for {len(historical_data)} games")
        
        # Generate sitemap
        sitemap = {
            'last_updated': datetime.utcnow().isoformat(),
            'games': [game['name'] for game in current_data]
        }
        
        with open('public/web_data/sitemap.json', 'w') as f:
            json.dump(sitemap, f, indent=2)
            print("\nGenerated sitemap.json")
        
        print("\nWebsite data generation completed successfully")
        
    except Exception as e:
        print(f"Error generating website data: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    generate_website_data() 
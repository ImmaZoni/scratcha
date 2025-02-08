from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import re
from db_handler import init_db, store_scraper_data
from datetime import datetime
import os
import argparse  # New import for command-line argument parsing
from webdriver_manager.chrome import ChromeDriverManager, ChromeType
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeType
import platform
import subprocess
from selenium.webdriver.chrome.options import Options

def wait_and_get_element(wait, by, selector, error_msg=""):
    """Helper function to wait for and get an element with better error handling"""
    try:
        return wait.until(EC.presence_of_element_located((by, selector)))
    except TimeoutException:
        print(f"Timeout waiting for element: {error_msg}")
        print(f"Selector used: {selector}")
        raise

def get_game_urls(driver, wait, base_url="https://azplayersclub.com/games/types/1", max_page=None):
    """First phase: Collect all active game URLs from the paginated list.
       If max_page is provided, only pages through that number are scraped.
    """
    game_urls = set()
    current_page = 1
    
    while True:
        print(f"\nProcessing page {current_page}")
        
        # Load the games list page (only for first page)
        if current_page == 1:
            driver.get(base_url)
        
        # Wait for page to fully load
        time.sleep(3)
        
        try:
            # Wait for page to load and cards to be present
            wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class, 'MuiCard-root')]"
                ))
            )
            time.sleep(2)  # Extra wait for cards to settle

            # Find all active game cards and store their indices
            active_indices = []
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiCard-root')]")
            
            for idx, card in enumerate(cards):
                try:
                    # Check if card has blue banner
                    card.find_element(
                        By.XPATH,
                        ".//div[contains(@style, 'border-color: rgb(54, 177, 230)')]"
                    )
                    active_indices.append(idx)
                except NoSuchElementException:
                    continue

            if not active_indices:
                print("No active games found on this page")
                break

            # Process each active card by index
            found_new_games = False
            for idx in active_indices:
                try:
                    # Get fresh card element
                    cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'MuiCard-root')]")
                    card = cards[idx]
                    
                    # Get game name
                    game_name = card.find_element(
                        By.XPATH,
                        ".//p[contains(@class, 'MuiTypography-subtitle1')]"
                    ).text.strip()
                    
                    # Click the button
                    button = card.find_element(
                        By.XPATH,
                        ".//button[contains(@class, 'MuiCardActionArea-root')]"
                    )
                    button.click()
                    time.sleep(2)
                    
                    # Get URL
                    game_url = driver.current_url
                    if game_url != base_url and game_url not in game_urls:
                        game_urls.add(game_url)
                        found_new_games = True
                        print(f"Found active game: {game_name} -> {game_url}")

                    # Return to games list and wait for page to load
                    driver.get(base_url)
                    time.sleep(2)
                    wait.until(
                        EC.presence_of_element_located((
                            By.XPATH,
                            "//div[contains(@class, 'MuiCard-root')]"
                        ))
                    )
                    
                    # If we're past page 1, click through to the current page
                    if current_page > 1:
                        for _ in range(current_page - 1):
                            next_button = wait.until(
                                EC.element_to_be_clickable((
                                    By.XPATH,
                                    "//button[@aria-label='Goto Next page']"
                                ))
                            )
                            next_button.click()
                            time.sleep(2)
                        time.sleep(2)  # Extra wait for page to settle

                except Exception as e:
                    print(f"Error with game at index {idx}: {str(e)}")
                    # Return to correct page
                    driver.get(base_url)
                    time.sleep(2)
                    if current_page > 1:
                        for _ in range(current_page - 1):
                            next_button = wait.until(
                                EC.element_to_be_clickable((
                                    By.XPATH,
                                    "//button[@aria-label='Goto Next page']"
                                ))
                            )
                            next_button.click()
                            time.sleep(2)
                    continue

            # If a max_page is specified and we've reached that page, stop scraping further pages.
            if max_page is not None and current_page >= max_page:
                print(f"Reached specified max page {max_page}.")
                break

            # Check for next page
            next_button = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//button[@aria-label='Goto Next page']"
                ))
            )
            
            if 'Mui-disabled' in next_button.get_attribute('class'):
                print("Reached last page")
                break
                
            if found_new_games:
                print(f"Moving to page {current_page + 1}")
                next_button.click()
                current_page += 1
                time.sleep(3)  # Wait for page transition
            else:
                print("No new games found on this page")
                break

        except Exception as e:
            print(f"Error processing page {current_page}: {str(e)}")
            break

    print(f"\nFound {len(game_urls)} active games")
    return list(game_urls)

def parse_prize_amount(text):
    """
    Convert a prize amount string (which might contain words like 'Million' or 'Thousand')
    into a float. For example, '5 Million' becomes 5000000.0.
    """
    s = text.replace("$", "").replace(",", "").strip().lower()
    if "million" in s:
        number_str = s.replace("million", "").strip()
        return float(number_str) * 1_000_000
    elif "thousand" in s:
        number_str = s.replace("thousand", "").strip()
        return float(number_str) * 1_000
    else:
        return float(s)

def scrape_game_details(driver, wait, url):
    """Scrape details for a single game with new data structure"""
    driver.get(url)
    time.sleep(3)

    try:
        # Get game name
        name = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//h1[contains(@class, 'MuiTypography')]"
            ))
        ).text.strip()
        print(f"Processing: {name}")

        # Get cost
        cost = float(wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//span[contains(@class, 'MuiTypography-h6') and contains(text(), '$')]"
            ))
        ).text.strip().replace("$", ""))

        # Get odds
        odds_element = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//div[.//p[contains(text(), 'Overall Odds')]]"
            ))
        )
        odds = float(re.search(r"1 in ([\d.]+)", odds_element.text).group(1))

        # Get game image URL from the background-image style attribute
        try:
            image_element = wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//div[contains(@class, 'MuiCardMedia-root') and contains(@style, 'background-image')]"
                ))
            )
            style_attr = image_element.get_attribute("style")
            # Convert any HTML-encoded quotes to normal quotes if necessary
            style_attr = style_attr.replace("&quot;", "\"")
            match = re.search(r'url\("(.+?)"\)', style_attr)
            if match:
                image_url = match.group(1)
            else:
                image_url = None
        except Exception as e:
            print("Error fetching image URL:", e)
            image_url = None

        # Get prize table rows
        table = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//table[.//th[contains(., 'Prize Amount')]]"
            ))
        )
        rows = table.find_elements(By.XPATH, ".//tbody/tr")

        # Collect prize tier data
        prize_amounts = []
        total_prizes = []
        remaining_prizes = []

        for row in rows:
            try:
                prize_text = row.find_element(By.XPATH, ".//td[1]//p").text.strip()
                prize = parse_prize_amount(prize_text)
                total = int(row.find_element(By.XPATH, ".//td[2]//p").text.strip().replace(",", ""))
                remaining = int(row.find_element(By.XPATH, ".//td[3]//p").text.strip().replace(",", ""))
                prize_amounts.append(prize)
                total_prizes.append(total)
                remaining_prizes.append(remaining)
            except Exception as row_error:
                print(f"Error processing row: {row_error}")
                continue

        return {
            'name': name,
            'cost': cost,
            'odds': odds,
            'prize_amounts': prize_amounts,
            'total_prizes': total_prizes,
            'remaining_prizes': remaining_prizes,
            'scrape_time': datetime.utcnow().isoformat(),
            'image_url': image_url  # New field added for the image URL
        }

    except Exception as e:
        print(f"Error scraping {url}: {str(e)}")
        driver.save_screenshot(f"error_{url.split('/')[-1]}.png")
        return None

def scrape_scratcher_data_selenium(max_page=None, headless=False):
    """Main function to coordinate the scraping process"""
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options

    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Universal headless configuration
    if headless or os.getenv('GITHUB_ACTIONS'):
        options.add_argument('--headless=new')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
    else:
        options.add_argument('--start-maximized')

    try:
        # Automatic driver management
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Platform-specific tweaks
        if platform.system() == 'Windows':
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            })

        wait = WebDriverWait(driver, 30)

        init_db()  # Initialize database
        
        try:
            # Phase 1: Get all game URLs
            print("Collecting active game URLs...")
            urls = get_game_urls(driver, wait, max_page=max_page)

            # Phase 2: Scrape each game's details and store directly in DB
            for url in urls:
                results = scrape_game_details(driver, wait, url)
                if results:
                    # Store in database
                    store_scraper_data(results)
                    print(f"Stored in DB: {results['name']}, ${results['prize_amounts'][0]}")

        finally:
            driver.quit()
            print("\nScraping completed! Data stored in database.")

    except Exception as e:
        print(f"Error in scrape_scratcher_data_selenium: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper for Arizona Lottery Scratcher Data")
    parser.add_argument("--page", type=int, help="Scrape up to specified page number (if omitted, scrape all pages)")
    parser.add_argument("--headless", action='store_true', help="Run browser in headless mode")
    args = parser.parse_args()
    
    print("Starting scraper...")
    scrape_scratcher_data_selenium(max_page=args.page, headless=args.headless)

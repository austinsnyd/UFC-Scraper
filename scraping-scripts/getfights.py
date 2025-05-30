from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def scrape_fights(driver, card_link):
    driver.get(card_link)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[href*="fight-details"]'))
    )
    fights_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="fight-details"]')
    fights = [element.get_attribute("href") for element in fights_elements]
    return pd.DataFrame({"fights": fights})



### actual main###
if __name__ == "__main__":
    driver = init_driver()
    link = "http://ufcstats.com/statistics/events/completed?page=all"

    # Scrape cards to get a dataframe of events
    cards_df = scrape_cards(driver, link)

    # Scrape fights for each event to get a dataframe of fights with eventIDs
    fights_df = scrape_fights(driver, cards_df)

    # Initialize empty DataFrames for event details and fight details
    all_event_details_df = pd.DataFrame()
    all_fight_details_df = pd.DataFrame()
    all_significant_strikes_df = pd.DataFrame()

    # Iterate over each event link to scrape event details
    for event_link in cards_df['card_link'].unique():
        event_details_df = scrape_event_details(driver, [event_link])
        all_event_details_df = pd.concat([all_event_details_df, event_details_df], ignore_index=True)

    # Iterate over each fight link to scrape fight details and significant strikes
    for fight_link in fights_df['fight_link'].unique():
        fight_details_df = scrape_fight_details(driver, fight_link)
        significant_strikes_df = scrape_significant_strikes(driver, fight_link)
        all_fight_details_df = pd.concat([all_fight_details_df, fight_details_df], ignore_index=True)
        all_significant_strikes_df = pd.concat([all_significant_strikes_df, significant_strikes_df], ignore_index=True)

    # Here, you might want to merge/join DataFrames based on common columns (e.g., eventID, fight_link)
    # to create a unified dataset for analysis or database insertion.

    driver.quit()

    # Optional: Save the DataFrames to files or insert them into a database
    # cards_df.to_csv('cards.csv', index=False)
    # all_event_details_df.to_csv('event_details.csv', index=False)
    # all_fight_details_df.to_csv('fight_details.csv', index=False)
    # all_significant_strikes_df.to_csv('significant_strikes.csv', index=False)

    # If saving to a database, you would use SQLAlchemy or another database connector here.

import pandas as pd
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver


def scrape_cards(driver, link):
    driver.get(link)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located(
            (By.CSS_SELECTOR, "a.b-link.b-link_style_black")
        )
    )
    event_rows = driver.find_elements(
        By.CSS_SELECTOR,
        "body > section > div > div > div > div.b-statistics__sub-inner > div > table > tbody > tr",
    )
    cards = []

    for row in event_rows:
        card_link_elements = row.find_elements(
            By.CSS_SELECTOR, "a.b-link.b-link_style_black"
        )
        if card_link_elements:
            card_link = card_link_elements[0].get_attribute("href")
            title = card_link_elements[0].text
        else:
            card_link = ""
            title = ""

        date_elements = row.find_elements(By.CSS_SELECTOR, "td:nth-child(1)")
        location_elements = row.find_elements(By.CSS_SELECTOR, "td:nth-child(2)")

        date = date_elements[0].text.split("\n")[-1] if date_elements else ""
        location = location_elements[0].text if location_elements else ""

        if title:  # Only add to cards if there is a title
            cards.append(
                {
                    "card_link": card_link,
                    "title": title,
                    "date": date,
                    "location": location,
                }
            )

    cards_df = pd.DataFrame(cards)
    # Convert date text to datetime
    cards_df["date"] = pd.to_datetime(cards_df["date"])
    # Sort by date in descending order
    cards_df = cards_df.sort_values(by="date", ascending=False).reset_index(drop=True)
    # Assign eventID starting from the total number of events for the most recent event
    total_events = len(cards_df)
    cards_df["eventID"] = range(total_events, 0, -1)
    # Assign eventID with leading zeros
    cards_df["eventID"] = cards_df["eventID"].apply(lambda x: f"{x:04}")

    return cards_df


if __name__ == "__main__":
    driver = init_driver()
    link = "http://ufcstats.com/statistics/events/completed?page=all"
    cards_df = scrape_cards(driver, link)

    # Specify the path and name of the Excel file you want to create
    excel_file_path = "cards.xlsx"  # Update this path
    # Save the DataFrame to an Excel file
    cards_df.to_excel(excel_file_path, index=False)

    print(f"Saved scraped data to '{excel_file_path}'.")

    driver.quit()

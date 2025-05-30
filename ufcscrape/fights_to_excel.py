import pandas as pd
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


def scrape_fights(driver, cards_df):
    all_fights = []
    # Iterate over the first five cards
    for index, row in cards_df.iloc[:].iterrows():
        card_link = row["card_link"]
        eventID = row["eventID"]

        driver.get(card_link)
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, 'a[href*="fight-details"]')
                )
            )
            fights_elements = driver.find_elements(
                By.CSS_SELECTOR, 'a[href*="fight-details"]'
            )
            fights = [
                {"fight_link": element.get_attribute("href"), "eventID": eventID}
                for element in fights_elements
            ]
            all_fights.extend(fights)
        except Exception as e:
            print(
                f"An error occurred while scraping event details from {card_link}: {e}"
            )

    df_fights = pd.DataFrame(all_fights)
    return df_fights


if __name__ == "__main__":
    driver = init_driver()
    link = "http://ufcstats.com/statistics/events/completed?page=all"
    cards_df = scrape_cards(driver, link)

    # The following line has been commented out to scrape all events
    # cards_df = cards_df.head()

    fights_df = scrape_fights(driver, cards_df)

    print(fights_df.head())  # Inspect the output

    # Specify the path and name of the Excel file you want to create
    excel_file_path = "fights_data.xlsx"  # Update this path as needed

    # Save the DataFrame to an Excel file
    fights_df.to_excel(excel_file_path, index=False, engine="openpyxl")

    print(f"Saved fights data to '{excel_file_path}'.")

    driver.quit()
if __name__ == "__main__":
    driver = init_driver()
    link = "http://ufcstats.com/statistics/events/completed?page=all"
    cards_df = scrape_cards(driver, link)

    # The following line has been commented out to scrape all events
    # cards_df = cards_df.head()

    fights_df = scrape_fights(driver, cards_df)

    print(fights_df.head())  # Inspect the output

    # Specify the path and name of the Excel file you want to create
    excel_file_path = "fights_data.xlsx"  # Update this path as needed

    # Save the DataFrame to an Excel file
    fights_df.to_excel(excel_file_path, index=False, engine="openpyxl")

    print(f"Saved fights data to '{excel_file_path}'.")

    driver.quit()

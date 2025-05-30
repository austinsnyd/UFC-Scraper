from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


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
    for index, row in cards_df.iloc[:5].iterrows():
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


def scrape_event_details(driver, event_links):
    all_event_details = []

    for event_link in event_links:
        try:
            driver.get(event_link)
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "tr.b-fight-details__table-row")
                )
            )
            # Extract event title here
            event_title_element = driver.find_element(
                By.CSS_SELECTOR, "body > section > div > h2 > span"
            )
            event_title = (
                event_title_element.text.strip()
            )  # Use strip() to remove any excess whitespace

            details_rows = driver.find_elements(
                By.CSS_SELECTOR, "tr.b-fight-details__table-row"
            )
            num_rows = len(details_rows)

            for i in range(1, num_rows + 1):
                # Attempt to dynamically check for NC status within the fight details
                nc_check_selector = f"tr:nth-child({i}) > td.b-fight-details__table-col.b-fight-details__table-col_style_align-top > p:nth-child(1)"
                nc_elements = driver.find_elements(By.CSS_SELECTOR, nc_check_selector)
                is_nc = any("NC" in el.text for el in nc_elements)

                # Shared details extraction remains the same
                weight_class_selector = f"tr:nth-child({i}) > td:nth-child(7) > p"
                method_selector = (
                    f"tr:nth-child({i}) > td:nth-child(8) > p:nth-child(1)"
                )
                round_selector = f"tr:nth-child({i}) > td:nth-child(9) > p"
                time_selector = f"tr:nth-child({i}) > td:nth-child(10) > p"

                weight_class = driver.find_element(
                    By.CSS_SELECTOR, weight_class_selector
                ).text
                method = driver.find_element(By.CSS_SELECTOR, method_selector).text
                round = driver.find_element(By.CSS_SELECTOR, round_selector).text
                time = driver.find_element(By.CSS_SELECTOR, time_selector).text

                # Iterate for each fighter in the row
                for j in range(1, 3):
                    row_index = i  # Adjust for 1-based indexing in CSS
                    fighter_name_selector = f"tr:nth-child({row_index}) > td:nth-child(2) > p:nth-child({j}) > a"
                    kd_selector = f"tr:nth-child({row_index}) > td:nth-child(3) > p:nth-child({j})"
                    str_selector = f"tr:nth-child({row_index}) > td:nth-child(4) > p:nth-child({j})"
                    td_selector = f"tr:nth-child({row_index}) > td:nth-child(5) > p:nth-child({j})"
                    sub_selector = f"tr:nth-child({row_index}) > td:nth-child(6) > p:nth-child({j})"

                    fighter_name = driver.find_element(
                        By.CSS_SELECTOR, fighter_name_selector
                    ).text
                    kd = driver.find_element(By.CSS_SELECTOR, kd_selector).text
                    str = driver.find_element(By.CSS_SELECTOR, str_selector).text
                    td = driver.find_element(By.CSS_SELECTOR, td_selector).text
                    sub = driver.find_element(By.CSS_SELECTOR, sub_selector).text

                    # Assign "NC" to both fighters if the NC flag is found; otherwise, assign "WIN" to the first and "LOSS" to the second
                    w_l = "NC" if is_nc else ("WIN" if j == 1 else "LOSS")

                    fighter_details = {
                        "W/L": w_l,
                        "Fighter": fighter_name,
                        "KD": kd,
                        "STR": str,
                        "TD": td,
                        "SUB": sub,
                        "Weight Class": weight_class,
                        "Method": method,
                        "Round": round,
                        "Time": time,
                        "Event Title": event_title,
                    }
                    all_event_details.append(fighter_details)

        except Exception as e:
            print(
                f"An error occurred while scraping event details from {event_link}: {e}"
            )

    return pd.DataFrame(all_event_details)


# Remember to replace the placeholders with actual Selenium WebDriver setup and usage as needed.


# The rest of your script remains unchanged

# Setting up the WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Example usage
link = "http://ufcstats.com/statistics/events/completed?page=all"
df = scrape_cards(driver, link)  # Assign the result to df
print(df)

# Pass the df to scrape_fights
df_fights = scrape_fights(driver, df)

# Extract event links from the DataFrame
event_links = df["card_link"].tolist()[:2]  # Limit to the first two event links

# Scrape event details for the selected event links
event_details_df = scrape_event_details(driver, event_links)
print(event_details_df)


if __name__ == "__main__":
    driver = init_driver()
    link = "http://www.ufcstats.com/statistics/events/completed"
    cards_df = scrape_cards(driver, link)
    driver.quit()
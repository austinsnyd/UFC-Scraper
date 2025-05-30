from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine
from sqlalchemy import text
from tqdm import tqdm


def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver


# Setup the database connection
engine = create_engine("sqlite:///UFC_Data.db")


def get_unprocessed_event_links(engine):
    """
    Fetches event links for which details haven't been scraped yet.

    Parameters:
    engine: SQLAlchemy engine connected to the SQLite database.

    Returns:
    pd.DataFrame: DataFrame containing event links that need processing.
    """
    query = """
    SELECT card_link FROM All_Cards
    WHERE details_scraped IS FALSE OR details_scraped IS NULL
    """
    df = pd.read_sql_query(query, engine)
    return df["card_link"].tolist()


def get_unprocessed_fight_links(engine):

    query = """
    SELECT fight_link
    FROM All_Fights
    WHERE details_scraped = 'FALSE' OR details_scraped IS NULL
    """
    unscraped_fights_df = pd.read_sql(query, engine)
    return unscraped_fights_df["fight_link"].tolist()


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


def scrape_fight_details(driver, fight_link):
    try:
        driver.get(fight_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "body > section > div > div > section:nth-child(3) > p",
                )
            )
        )
        event_title_element = driver.find_element(
            By.CSS_SELECTOR, "body > section > div > h2 > a"
        )
        EVENT_TITLE = event_title_element.text.strip()

        # Initialize data structure
        data = {
            "FIGHTER": [],
            "KD": [],
            "SIG_STR": [],
            "SIG_STR_PCT": [],
            "TOTAL_STR": [],
            "TD": [],
            "TD_PCT": [],
            "SUB_ATT": [],
            "REV": [],
            "CTRL": [],
            "EVENT_TITLE": [],
        }

        # Define selectors for each data point for both fighters
        selectors = {
            "FIGHTER": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(1) > a",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(2) > a",
            ],
            "KD": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(2) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(2) > p:nth-child(2)",
            ],
            "SIG_STR": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(3) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(3) > p:nth-child(2)",
            ],
            "SIG_STR_PCT": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(4) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(4) > p:nth-child(2)",
            ],
            "TOTAL_STR": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(5) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(5) > p:nth-child(2)",
            ],
            "TD": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(6) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(6) > p:nth-child(2)",
            ],
            "TD_PCT": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(7) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(7) > p:nth-child(2)",
            ],
            "SUB_ATT": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(8) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(8) > p:nth-child(2)",
            ],
            "REV": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(9) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(9) > p:nth-child(2)",
            ],
            "CTRL": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(10) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(10) > p:nth-child(2)",
            ],
        }

        # Extract data for both fighters across all categories
        for category, sel_pair in selectors.items():
            element1 = driver.find_element(By.CSS_SELECTOR, sel_pair[0])
            element2 = driver.find_element(By.CSS_SELECTOR, sel_pair[1])
            data[category].append(element1.text if element1 else "N/A")
            data[category].append(element2.text if element2 else "N/A")

        data["EVENT_TITLE"].extend([EVENT_TITLE] * 2)
        # Create DataFrame
        fight_Details = pd.DataFrame(data)

        return fight_Details

    except Exception as e:
        print(f"An error occurred while scraping fight details: {e}")
        return pd.DataFrame()


def scrape_significant_strikes(driver, fight_link):
    try:
        driver.get(fight_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "body > section > div > div > table > tbody > tr")
            )
        )
        event_title_element = driver.find_element(
            By.CSS_SELECTOR, "body > section > div > h2 > a"
        )
        EVENT_TITLE = event_title_element.text.strip()
        # Initialize data structure
        data = {
            "FIGHTER": [],
            "SIG_STR": [],
            "SIG_STR_PCT": [],
            "HEAD": [],
            "BODY": [],
            "LEG": [],
            "DISTANCE": [],
            "CLINCH": [],
            "GROUND": [],
            "EVENT_TITLE": [],
        }

        # Define selectors for each data point for both fighters
        selectors = {
            "FIGHTER": [
                "body > section > div > div > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(1) > a",
                "body > section > div > div > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(2) > a",
            ],
            "SIG_STR": [
                "body > section > div > div > table > tbody > tr > td:nth-child(2) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(2) > p:nth-child(2)",
            ],
            "SIG_STR_PCT": [
                "body > section > div > div > table > tbody > tr > td:nth-child(3) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(3) > p:nth-child(2)",
            ],
            "HEAD": [
                "body > section > div > div > table > tbody > tr > td:nth-child(4) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(4) > p:nth-child(2)",
            ],
            "BODY": [
                "body > section > div > div > table > tbody > tr > td:nth-child(5) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(5) > p:nth-child(2)",
            ],
            "LEG": [
                "body > section > div > div > table > tbody > tr > td:nth-child(6) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(6) > p:nth-child(2)",
            ],
            "DISTANCE": [
                "body > section > div > div > table > tbody > tr > td:nth-child(7) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(7) > p:nth-child(2)",
            ],
            "CLINCH": [
                "body > section > div > div > table > tbody > tr > td:nth-child(8) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(8) > p:nth-child(2)",
            ],
            "GROUND": [
                "body > section > div > div > table > tbody > tr > td:nth-child(9) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(9) > p:nth-child(2)",
            ],
        }

        # Extract data for both fighters across all categories
        for category, sel_pair in selectors.items():
            element1_text = driver.find_element(By.CSS_SELECTOR, sel_pair[0]).text
            element2_text = driver.find_element(By.CSS_SELECTOR, sel_pair[1]).text
            data[category].append(element1_text)
            data[category].append(element2_text)

        data["EVENT_TITLE"].extend([EVENT_TITLE] * 2)
        # Create DataFrame
        Significant_Strikes = pd.DataFrame(data)

        return Significant_Strikes

    except Exception as e:
        print(f"An error occurred while scraping significant strikes: {e}")
        return pd.DataFrame()


def update_event_scraped_status(engine, event_link):
    with engine.connect() as conn:
        statement = text(
            """
            UPDATE All_Cards
            SET details_scraped = TRUE
            WHERE card_link = :event_link
        """
        )
        conn.execute(statement, {"event_link": event_link})


def update_fight_scraped_status(engine, fight_link):
    with engine.connect() as conn:
        statement = text(
            """
            UPDATE All_Fights
            SET details_scraped = TRUE
            WHERE fight_link = :fight_link
        """
        )
        conn.execute(statement, {"fight_link": fight_link})


def process_fight_links_batch(driver, fight_links, engine):
    for fight_link in fight_links:
        try:
            # Scrape fight details
            fight_details_df = scrape_fight_details(driver, fight_link)
            fight_details_df.to_sql(
                "Fight_Details", con=engine, if_exists="append", index=False
            )

            # Scrape significant strikes
            sig_strike_df = scrape_significant_strikes(driver, fight_link)
            sig_strike_df.to_sql(
                "Significant_Strikes", con=engine, if_exists="append", index=False
            )

            # Mark the fight as scraped
            engine.execute(
                "UPDATE All_Fights SET details_scraped = TRUE WHERE fight_link = ?",
                (fight_link,),
            )

        except Exception as e:
            print(f"Error processing {fight_link}: {e}")


def get_all_fight_links(engine):
    """
    Fetches all fight links from the database.

    Parameters:
    engine: SQLAlchemy engine connected to the SQLite database.

    Returns:
    list: A list of all fight links to be processed.
    """
    query = "SELECT fight_link FROM All_Fights"
    df = pd.read_sql_query(query, engine)
    return df["fight_link"].tolist()


def main():
    engine = create_engine("sqlite:///UFC_Data.db")
    driver = init_driver()

    # Fetch all fight links
    fight_links = get_all_fight_links(engine)

    # Process in batches of 20
    batch_size = 20
    for i in tqdm(range(0, len(fight_links), batch_size), desc="Processing fights"):
        batch_links = fight_links[i : i + batch_size]
        for fight_link in batch_links:
            try:
                # Scrape fight details and significant strikes for each fight link
                fight_details_df = scrape_fight_details(driver, fight_link)
                sig_strike_df = scrape_significant_strikes(driver, fight_link)

                # Append scraped data to the respective tables in the database
                fight_details_df.to_sql(
                    "Fight_Details", engine, if_exists="append", index=False
                )
                sig_strike_df.to_sql(
                    "Significant_Strikes", engine, if_exists="append", index=False
                )

                # Optionally, update the details_scraped status for the processed fight
                # This step can be skipped if processing all links regardless of their status
            except Exception as e:
                print(f"Error processing {fight_link}: {e}")

    print("Processing completed for all fight links.")
    driver.quit()


if __name__ == "__main__":
    main()

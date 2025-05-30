from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd


def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver


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
        event_title = event_title_element.text.strip()

        # Initialize data structure
        data = {
            "FIGHTER": [],
            "KD": [],
            "SIG. STR.": [],
            "SIG. STR. %": [],
            "TOTAL STR.": [],
            "TD": [],
            "TD %": [],
            "SUB. ATT": [],
            "REV.": [],
            "CTRL": [],
            "Event Title": [],
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
            "SIG. STR.": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(3) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(3) > p:nth-child(2)",
            ],
            "SIG. STR. %": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(4) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(4) > p:nth-child(2)",
            ],
            "TOTAL STR.": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(5) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(5) > p:nth-child(2)",
            ],
            "TD": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(6) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(6) > p:nth-child(2)",
            ],
            "TD %": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(7) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(7) > p:nth-child(2)",
            ],
            "SUB. ATT": [
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(8) > p:nth-child(1)",
                "body > section > div > div > section:nth-child(4) > table > tbody > tr > td:nth-child(8) > p:nth-child(2)",
            ],
            "REV.": [
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

        data["Event Title"].extend([event_title] * 2)
        # Create DataFrame
        fight_details_df = pd.DataFrame(data)

        return fight_details_df

    except Exception as e:
        print(f"An error occurred while scraping fight details: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    driver = init_driver()

    # Define the fight link to test
    fight_link = "http://www.ufcstats.com/fight-details/406f2aacd1d1faf9"

    # Call the scrape_fight_details function
    fight_details_df = scrape_fight_details(driver, fight_link)

    # Print the DataFrame
    print(fight_details_df)

    driver.quit()

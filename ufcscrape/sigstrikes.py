from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def init_driver():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    return driver


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
        event_title = event_title_element.text.strip()
        # Initialize data structure
        data = {
            "FIGHTER": [],
            "SIG. STR": [],
            "SIG. STR. %": [],
            "HEAD": [],
            "BODY": [],
            "LEG": [],
            "DISTANCE": [],
            "CLINCH": [],
            "GROUND": [],
            "Event Title": [],
        }

        # Define selectors for each data point for both fighters
        selectors = {
            "FIGHTER": [
                "body > section > div > div > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(1) > a",
                "body > section > div > div > table > tbody > tr > td.b-fight-details__table-col.l-page_align_left > p:nth-child(2) > a",
            ],
            "SIG. STR": [
                "body > section > div > div > table > tbody > tr > td:nth-child(2) > p:nth-child(1)",
                "body > section > div > div > table > tbody > tr > td:nth-child(2) > p:nth-child(2)",
            ],
            "SIG. STR. %": [
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

        data["Event Title"].extend([event_title, event_title])
        # Create DataFrame
        fight_details_df = pd.DataFrame(data)

        return fight_details_df

    except Exception as e:
        print(f"An error occurred while scraping significant strikes: {e}")
        return pd.DataFrame()


# Initialize the driver
driver = init_driver()

# Define the fight link
fight_link = "http://www.ufcstats.com/fight-details/406f2aacd1d1faf9"

# Call the scrape_significant_strikes function with the fight link
significant_strikes_df = scrape_significant_strikes(driver, fight_link)

# Output the result to console
print(significant_strikes_df)

# Quit the driver after the test
driver.quit()

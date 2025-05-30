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


def scrape_cards(driver, link):
    driver.get(link)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "a.b-link.b-link_style_black")
        )
    )
    cards_elements = driver.find_elements(
        By.CSS_SELECTOR, "a.b-link.b-link_style_black"
    )
    cards = [element.get_attribute("href") for element in cards_elements]
    return pd.DataFrame({"cards": cards})


def scrape_fights(driver, card_link):
    driver.get(card_link)
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, 'a[href*="fight-details"]'))
    )
    fights_elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="fight-details"]')
    fights = [element.get_attribute("href") for element in fights_elements]
    return pd.DataFrame({"fights": fights})


def scrape_fight_details(driver, fight_link):
    # Initialize an empty dictionary to store fight details
    fight_details = {"Fighter 1": {}, "Fighter 2": {}}

    try:
        driver.get(fight_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "tr.b-fight-details__table-row")
            )
        )
        # Select the row that contains the stats
        stats_row = driver.find_elements(
            By.CSS_SELECTOR, "tr.b-fight-details__table-row"
        )[1]

        # Extract text from each cell in the row
        stats_cells = stats_row.find_elements(
            By.CSS_SELECTOR, "td.b-fight-details__table-col"
        )

        # Define the keys for the statistics in the order they appear
        stats_keys = [
            "Name",
            "KD",
            "SIG. STR.",
            "SIG. STR. %",
            "TOTAL STR.",
            "TD",
            "TD %",
            "SUB. ATT",
            "REV.",
            "CTRL",
        ]

        # Iterate over each cell and split the text to separate stats for Fighter 1 and Fighter 2
        for key, cell in zip(stats_keys, stats_cells):
            fighter_stats = cell.text.split("\n")  # Expecting two stats per cell
            if len(fighter_stats) == 2:
                # Assign stats for each fighter to the corresponding dictionary key
                fight_details["Fighter 1"][key] = fighter_stats[0]
                fight_details["Fighter 2"][key] = fighter_stats[1]
            else:
                print("Unexpected number of stats found in a cell.")
                return (
                    pd.DataFrame()
                )  # Return an empty DataFrame if the data is not as expected

        # Convert the dictionaries to DataFrames
        fighter_1_df = pd.DataFrame([fight_details["Fighter 1"]])
        fighter_2_df = pd.DataFrame([fight_details["Fighter 2"]])

        # Concatenate both DataFrames
        fight_details_df = pd.concat([fighter_1_df, fighter_2_df], ignore_index=True)

        return fight_details_df

    except Exception as e:
        print(f"An error occurred while scraping fight details: {e}")
        return pd.DataFrame()


def scrape_significant_strikes(driver, fight_link):
    # Initialize an empty dictionary to store fight details
    significant_strikes_details = {"Fighter 1": {}, "Fighter 2": {}}

    try:
        driver.get(fight_link)
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "body > section > div > div > table > tbody > tr")
            )
        )

        # Select the rows that contain the significant strikes stats
        significant_strikes_rows = driver.find_elements(
            By.CSS_SELECTOR, "body > section > div > div > table > tbody > tr"
        )

        # Assuming the first row contains the column titles and the second row the values
        stats_keys = significant_strikes_rows[0].find_elements(By.TAG_NAME, "th")
        stats_values = significant_strikes_rows[1].find_elements(By.TAG_NAME, "td")

        # Extract text from each cell in the header row for column titles
        column_titles = [th.text for th in stats_keys]

        # Extract text from each cell in the value row for the fighters' stats
        for title, value in zip(column_titles, stats_values):
            fighter_stats = value.text.split("\n")  # Expecting two stats per cell
            if len(fighter_stats) == 2:
                # Assign stats for each fighter to the corresponding dictionary key
                significant_strikes_details["Fighter 1"][title] = fighter_stats[0]
                significant_strikes_details["Fighter 2"][title] = fighter_stats[1]
            else:
                print("Unexpected number of stats found in a cell.")
                return (
                    pd.DataFrame()
                )  # Return an empty DataFrame if the data is not as expected

        # Convert the dictionaries to DataFrames
        fighter_1_df = pd.DataFrame([significant_strikes_details["Fighter 1"]])
        fighter_2_df = pd.DataFrame([significant_strikes_details["Fighter 2"]])

        # Concatenate both DataFrames
        significant_strikes_df = pd.concat(
            [fighter_1_df, fighter_2_df], ignore_index=True
        )

        return significant_strikes_df

    except Exception as e:
        print(f"An error occurred while scraping significant strikes: {e}")
        return pd.DataFrame()


# Initialize an empty DataFrame to store all fight details
all_fight_details = pd.DataFrame()

driver = init_driver()  # Ensure you have called this function to initialize the driver

try:
    link = "http://ufcstats.com/statistics/events/completed?page=all"
    cards_df = scrape_cards(driver, link)

    if not cards_df.empty:
        first_card_link = cards_df.iloc[0]["cards"]
        fights_df = scrape_fights(driver, first_card_link)
        limited_fights_df = fights_df.head(2)  # Adjust the number of fights for testing

        fight_data_collected = False
        fight_data = []

        for fight_index, fight_row in limited_fights_df.iterrows():
            fight_link = fight_row["fights"]
            fight_details_df = scrape_fight_details(driver, fight_link)

            if not fight_details_df.empty:
                fight_data_collected = True
                fight_data.append(fight_details_df)
            else:
                print(f"No valid data found for fight link: {fight_link}")

        if fight_data_collected:
            excel_file_name = "UFC_fight_data.xlsx"
            with pd.ExcelWriter(excel_file_name, engine="openpyxl") as writer:
                for index, df in enumerate(fight_data):
                    sheet_name = f"Fight_{index + 1}"
                    df.to_excel(writer, sheet_name=sheet_name)
            print(f"Fight data exported to {excel_file_name}")
        else:
            print("No fight data was collected to write to Excel.")
finally:
    driver.quit()


# Write all fight details to a single Excel sheet
if not all_fight_details.empty:
    excel_file_name = "UFC_fight_data_combined.xlsx"
    with pd.ExcelWriter(excel_file_name, engine="openpyxl", mode="w") as writer:
        all_fight_details.to_excel(writer, index=False, sheet_name="All Fights")
    print(f"Fight data exported to {excel_file_name}")
else:
    print("No fight data was collected.")

import pandas as pd
from sqlalchemy import create_engine

# Define paths to the Excel files
fights_file_path = "fights_data.xlsx"  # Update this path
cards_file_path = "cards.xlsx"  # Update this path

# Create a SQLAlchemy engine for the SQLite database
engine = create_engine("sqlite:///UFC_Data.db")

# Read the data from Excel files into Pandas DataFrames
fights_df = pd.read_excel(fights_file_path)
cards_df = pd.read_excel(cards_file_path)

# Check if the date column is in number format and convert if necessary
if cards_df["date"].dtype == "float64":
    cards_df["date"] = pd.TimedeltaIndex(cards_df["date"], unit="d") + pd.to_datetime(
        "1899-12-30"
    )
elif cards_df["date"].dtype != "datetime64[ns]":
    # Attempt to convert to datetime if not already
    cards_df["date"] = pd.to_datetime(cards_df["date"])

# Write the data to tables in the SQLite database
fights_df.to_sql("All_Fights", engine, if_exists="replace", index=False)
cards_df.to_sql("All_Cards", engine, if_exists="replace", index=False)

print("Data has been successfully written to the UFC Data database.")

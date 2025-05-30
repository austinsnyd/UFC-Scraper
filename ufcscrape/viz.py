import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Connect to the database
engine = create_engine("sqlite:///UFC_Data.db")

# Query to fetch relevant columns
query = """
SELECT WEIGHT_CLASS, ROUND, TIME
FROM Event_Details
"""
df = pd.read_sql_query(query, engine)


# Preprocess the TIME column to convert times into total minutes
def time_to_minutes(time_str):
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes + seconds / 60.0  # Convert to total minutes
    except ValueError:  # Handle any formatting issues, e.g., empty strings
        return 0


# Apply the conversion to the TIME column
df["TIME_IN_MINUTES"] = df["TIME"].apply(time_to_minutes)

# Pivot the table to create a matrix of average time spent in each round per weight class
pivot_table = df.pivot_table(
    values="TIME_IN_MINUTES", index="WEIGHT_CLASS", columns="ROUND", aggfunc="mean"
)

# Plotting the heatmap
plt.figure(figsize=(12, 8))
sns.heatmap(
    pivot_table, cmap="YlGnBu", annot=False
)  # Set annot=False to remove the numbers
plt.title("Average Finish by Round")
plt.ylabel("Weight Class")
plt.xlabel("Round")
plt.xticks(rotation=45)  # Rotate the x labels to make them more readable
plt.tight_layout()  # Adjust layout
plt.show()

plt.savefig("average_finish_by_round.png", dpi=300)

plt.show()

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Suppress warnings for cleaner output
import warnings

warnings.filterwarnings("ignore")

# Connect to your SQLite database
engine = create_engine("sqlite:///UFC_Data.db")

# SQL Query to select method counts by weight class
query_methods_by_weightclass = """
SELECT WEIGHT_CLASS, METHOD, COUNT(*) as Count
FROM Event_Details
WHERE WEIGHT_CLASS NOT IN ('Super Heavyweight', 'Open Weight', 'Catch Weight')
AND METHOD NOT IN ('DQ', 'Other', 'Overturned')
GROUP BY WEIGHT_CLASS, METHOD
ORDER BY WEIGHT_CLASS, METHOD
"""

# Read the query result into a DataFrame
df_methods = pd.read_sql_query(query_methods_by_weightclass, engine)

# Pivot the DataFrame to create a matrix suitable for a heatmap
pivot_df = df_methods.pivot_table(
    index="WEIGHT_CLASS", columns="METHOD", values="Count", aggfunc="sum", fill_value=0
)

# Plotting the heatmap without annotations
plt.figure(figsize=(14, 8))
sns.heatmap(pivot_df, cmap="cubehelix", linewidths=0.5, annot=False)

# Set the title and labels
plt.title("Frequency of Victory Methods by Weight Class")
plt.xlabel("Method of Victory")
plt.ylabel("Weight Class")

# Rotate the x-axis labels for better readability
plt.xticks(rotation=45)

# Save the figure
plt.savefig("methods_by_weightclass_heatmap.png")

# Show the plot
plt.show()

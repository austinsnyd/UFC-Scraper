import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# Connect to your SQLite database
engine = create_engine("sqlite:///UFC_Data.db")

# SQL Query to select KO finishes
query = """
SELECT ed.WEIGHT_CLASS, ed.FIGHTER, ed.ROUND, ed.METHOD
FROM Event_Details ed
WHERE ed.METHOD LIKE '%KO%'
"""

df_ko = pd.read_sql_query(query, engine)

# Count KOs per fighter per weight class per round
df_ko_count = (
    df_ko.groupby(["WEIGHT_CLASS", "FIGHTER", "ROUND"])
    .size()
    .reset_index(name="Num_KOs")
)

# Identify the top fighter in each weight class based on total KOs
df_top_ko = (
    df_ko_count.groupby(["WEIGHT_CLASS", "FIGHTER"])["Num_KOs"].sum().reset_index()
)
df_top_ko = (
    df_top_ko.sort_values(by=["Num_KOs"], ascending=False)
    .drop_duplicates(["WEIGHT_CLASS"])
    .sort_values(by=["WEIGHT_CLASS"])
)

# Merge back to get round-specific data for these top fighters
df_top_ko_rounds = pd.merge(
    df_ko_count, df_top_ko[["WEIGHT_CLASS", "FIGHTER"]], on=["WEIGHT_CLASS", "FIGHTER"]
)

# Adjust WEIGHT_CLASS column to include fighter's name for the x-axis
df_top_ko_rounds["WEIGHT_CLASS_FIGHTER"] = (
    df_top_ko_rounds["WEIGHT_CLASS"] + " - " + df_top_ko_rounds["FIGHTER"]
)

# Plotting
plt.figure(figsize=(14, 8))
sns.barplot(
    x="WEIGHT_CLASS_FIGHTER",
    y="Num_KOs",
    hue="ROUND",
    data=df_top_ko_rounds,
    dodge=True,
    palette="coolwarm",
)
plt.title("Top Fighter KO Finishes per Round by Weight Class")
plt.xlabel("Weight Class - Fighter")
plt.ylabel("Number of KO Finishes")
plt.xticks(rotation=90)  # Rotate for better readability

plt.tight_layout()
plt.savefig("Top_Fighter_KO_Finishes.png", dpi=300)
plt.show()

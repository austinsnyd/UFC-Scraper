🥋 UFC Fight Data Scraper
📌 Project Overview
This Python-based project scrapes and stores historical UFC fight data from ufcstats.com. It was developed to support future analysis and modeling for predicting UFC fight outcomes, especially in the context of making informed sports betting decisions.

The scraper collects fight-level statistics including knockdowns, strikes, takedowns, submission attempts, and more — and organizes the data into a structured format for analysis and visualization.

🎯 Motivation
The UFC is highly unpredictable, with a wide variety of fighting styles and competitors. When placing bets — especially in casual social settings — it's not always feasible to research every fighter. This project was designed to streamline access to fight data and enable fast comparisons between fighters, laying the groundwork for a future betting assistant app.

🛠️ Tools & Technologies
Python

Selenium + Chrome Driver – for dynamic web scraping

Pandas – for data wrangling and structuring

SQLite / CSV / JSON – for database and file storage

SQLAlchemy – for database handling

Matplotlib / Seaborn – for visualization

🧩 Features
Scrapes:

All past UFC events, including event metadata (title, date, location)

Fight-level statistics (KD, STR, TD, SUB, Method, Round, Time)

Detailed breakdowns of totals and significant strikes by body target and position

Stores the scraped data in structured formats (JSON, CSV, SQLite)

Cleaned key fields for analysis, including splitting "X of Y" stats into numeric columns

Visualizations of:

Average fight durations by weight class

Knockout rounds by fighter

Method of victory frequency by weight class


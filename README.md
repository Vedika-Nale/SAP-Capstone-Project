# SAP-Capstone-Project
# 🥗 Smart Diet Tracker v3.0

A desktop calorie-tracking application built with Python and CustomTkinter. It uses the **USDA FoodData Central API** to fetch real-time nutritional data, validates food items live as you type, and stores all meal logs in a local SQLite database — no account or internet subscription required.

---

## Features

- **Live food validation** — Color-coded border feedback as you type: green (found), yellow (searching), red (not recognized)
- **Meal categorization** — Log entries under Breakfast, Lunch, Dinner, or Snacks
- **Date navigation** — Browse and log meals for any past or future date
- **Daily calorie progress** — Visual progress bar toward a configurable 2000 kcal goal
- **Weekly trend chart** — 7-day bar graph rendered with Matplotlib
- **Non-food filtering** — Blacklist blocks invalid entries like metal, plastic, and stone
- **Response caching** — In-memory cache reduces redundant API calls

---

## Tech Stack

| Component | Library/Tool |
|---|---|
| UI Framework | CustomTkinter |
| Nutritional Data | USDA FoodData Central API |
| Database | SQLite3 (stdlib) |
| Charts | Matplotlib |
| HTTP Requests | Requests |
| Threading | Python `threading` module |

---

## Installation
```bash
pip install customtkinter requests matplotlib
```

Then run:
```bash
python DIET APP SAP.py
```

A `diet.db` file will be created automatically in the same directory on first run.

---

## Configuration

At the top of `diet_tracker.py`, you can adjust:
```python
API_KEY = "your_usda_api_key_here"   # Get a free key at https://fdc.nal.usda.gov/
DAILY_GOAL = 2000                     # Your daily calorie target (kcal)
```

> Get a free USDA API key at [https://fdc.nal.usda.gov/api-guide.html](https://fdc.nal.usda.gov/api-guide.html)

---

## Usage

1. Select a meal type (Breakfast / Lunch / Dinner / Snacks)
2. Type a food name and wait for the green border — this confirms the item was found in the USDA database
3. Enter the weight in grams
4. Click **Add Entry to Date**
5. Switch to **Today Log** to review your entries or **Weekly Graph** to see your 7-day trend

-x-o-x-

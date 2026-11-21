# Global Sales Intelligence

**An interactive business analytics and data visualization dashboard built with Python, Google Colab and Streamlit.**

This project analyses the Global Superstore dataset (51,290 order lines, 147 countries, January 2011 to December 2014). The data is inspected and cleaned in a Google Colab notebook, then explored through an interactive Streamlit dashboard with filters, charts, maps and a sales forecast.

> Major-semester project, Data Visualization.
> Authors: **Danyal Ahmad** and **Shafaat Zaman Khattak**

---

## Overview

Companies that sell worldwide collect thousands of order records, and a table that large is hard to read. This project turns the Global Superstore data into answers to practical business questions:

- How have sales and profit changed from 2011 to 2014?
- Which categories, products, customers and countries earn money, and which lose it?
- How do discounts relate to profit?
- How many orders are returned, and where?
- What might sales look like over the next 12 months?

The work has two parts. First, a Google Colab notebook inspects the raw data, cleans it without changing the business totals, adds the Returns and People sheets, and explores the results. Second, a Streamlit dashboard lets anyone filter the cleaned data and explore it through charts, tables, a world map and a forecast.

The main finding is that the business grew strongly, but heavy discounting is strongly associated with lost profit. The clearest example is Turkey, which applies a flat 60% discount to every order and loses money on all of them.

---

## Features

**Interactive dashboard (Streamlit)**

- Sidebar filters: year, market, category, segment, country and order-date range.
- Headline numbers: total sales, total profit, profit margin, unique orders, average order value and return rate. They update with the filters.
- Eight tabs:

| Tab | What it shows |
|---|---|
| Overview | Sales and profit by year, margin by market, yearly growth |
| Time | Monthly trend, seasonality by year, quarterly sales |
| Products | Category and sub-category profit, treemap, top and bottom products |
| Customers | Segment share, customer rankings, orders per customer, sales concentration |
| Geography | World map (sales, profit, margin or orders), top and bottom countries, regional margins |
| Discounts | Margin by discount band, share of loss-making lines, correlation matrix, discount vs profit |
| Returns and shipping | Return rate by dimension, shipping time and cost, regional manager performance |
| Forecast | 12-month sales forecast with approximate range, second-model cross-check, growth what-if slider, model accuracy |

- Download button for the filtered data.

**Analysis pipeline (Google Colab)**

1. **Inspection:** structure, types, missing values, duplicates, outliers and date checks, without changing the data.
2. **Cleaning:** trimmed text, removed Postal Code, added derived columns, merged the Returns and People sheets, added ISO country codes, and validated that totals match the original.
3. **Exploration:** sales over time, products, customers, geography, discounts, shipping, returns and managers.
4. **Forecasting:** backtested five methods on monthly sales and forecast the next 12 months.

---

## Rules used in every calculation

- **Orders are counted by unique Order ID**, not rows. Each row is an order line (51,290 lines, 25,035 orders).
- **Return rate uses unique orders** (1,172 returned orders out of 25,035).
- **Profit margin = total profit / total sales** for each group, not an average of row margins.
- **Negative profits and outliers are kept**, because they are genuine business results.

---

## Key findings

All figures come from the project's notebook outputs.

- Sales rose from 2,259,450.90 (2011) to 4,299,865.87 (2014), about +90%. Profit rose from 248,940.81 to 504,165.97, about +102%.
- Total sales are 12,642,501.91 and total profit is 1,467,457.29, an overall margin of about 11.6%. 24.46% of order lines lose money.
- Profit margin falls at every step as discounts rise: 25.32% with no discount and -111.02% above 50%. This holds with and without Turkey.
- Turkey has a flat 60% discount on all 1,378 of its order lines and loses money on every one (profit -98,447.23). Without Turkey, the EMEA market's margin rises from 5.45% to 20.40%.
- Technology is the most profitable category. Tables is the only sub-category with a total loss. 29 of 147 countries have a total loss.
- 4.68% of orders were returned.
- Forecast: the best-supported simple model (seasonal naive with growth) predicts about 5.43 million in sales for 2015, which assumes growth similar to 2014's. See the limitations below.

---

## Project structure

```text
global-sales-intelligence/
├── app.py                          # Streamlit dashboard
├── requirements.txt                # Python libraries for the dashboard
├── run_dashboard.bat               # Windows launcher
├── run_dashboard.sh                # Mac/Linux launcher
├── global_superstore_clean.csv     # Cleaned dataset (output of the notebook)
├── forecast_next_12_months.csv     # Forecast (output of the notebook)
├── monthly_history.csv             # Monthly sales history (output of the notebook)
├── forecast_backtest_score.csv     # Forecast accuracy table (output of the notebook)
└── notebooks/
    └── Global_Sales_Intelligence.ipynb   # Colab notebook (Stages 1 to 5)
```

The dashboard expects the CSV files to sit in the **same folder as `app.py`**.

---

## Getting started

### Requirements

- Python 3.10 or newer (download from [python.org](https://www.python.org/downloads/); on Windows, tick **"Add Python to PATH"** during setup)
- Libraries: Streamlit, pandas, NumPy and Plotly (listed in `requirements.txt`)

### Run the dashboard

1. Clone or download this repository.
2. Open a terminal in the project folder.
3. Install the libraries:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the dashboard:

   ```bash
   python -m streamlit run app.py
   ```

5. Open `http://localhost:8501` in your browser if it doesn't open automatically.

**Shortcut on Windows:** double-click `run_dashboard.bat`. On Mac/Linux, run `bash run_dashboard.sh`.

### Troubleshooting

- *"Data file not found":* check that `global_superstore_clean.csv` is in the same folder as `app.py` and has exactly that name (browsers add `(1)` or `(2)` to repeated downloads).
- *"CSV is missing columns":* use the latest cleaned file, which includes the `Country ISO3` column.
- *Forecast tab shows a warning:* put `forecast_next_12_months.csv` and `monthly_history.csv` next to `app.py`.

---

## Reproduce the analysis in Google Colab

1. Download the Global Superstore dataset from [Kaggle](https://www.kaggle.com/datasets/shekpaul/global-superstore).
2. Open `notebooks/Global_Sales_Intelligence.ipynb` in [Google Colab](https://colab.research.google.com).
3. Run the cells in order. The notebook asks you to upload the original Excel file (it uses the Orders, Returns and People sheets).
4. The notebook saves `global_superstore_clean.csv` and the forecast files. Download them into the dashboard folder.

---

## Tech stack

| Library | Used for |
|---|---|
| pandas, NumPy | Data loading, cleaning, grouping and calculations |
| Plotly | Interactive charts, treemap and world map |
| Streamlit | The interactive dashboard |
| Matplotlib, Seaborn | Early inspection charts in Colab |
| openpyxl, xlrd | Reading Excel files |
| pycountry | Converting country names to ISO codes |
| statsmodels | Holt-Winters and SARIMA forecasting models |

---

## Data

The dataset is **Global Superstore**, available on [Kaggle](https://www.kaggle.com/datasets/shekpaul/global-superstore). The original file has three sheets: Orders (51,290 rows), Returns (1,173 rows) and People (13 rows). Please check the dataset's license on its Kaggle page before redistributing it.

Postal Code was removed because it exists only for the United States.

---

## Limitations and assumptions

- **Association is not cause.** Discounts and losses are linked, but the analysis cannot separate discounts from product mix or market. The reason for Turkey's 60% discount is not in the data.
- **AMEA = EMEA.** The People sheet lists a region called AMEA while the Orders sheet uses EMEA. They were matched because all 12 other regions matched exactly. This should be confirmed with the data owner.
- **Returns.** The data does not say whether returned sales were refunded, so profit on returned orders may be overstated.
- **Forecast.** It continues past patterns, so it cannot know about price changes, competitors or the economy. It was tested on limited history (48 months). The best simple model scales last year's months by last year's growth, and its approximate range comes from one backtest year, so it likely understates real uncertainty. SARIMA performed poorly because the data is too short for its seasonal part.
- **Small markets.** Margins for small markets, such as Canada (384 order lines), are less stable than those of large markets.
- The dataset ends in December 2014.

---

## Future work

- Opportunity score for choosing which country to focus on in each category.
- Forecasts by market and category.
- A discount what-if scenario to estimate profit under lower discounts.
- A model to predict loss-making order lines.
- Deployment on Streamlit Community Cloud.

---

## Acknowledgements

- Dataset: Global Superstore, via Kaggle.
- Built with Python, Streamlit, pandas, Plotly and Google Colab.

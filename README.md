# Why Isn't Olist Growing?

End to end analysis of about 100,000 orders from Olist, a Brazilian online marketplace, to find out why sales stopped growing in 2018.

**[View the interactive dashboard on Tableau Public](https://public.tableau.com/app/profile/yuta.banishky/viz/OlistDashboard_17904600384160/Dashboard1)**  |  **[Read the full report (PDF)](E-commerce%20OLIST%20findings%20report.pdf)**

![Olist dashboard](Olist%20Dashboard.png)

## The Short Version

Olist's monthly sales grew almost ninefold in 2017, then flattened at about R$1.0M a month in 2018. The reason: **almost nobody buys a second time.** Growth depended on constantly finding new customers, and when that slowed, so did sales. Late deliveries make it worse.

## Key Findings

| Finding | Number |
|---|---|
| Customers who never bought again | **97%** (only 2,801 of 93,358 are repeat buyers) |
| Best month for customers coming back | **Under 1%** in every monthly group |
| Average rating, late vs on time orders | **2.6 vs 4.3 stars** |
| Expected sales, next 3 months | **About R$1.0M a month**, no growth |

1. **Sales grew fast in 2017, then flattened.** Revenue peaked around R$1.15M in November 2017 (Black Friday) and has held near R$1.0M to R$1.1M since.
2. **Fewer than 1 in 100 customers come back.** Grouping customers by the month they first bought, no group ever had more than 0.79% return in a later month.
3. **Only 3% of customers are regulars.** The best groups to target are High Value New (14,454 recent big spenders) and At Risk (13,735 big spenders who went quiet).
4. **Late deliveries cost almost 2 stars.** A bad first order is a big reason customers never return.

## Recommendations

1. **Ask for a second order.** Send High Value New customers a reminder or small discount 2 to 4 weeks after their first purchase.
2. **Win back big spenders.** Send At Risk customers a strong comeback offer.
3. **Fix late deliveries.** Start with the sellers and regions that are late most often.

## How It Was Built

```
Kaggle CSVs  ->  SQL Server  ->  SQL views + Python  ->  Tableau dashboard  ->  Report
```

| Step | Tool | What it does |
|---|---|---|
| Store | SQL Server | Nine Olist tables loaded into a local database |
| Analyze | SQL | Views for monthly revenue, cohort retention, and delivery vs reviews |
| Model | Python (pandas) | RFM customer segments and a 3 month revenue forecast, written back to SQL Server |
| Visualize | Tableau | Dashboard connected to the views and tables |
| Communicate | PDF report | Plain language findings with a technical appendix |

## Files

| File | Description |
|---|---|
| [`views.sql`](views.sql) | SQL views used by the dashboard |
| [`week5_export.py`](week5_export.py) | Builds RFM segments and the revenue forecast |
| `Olist Dashboard.twbx` | Tableau workbook (open with Tableau Public, free) |
| `E-commerce OLIST findings report.pdf` | Full findings report |

## How to Run It

1. Download the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) from Kaggle.
2. Load the CSVs into a SQL Server database named `Olist`.
3. Run `views.sql` in SSMS.
4. Install packages: `pip install pandas sqlalchemy pyodbc`
5. Update the `SERVER` name at the top of `week5_export.py`, then run `python week5_export.py`.
6. Open the `.twbx` in Tableau.

## Limitations

- Olist sells through bigger marketplaces, so many customers may not know they bought from Olist. Some of the low return rate may be a brand awareness issue.
- Late deliveries and low ratings go together, but that doesn't prove late deliveries are the only reason customers leave.
- The forecast is a simple moving average and won't predict holiday spikes.
- Data covers late 2016 to 2018.

## Next Steps

- Predict which orders will get a low review (logistic regression on delivery time, price, freight, and state)
- Seasonal forecast with Prophet
- Late delivery rates by state and seller
- Compare rule based segments with k means clustering

---

**Yuta Banishky**  |  [LinkedIn](https://linkedin.com/in/yutabanishky)  |  [Portfolio](https://yutabanishky.com)

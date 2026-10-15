Olist E-commerce Order Management Dashboard

1. Dataset and Business Context

Dataset: Brazilian E-Commerce Public Dataset by Olist on Kaggle

This project uses the olist_orders_dataset.csv file from the Olist Brazilian E-Commerce public dataset. Each row represents an order and contains information about its status, purchase time, approval time, carrier handoff, actual delivery, and estimated delivery.

The dataset contains historical order records rather than live tracking information. It is useful for studying order fulfillment and delivery operations, but it should not be treated as a real-time view of current orders.

2. Decision-Maker and Business Objective

Primary user: E-commerce Operations Manager.

The manager needs to review order fulfillment progress regularly and identify orders that require follow-up.

The dashboard supports a specific operational decision:

“If the manager sees orders that have not been shipped, orders still in transit, or orders with potential delivery delays, they can prioritize follow-up with the fulfillment team and investigate possible delivery problems.”

Without a dashboard, the manager may need to manually inspect order records and sort orders by status and date. This takes time and makes it harder to identify important exceptions quickly.

A dashboard is more useful than a one-time report because order fulfillment is a recurring operational process. Managers need a consistent overview of order status and delivery progress whenever updated data becomes available.

3. What the Dashboard Shows

The dashboard focuses on information that can support immediate operational decisions.

Headline Metrics

The most important metrics should appear at the top of the page so that the manager can quickly understand the overall situation:

* Total number of orders.
* Number of orders that have not yet been shipped.
* Number of orders that have been shipped but not yet delivered.

These metrics help the manager assess the size of the current workload and identify orders that may require attention.

Supporting Visualization

An order-status breakdown helps the manager understand how orders are distributed across fulfillment stages, including delivered, shipped, canceled, and other recorded statuses.

A date filter or order-status filter allows the manager to focus on a relevant subset of orders instead of reviewing every record.

Detailed Order Records

A detailed table can help the manager investigate individual orders when follow-up is needed. Order identifiers, statuses, and relevant timestamps are more actionable than a large number of unrelated charts.

The dashboard should prioritize operational clarity over visual complexity.

4. What I Chose Not to Show and Why

1. Customer-level personal details

The dashboard does not need customer names, addresses, or other personal details to provide a high-level view of fulfillment progress. Excluding these details reduces unnecessary exposure of personal information and keeps attention on operational decisions.

2. Unrelated product and marketing analysis

Product-category comparisons, customer segmentation, and marketing performance are outside the main purpose of this dashboard. Although these analyses may be useful for other business questions, they do not directly help an operations manager prioritize unshipped or delayed orders. They are therefore excluded to keep the dashboard focused.

5. Data Quality and Potential Misinterpretation

The dataset records historical order events, and some timestamps may be missing. Missing carrier handoff or customer delivery timestamps can make it difficult to determine an order’s exact fulfillment stage.

The dashboard should distinguish recorded order statuses from classifications inferred from available timestamps. Missing timestamps should not automatically be interpreted as proof that an order is currently delayed.

The dataset is a historical snapshot, so its order counts and delivery patterns do not represent live operational conditions. The dashboard should clearly label the dataset as historical and display the data period once the date range has been verified.

Delivery delays should be evaluated by comparing actual delivery dates with estimated delivery dates when both are available. Orders with incomplete date information should be handled separately rather than assigned an unsupported delay status.

6. Data Refresh and Review Frequency

For a real e-commerce operation, I would recommend refreshing order data hourly and having the operations manager review the dashboard at least once each business day, with additional checks during periods of heavy order volume.

Hourly updates provide a practical balance between timely information and the cost of repeatedly retrieving and processing data. Orders approaching or exceeding their estimated delivery dates should receive priority attention.

The main metric to monitor is the number of orders that have not been handed over to the carrier. A sustained increase in this number, or an order remaining unshipped beyond the company’s normal processing target, should trigger an investigation by the fulfillment team.

Stale data can cause managers to overlook orders requiring action or to follow up on orders whose status has already changed.

The current project reads from a local CSV file and does not automatically receive live updates. The hourly refresh described above is the proposed frequency for a production system, not a feature currently implemented by this project. The Kaggle data should be labeled as a historical snapshot, and its actual date range should be verified from the data before being displayed.

7. Technical Implementation

The application is built with:

* Python for application logic.
* Streamlit for the interactive dashboard.
* Pandas for loading and processing order data.
* Plotly Express for interactive data visualizations.
* CSV as the current data source.

The application converts relevant timestamp columns into datetime values, checks for required columns, and classifies orders using recorded statuses and available delivery timestamps.

Streamlit caching helps avoid repeatedly loading the same dataset during normal interactions.

8. Project Files

* order_dataset.py — Main Streamlit dashboard application.
* olist_orders_dataset.csv — Order dataset used by the application.
* requirements.txt — Python package dependencies.
* README.md — Project documentation and design rationale.

9. Limitations and Future Improvements

The current dashboard is designed for historical order analysis and operational monitoring. It does not independently retrieve live carrier events or automatically synchronize with an order management database.

Future improvements could include scheduled data ingestion, clearer overdue-order alerts, more robust treatment of missing timestamps, and a verified data-period label in the interface.

These improvements would make the dashboard more suitable for ongoing operational use while preserving its focus on actionable information.

# Business Analytics Portfolio

This portfolio presents an end-to-end business analytics case built around merchant performance diagnosis, GMV decline analysis, SQL/Python analysis, interactive dashboards, anomaly detection, and automated weekly reporting.

The focus is not only the code. It is a complete business analysis workflow: defining the business problem, designing KPI logic, extracting data, identifying signals, generating insights, and turning the analysis into decision-support deliverables.

## Project Overview

In an e-commerce operating scenario, a key merchant may show a continuous decline in GMV. Before making business recommendations, the first question is whether the decline is caused by platform-wide movement, category-level fluctuation, or merchant-specific operational issues.

This project uses public anonymized e-commerce transaction data to build a reusable analysis framework. It decomposes GMV into orders, AOV, seller contribution, category structure, SKU movement, and observable risk signals. The final outputs include three Streamlit modules, business analysis deliverables, Executive Summary documents, and resume materials.

## Core Business Questions

- Is the merchant's GMV decline abnormal?
- Is the change driven by the platform/category trend or by merchant-specific issues?
- Which indicators contribute most to the business decline: orders, AOV, seller mix, category mix, or SKU structure?
- Which merchants or SKUs should be prioritized for follow-up investigation?
- How can the analysis be converted into ongoing monitoring and weekly reporting?

## Live Portfolio Demo

[Open Streamlit Portfolio](https://huaxu0907-spec-business-analytics-portfolio-app-9hxbax.streamlit.app)

The online app includes the full portfolio entrance and the three interactive modules below.

## Core Projects

### 1. Business Analytics Dashboard

![Dashboard Screenshot](assets/screenshots/dashboard.png)

**Business Background**  
Business teams need a fast way to monitor GMV, order volume, AOV, active merchants, seller contribution, category contribution, and merchant-level performance changes.

**Problem**  
GMV alone cannot explain what happened. The dashboard needs to help users move from high-level performance monitoring to merchant diagnosis without losing the business context.

**Analysis Method**  
The dashboard applies KPI decomposition, period-over-period comparison, seller/category contribution analysis, and merchant change ranking. Users can filter by date range, category, and seller scope.

**Key Findings**  
The dashboard helps identify whether GMV movement is mainly associated with order volume, AOV, seller concentration, or category structure. It also surfaces merchants that require deeper diagnosis.

**Business Recommendation**  
Use the dashboard as the first layer of business monitoring. When negative changes are detected, move selected merchants into the diagnosis module for evidence-based follow-up.

**Tech Stack**  
SQL, Python, Pandas, Streamlit, Plotly

**Demo Link**  
[View Dashboard App](https://huaxu0907-spec-business-analytics-portfolio-app-9hxbax.streamlit.app)

### 2. Business Anomaly Detection

![Anomaly Detection Screenshot](assets/screenshots/anomaly_detection.png)

**Business Background**  
When multiple merchants operate on the same platform, business teams need a structured way to identify abnormal performance changes and prioritize follow-up actions.

**Problem**  
Manual review is inefficient and inconsistent. The key challenge is to convert observable business signals into a prioritized anomaly list.

**Analysis Method**  
The module compares active months and uses GMV decline, order decline, late delivery rate, and low review rate as observable signals. It generates severity levels, priority labels, evidence fields, investigation directions, and recommended actions.

**Key Findings**  
The analysis identifies abnormal merchant events and separates high-priority cases from lower-priority monitoring cases. The result is not treated as confirmed root cause, but as a structured investigation queue.

**Business Recommendation**  
Use the anomaly list to prioritize P0/P1/P2 follow-up. High-severity merchants should be reviewed first, especially when GMV/order decline is accompanied by observable experience signals.

**Tech Stack**  
SQL, Python, Pandas, Streamlit, Business Rules

**Demo Link**  
[View Anomaly Detection App](https://huaxu0907-spec-business-analytics-portfolio-app-9hxbax.streamlit.app)

### 3. Automated Weekly Business Report

![Weekly Report Screenshot](assets/screenshots/weekly_report.png)

**Business Background**  
Business teams often need recurring weekly updates for management review, including performance changes, risk signals, and next-step actions.

**Problem**  
Manual weekly reporting is repetitive and may create inconsistent KPI definitions. The report process should reuse the same analysis logic as the dashboard.

**Analysis Method**  
The module calculates weekly KPIs, compares them with the previous equivalent period, summarizes key changes, extracts risk signals, and generates a downloadable Word report.

**Key Findings**  
The weekly report converts dashboard-level analysis into a management-facing summary. It keeps KPI definitions consistent across page preview and Word output.

**Business Recommendation**  
Use the report generator for regular business review. The output should be combined with real operational data such as inventory, traffic, exposure, promotion, and supply-chain records for further validation.

**Tech Stack**  
Python, Pandas, Streamlit, python-docx, Business Reporting

**Demo Link**  
[View Weekly Report App](https://huaxu0907-spec-business-analytics-portfolio-app-9hxbax.streamlit.app)

## Analysis Framework

```text
Business Understanding
        |
        v
KPI Design
        |
        v
SQL Data Extraction
        |
        v
Python Data Analysis
        |
        v
Anomaly Diagnosis
        |
        v
Business Insight
        |
        v
Business Recommendation
        |
        v
Validation and Monitoring
```

## Deliverables

| Deliverable | Purpose | Link |
| --- | --- | --- |
| Business Analysis Report | Full business analysis report | [Business_Analysis_Report.pdf](analysis/deliverables/Business_Analysis_Report.pdf) |
| Business Project Brief | Project background and analysis scope | [Business_Project_Brief.docx](analysis/deliverables/Business_Project_Brief.docx) |
| SQL Scripts | Data extraction and analysis logic | [merchant_anomaly_analysis.sql](analysis/merchant_anomaly_analysis.sql) |
| Python Notebook | Analysis process and outputs | [merchant_anomaly_analysis.ipynb](analysis/merchant_anomaly_analysis.ipynb) |
| Dashboard App | Business monitoring and merchant diagnosis | [dashboard/app.py](dashboard/app.py) |
| Anomaly Detection App | Merchant anomaly identification | [anomaly_detection/app.py](anomaly_detection/app.py) |
| Weekly Report App | Weekly business reporting | [weekly_report/app.py](weekly_report/app.py) |
| Executive Summary | Interview-ready project summary | [Executive_Business_Final.docx](executive/Executive_Business_Final.docx) |
| Business Resume | Resume for Business/Data Analytics roles | [Resume_Business_Final.docx](resume/Resume_Business_Final.docx) |
| Product Resume | Resume for Product/AI Product Analytics roles | [Resume_Product_Final.docx](resume/Resume_Product_Final.docx) |

## Resume

This repository also includes two role-oriented resume versions:

- [Business Resume](resume/Resume_Business_Final.docx): Business Analytics, Operations Analytics, Data Analytics, BI
- [Product Resume](resume/Resume_Product_Final.docx): Product Analytics, AI Product, Data Product

## Portfolio Structure

```text
Business-Analytics-Portfolio/
|-- app.py                    # Unified Streamlit portfolio entrance
|-- app_core.py               # Shared page rendering logic
|-- dashboard/                # Business Analytics Dashboard
|-- anomaly_detection/        # Merchant Anomaly Detection
|-- weekly_report/            # Automated Weekly Business Report
|-- analysis/                 # SQL, Notebook, figures, and analysis deliverables
|-- executive/                # Executive Summary documents
|-- resume/                   # Resume documents
|-- assets/screenshots/       # Project screenshots
|-- data/                     # Prepared public anonymized data
|-- shared/                   # KPI, charts, anomaly, reporting logic
`-- requirements.txt          # Runtime dependencies
```

## How To Run Locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

Independent module entrances:

```bash
streamlit run dashboard/app.py
streamlit run anomaly_detection/app.py
streamlit run weekly_report/app.py
```

## Target Roles

- Business Analyst
- Operations Analyst
- Data Analyst
- BI Analyst
- Merchant Analyst
- Product Analyst
- Data Product Analyst
- AI Product Analyst

## Evidence Boundary

This project is based on public anonymized e-commerce data. The analysis can support business diagnosis and investigation prioritization, but it does not claim to prove real enterprise operating results.

Public transaction data cannot directly prove inventory, traffic, exposure, promotion, competitor pricing, or supply-chain mechanisms. If real enterprise data were available, the next step would be to add these fields for validation and monitoring.

## Contact

- GitHub: [huaxu0907-spec](https://github.com/huaxu0907-spec)
- Email: 3080622230@163.com

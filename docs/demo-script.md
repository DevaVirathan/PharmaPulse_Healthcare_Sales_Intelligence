# Five-Minute POC Demo Script (T18)

**Product:** PharmaPulse — Healthcare Sales Intelligence  
**Audience:** Commercial Sales Leaders, Regional Managers, and Business Analysts  
**Duration:** 5 Minutes  
**Goal:** Demonstrate the complete end-to-end flow from data upload to analytics and explainable anomaly alerts.  

---

## Preparation Before Starting

1. Ensure PostgreSQL is running and seeded (`python -m scripts.seed`).
2. Start the Backend API (Terminal 1):
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```
3. Start the Frontend Dev Server (Terminal 2):
   ```powershell
   cd frontend
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.
5. Have `sample-data/pharma_sales_sample.csv` ready to upload.

---

## Minute 1: The Problem & The Solution

* **Action:** Open `http://localhost:5173/` in the browser.
* **Speaking Points:**
  * *"Commercial pharma sales teams face a critical challenge: sales data arrives fragmented across regions and therapeutic brands every month."*
  * *"Identifying significant revenue shifts manually across multiple brands and territories is slow, error-prone, and often delays strategic responses."*
  * *"PharmaPulse solves this by providing automated ingestion, trustworthy SQL analytics, and rule-based, explainable anomaly detection that highlights where to investigate without jumping to unverified conclusions."*
  * *Point out the top-right badges: 'POC Demo (Synthetic Data)' and 'API Online' connected to the live backend.*

---

## Minute 2: Transactional Ingestion & Validation

* **Action:** Click **Upload Data** in the sidebar (navigates to `http://localhost:5173/upload`).
* **Speaking Points:**
  * *"Here we see our ingestion interface. It requires an exact five-column contract: sales date, brand name, region name, quantity, and revenue."*
  * *"The ingestion engine enforces atomic database transactions, rejects unknown brands or regions, checks data types, and flags invalid numbers."*
* **Demonstration Steps:**
  1. Drag and drop `sample-data/pharma_sales_sample.csv` onto the upload zone (or click to select it).
  2. Click **Upload & Process**. Observe the real-time progress bar.
  3. Review the result panel:
     * **Status:** `COMPLETED`
     * **Total Rows:** `240`
     * **Accepted Rows:** `240`
     * **Rejected Rows:** `0`
  4. Explain partial acceptance: *"If any row had an invalid date or negative revenue, only valid rows would be saved, and row-level errors would be listed here for immediate correction."*
  5. *(Optional test of idempotency)* Click **Upload & Process** again with the same file. Show the friendly **409 Conflict** banner preventing duplicate data and linking to the original import.
  6. Click **Import History** to show the audit trail with timestamps and SHA-256 hash preview.

---

## Minute 3: Real-Data Analytics & Workspace

* **Action:** Click **Overview** in the sidebar (navigates to `http://localhost:5173/`).
* **Speaking Points:**
  * *"With our sales data ingested, the Overview dashboard computes SQL aggregates on the fly—no hard-coded numbers and no fake 'real-time' claims."*
* **Walkthrough:**
  1. **KPI Cards:** Point out **Total Sales Revenue** (formatted in INR e.g. `₹1,47,12,345.00`), **Total Units Sold**, **5 Active Brands**, and **4 Active Regions**.
  2. **Global Date Filter:** Demonstrate clicking the date filter quick presets (e.g. `2026 YTD`, `All 12M`) and show that every KPI and chart updates synchronously.
  3. **Visualizations:**
     * Dual-axis **Monthly Trend Line Chart** showing revenue and unit volume over time.
     * **Revenue by Brand** and **Revenue by Region** bar charts.
* **Action:** Click **Sales Analytics** in the sidebar.
  * Filter by Brand (*Cardioval*) and Region (*Chennai*).
  * Show active filter chips, synchronized trend charts, and the granular, paginated sales transactions table at the bottom.

---

## Minute 4: Explainable Anomaly Detection

* **Action:** Click **Alerts** in the sidebar (navigates to `http://localhost:5173/alerts`).
* **Speaking Points:**
  * *"This is the detection engine. Rather than using an unexplainable 'black-box' model, PharmaPulse uses explicit, business-approved rules to spot month-over-month shifts."*
  * *"Our default demo rules are: revenue decline $\ge 20\%$ triggers a HIGH alert; revenue growth $\ge 30\%$ triggers a MEDIUM alert, with a ₹10,000 minimum baseline."*
* **Demonstration Steps:**
  1. Click **Run Anomaly Detection**.
  2. Select month `2026-10` and click **Execute Detection**.
  3. Show the result banner: *20 brand-region pairs evaluated, 4 alerts created.*
  4. Observe the summary KPI counters update: 2 High Severity, 2 Medium Severity, 4 Open Queue.
  5. Click **Review** on the top High-severity decline alert: **Cardioval in Chennai**.
  6. In the modal, explain:
     * **Previous Baseline:** `₹2,65,518.26`
     * **Current Value:** `₹1,64,621.32`
     * **Observed Change:** `-38.00%`
     * **Threshold:** Crossed the configured decline threshold of `20.00%`.
     * **Stored Explanation:** Highlight the factual, objective text. Point out the reminder: *An alert is an objective signal to prioritize investigation; it does not diagnose causes (like stockouts or rep performance).*

---

## Minute 5: Business Value & Next Steps

* **Action:** Within the **Alert Details Modal**:
  1. Change the status dropdown from `OPEN` to `INVESTIGATING`.
  2. Click **Save Status**. Show the success confirmation.
  3. Close the modal and show that the **Open Queue** decremented and **Investigating** incremented.
* **Closing Speaking Points:**
  * *"In 5 minutes, we have ingested raw sales data, verified clean persistence, reviewed high-level performance trends, and flagged high-priority regional anomalies for commercial investigation."*
  * *"Notice what PharmaPulse does NOT do: it does not expose patient data, invent unverified root causes, or bypass data governance."*
  * *"Future production phases will introduce Role-Based Access Control (RBAC), automated recurring detection cron jobs, and authorized, read-only Key Account Management (KAM) integration."*
  * *"Thank you. We are now open for feedback and questions."*

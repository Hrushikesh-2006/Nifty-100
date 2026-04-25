<div align="center">

# 🚀 India's Premier Financial Intelligence Platform

![Main Hero](static/images/hero_main.png)

### *Precision Analytics for India's Top 100 Market Leaders*

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Managed-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-F7DF1E?style=for-the-badge)](LICENSE)

</div>

---

## 🌟 Project Overview

The **Nifty 100 Financial Intelligence Platform** is a high-performance web application designed for investors, analysts, and financial enthusiasts. It provides deep insights into India's top 100 companies by market capitalization, combining historical financial data with **real-time metrics** and **ML-driven health scores**.

### 🚀 Key Features
- **⚡ Real-time Market Data**: Live stock prices, revenue, and margins via FMP API.
- **🧠 ML Health Scoring**: Proprietary algorithm calculating company stability and growth potential.
- **⚖️ Side-by-Side Comparison**: Multi-metric comparison tool for benchmarking market leaders.
- **🔍 Advanced Screener**: Filter companies based on ROCE, ROE, P/E, and custom financial ratios.
- **📊 Power BI Integration**: Interactive embedded dashboards for macro-level market analysis.

---

## 🛠️ Tech Stack

<div align="center">

| Layer | Technology |
| :--- | :--- |
| **Backend** | ![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django) ![DRF](https://img.shields.io/badge/DRF-A30000?style=flat-square&logo=django) |
| **Frontend** | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3) ![JS](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript) |
| **Database** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql) |
| **Caching** | ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis) |
| **Data API** | ![FMP](https://img.shields.io/badge/Financial_Modeling_Prep-FF6F61?style=flat-square) |
| **ML/ETL** | ![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=pandas) ![ScikitLearn](https://img.shields.io/badge/Scikit_Learn-F7931E?style=flat-square&logo=scikit-learn) |

</div>

---

## 🏗️ Architecture

<div align="center">
  <img src="static/images/architecture.png" width="400" alt="Architecture Diagram">
</div>

### How it Works:
1.  **Data Extraction**: The ETL pipeline fetches raw data from official exchanges and Excel files.
2.  **Processing**: Pandas and Scikit-learn clean the data and calculate **ML Health Scores**.
3.  **Real-time Sync**: The `RealtimeDataService` fetches live metrics from FMP API with a **15-minute intelligent cache**.
4.  **API Layer**: Django Rest Framework (DRF) serves JSON data to the frontend.
5.  **Frontend**: A responsive dashboard renders data with color-coded health indicators and interactive charts.

---

## 🚦 Getting Started

### 1. Clone & Install
```bash
git clone https://github.com/Hrushikesh-2006/Nifty-100.git
cd Nifty-100
pip install -r REQUIREMENTS_REALTIME.txt
```

### 2. Setup Environment
Create a `.env` file or update `config/settings.py` with your API keys:
```python
# Real-time API Key
FMP_API_KEY = "your_key_here"
```

### 3. Initialize & Run
```bash
python manage.py migrate
python manage.py fetch_realtime_data
python manage.py runserver
```

---

## 📸 Screenshots & UI

<div align="center">
  <table>
    <tr>
      <td><b>Market Overview</b></td>
      <td><b>Stock Screener</b></td>
    </tr>
    <tr>
      <td><img src="static/images/home.png" width="400"></td>
      <td><img src="static/images/screener.png" width="400"></td>
    </tr>
    <tr>
      <td><b>Head-to-Head Comparison</b></td>
      <td><b>Executive Dashboard</b></td>
    </tr>
    <tr>
      <td><img src="static/images/compare.png" width="400"></td>
      <td><img src="static/images/dashboard.png" width="400"></td>
    </tr>
  </table>
</div>

---

## 📞 Support & Contact

Developed by **Hrushikesh**  
📧 [hrushikeshanumula1111@gmail.com](mailto:hrushikeshanumula1111@gmail.com)  
🔗 [GitHub Profile](https://github.com/Hrushikesh-2006)

---

<div align="center">

*Designed for the future of Financial Intelligence.*  
⭐ **Star this repo if you find it useful!**

</div>

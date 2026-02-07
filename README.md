# 📊 E-Commerce Price & Competition Analysis
## Amazon vs Jumia Price Comparison Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

**A powerful data science application for comparing prices and analyzing competition between Amazon and Jumia**

[Features](#-features) • [Screenshots](#-screenshots) • [Installation](#-installation) • [Usage](#-usage) • [Tech Stack](#-tech-stack) • [License](#-license)

</div>

---

## 📖 About The Project

This project is a comprehensive e-commerce analytics platform that tracks, compares, and analyzes product prices between **Amazon** and **Jumia**. Using advanced data science techniques including web scraping, NLP sentiment analysis, and machine learning, it provides actionable insights for both buyers and sellers.

### 🎯 Key Objectives

- **Price Tracking**: Monitor and compare prices across platforms in real-time
- **Sentiment Analysis**: Analyze customer reviews using Natural Language Processing
- **Trend Detection**: Identify price trends and patterns over time
- **Smart Recommendations**: ML-powered product and pricing recommendations
- **Competitive Intelligence**: Detect overpriced/underpriced products

---

## ✨ Features

### 📊 Core Functionality

- **🔍 Price Comparison**: Side-by-side price analysis between Amazon and Jumia
- **📈 Price Evolution**: Historical price tracking with trend visualization
- **😊 Sentiment Analysis**: NLP-based analysis of customer reviews and ratings
- **🎯 Product Recommendations**: ML-powered suggestion system
- **💰 Value Detection**: Identify overpriced and underpriced products
- **📱 Interactive Dashboard**: Real-time visualizations with Plotly and Streamlit

### 🛠️ Technical Features

- **Web Scraping**: Automated data collection with pagination and anti-bot handling
- **Data Processing**: Clean, normalize, and analyze large datasets
- **NLP Analysis**: Advanced sentiment analysis on customer reviews
- **Machine Learning**: Price prediction and product clustering
- **Responsive Design**: Modern UI that works on all devices

---

## 📸 Screenshots

### Main Dashboard
![Dashboard](screenshots/dashboard_main.png)
*Interactive dashboard with real-time metrics and price comparisons*

### Price Analysis
![Price Analysis](screenshots/price_analysis.png)
*Detailed price evolution charts and trend analysis*

### Sentiment Analysis
![Sentiment Analysis](screenshots/sentiment_analysis.png)
*Customer review sentiment visualization with NLP insights*

### Product Comparison
![Comparison](screenshots/comparison.png)
*Side-by-side product comparison with detailed metrics*

### Recommendations
![Recommendations](screenshots/recommendations.png)
*Smart product recommendations based on ML algorithms*

---

## 🚀 Installation

### Prerequisites

Before you begin, ensure you have the following installed:
```bash
✅ Python 3.9 or higher
✅ pip (Python package manager)
✅ Git
✅ 4GB RAM minimum
```

### Step 1: Clone the Repository
```bash
git clone https://github.com/mohamedhou/ecommerce-price-analysis.git
cd ecommerce-price-analysis
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS/Linux
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Download NLTK Data (for sentiment analysis)
```bash
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
```

### Step 5: Configure Environment (Optional)
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings (if needed)
```

---

## 💻 Usage

### Run the Application
```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`

### Alternative Port
```bash
# Run on a different port
streamlit run app.py --server.port 8080
```

### Docker Deployment (Optional)
```bash
# Build the Docker image
docker build -t ecommerce-analytics .

# Run the container
docker run -p 8501:8501 ecommerce-analytics
```

---

## 🔧 Tech Stack

### Backend & Data Science

| Technology | Purpose |
|-----------|---------|
| **Python 3.9+** | Core programming language |
| **Pandas** | Data manipulation and analysis |
| **NumPy** | Numerical computations |
| **Scikit-learn** | Machine learning models |
| **NLTK** | Natural language processing |
| **TextBlob** | Sentiment analysis |

### Frontend & Visualization

| Technology | Purpose |
|-----------|---------|
| **Streamlit** | Web application framework |
| **Plotly** | Interactive visualizations |
| **Matplotlib** | Statistical charts |
| **Seaborn** | Advanced visualizations |

### Web Scraping

| Technology | Purpose |
|-----------|---------|
| **BeautifulSoup4** | HTML parsing |
| **Requests** | HTTP requests |
| **Selenium** | Dynamic content scraping |

---

## 📂 Project Structure
```
ecommerce-price-analysis/
├── 📂 data/                    # Data files
│   ├── raw/                   # Raw scraped data
│   ├── processed/             # Cleaned data
│   └── external/              # External data sources
├── 📂 pages/                   # Streamlit pages
│   ├── 1_dashboard.py
│   ├── 2_price_analysis.py
│   ├── 3_sentiment.py
│   └── 4_recommendations.py
├── 📂 src/                     # Source code
│   ├── data_processing.py
│   ├── scraping.py
│   ├── analysis.py
│   ├── sentiment.py
│   └── models.py
├── 📂 utils/                   # Utilities
│   └── helpers.py
├── 📂 assets/                  # Static files
│   ├── css/
│   └── images/
├── 📂 screenshots/            # App screenshots
├── 📜 app.py                  # Main application
├── 📜 requirements.txt        # Dependencies
├── 📜 config.py              # Configuration
├── 📜 .env.example           # Environment template
├── 📜 Dockerfile             # Docker config
└── 📜 README.md              # This file
```

---

## 🎓 How It Works

### 1. Data Collection
- **Web scraping** from Amazon and Jumia using BeautifulSoup and Selenium
- **Pagination handling** to collect comprehensive data
- **Anti-bot mechanisms** to ensure reliable scraping

### 2. Data Processing
- **Data cleaning** and normalization
- **Price standardization** across platforms
- **Feature engineering** for ML models

### 3. Analysis & Insights
- **Price trend analysis** using time series
- **Sentiment analysis** on customer reviews using NLP
- **Product clustering** to identify similar items
- **Anomaly detection** for pricing irregularities

### 4. Visualization & Recommendations
- **Interactive dashboards** with real-time updates
- **ML-based recommendations** for buyers and sellers
- **Predictive analytics** for future price trends

---

## 🌟 Key Features Explained

### Price Comparison
Compare identical products across Amazon and Jumia with detailed metrics including:
- Current prices
- Historical price trends
- Price gap percentage
- Best time to buy

### Sentiment Analysis
Analyze customer reviews using advanced NLP techniques:
- Positive/Negative/Neutral classification
- Key topics and themes extraction
- Review summary generation
- Sentiment score over time

### Smart Recommendations
Get intelligent suggestions based on:
- Price history and trends
- Product ratings and reviews
- Similar product analysis
- Value for money calculations

---

## 📋 Requirements

**Main Dependencies:**
```txt
streamlit==1.28.0
pandas==2.0.3
numpy==1.24.3
plotly==5.15.0
scikit-learn==1.3.0
nltk==3.8.1
textblob==0.17.1
beautifulsoup4==4.12.2
requests==2.31.0
selenium==4.11.2
```

See `requirements.txt` for complete list.

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
```
MIT License - Copyright (c) 2024 Mohamed Hou
```

---

## 👤 Author

**Mohamed Hou**

- 📧 Email: mohamed.hou@example.com
- 💼 LinkedIn: [linkedin.com/in/mohamedhou](https://linkedin.com/in/mohamedhou)
- 🐦 Twitter: [@mohamed_hou](https://twitter.com/mohamed_hou)
- 🌐 Portfolio: [mohamedhou.com](https://mohamedhou.com)

---

## 🙏 Acknowledgments

- **Streamlit** - Amazing framework for data apps
- **Plotly** - Interactive visualization library
- **Scikit-learn** - Machine learning tools
- **NLTK** - Natural language processing toolkit

---

## ❓ Support

If you encounter any issues or have questions:

- 📫 Open an [issue](https://github.com/mohamedhou/ecommerce-price-analysis/issues)
- 💬 Contact via email
- ⭐ Star the project if you find it useful!

---

<div align="center">

**Made with ❤️ by Mohamed Hou**

[![GitHub stars](https://img.shields.io/github/stars/mohamedhou/ecommerce-price-analysis?style=social)](https://github.com/mohamedhou/ecommerce-price-analysis/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/mohamedhou/ecommerce-price-analysis?style=social)](https://github.com/mohamedhou/ecommerce-price-analysis/network/members)

</div>

# Chemical Equipment Parameter Visualizer

A comprehensive full-stack visualization suite designed to analyze Time-Series data from chemical processing equipment. The system consists of a centralized **Django Backend** that serves data to both a polished **Desktop Application** (PyQt5) and a modern **Web Dashboard** (React).


## 🚀 Features

### 🖥️ Desktop Application
- **Native Experience**: Built with **PyQt5** for high-performance rendering on Windows.
- **Advanced Plotting**: Utilizes **Matplotlib** with a custom dark-themed `GridSpec` layout.
    - **Trend Analysis**: Dual-axis line chart for Flow Rate vs. Pressure.
    - **Equipment Distribution**: Pie chart with distinct coloring and absolute counts.
    - **Correlations**: Scatter plots for operational regime analysis.
- **Multithreading**: Implements `QThread` for non-blocking file uploads and background data fetching.
- **Robustness**: Handles network timeouts, file permission errors, and invalid data gracefully.
- **Report Generation**: Generates and downloads detailed PDF reports with **localized timestamps** (IST).

### 🌐 Web Dashboard
- **Modern UI**: Built with **React** and **Vite**, featuring a responsive dark mode design.
- **Interactive Charts**: Uses **Chart.js v4** for dynamic web-based visualizations.
- **Instant Feedback**: Real-time upload status and error handling.

### 🔌 Backend API
- **Django REST Framework**: robust API endpoints for data ingestion (`/upload/`), historical querying (`/history/`), and reporting (`/report/`).
- **Data Processing**: Uses **Pandas** for efficient CSV parsing and statistical aggregation.
- **PDF Engine**: Integrated **ReportLab** for server-side report generation.

---

## 🛠️ Technology Stack

| Component | Key Technologies |
|-----------|------------------|
| **Backend** | Python, Django, DRF, Pandas, SQLite, ReportLab |
| **Desktop** | Python, PyQt5, Matplotlib, Requests, Numpy |
| **Frontend** | React, Vite, Chart.js, CSS Modules |

---

## 📦 Installation & Setup

### Prerequisites
- **Python 3.9+**
- **Node.js 16+** (for Web Dashboard)

### 1. Backend Setup
The backend is the core of the system. Run this first.

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# database migrations
python manage.py makemigrations
python manage.py migrate

# Start the server
python manage.py runserver
```

### 2. Desktop App Setup
Open a new terminal.

```bash
# Navigate to desktop directory
cd desktop

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### 3. Web Dashboard (Optional)
Open a new terminal.

```bash
# Navigate to web directory
cd web

# Install Node modules
npm install

# Start development server
npm run dev
```

---

## 📖 Usage Guide

1.  **Launch the Backend**: Ensure `python manage.py runserver` is running on port 8000.
2.  **Start the Desktop App**: Run `main.py`.
3.  **Upload Data**:
    - Click **"Upload CSV"**.
    - Select a valid CSV file containing columns like `FlowRate`, `Pressure`, `Temperature`, `EquipmentType`.
    - The dashboard will automatically update with 5 visualizations.
4.  **Download Report**:
    - Click **"Download PDF"** to get a summary report.
    - The report includes dataset statistics and equipment distribution, timestamped in your local time.
5.  **View History**:
    - Switch to the **History Tab** to view a log of all previously uploaded datasets.

---

## 📂 Project Structure

```
chemical_visualizer/
├── backend/                # Django Project
│   ├── api/                # API App (Views, Models, Serializers)
│   ├── chemical_project/   # Project Settings
│   ├── manage.py
│   └── requirements.txt
├── desktop/                # PyQt5 Application
│   ├── main.py             # Entry Point & UI Logic
│   └── requirements.txt
├── web/                    # React Application
│   ├── src/
│   ├── index.html
│   └── package.json
└── README.md               # You are here
```

## 📄 License
This project is open source and available under the [MIT License](LICENSE).

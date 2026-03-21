# 🏨 Kashmir Hotel PMS — Streamlit App

A complete Property Management System for your hotel built with Python + Streamlit.

---

## 📁 Project Structure

```
hotel_pms/
├── app.py              ← Main application (all code here)
├── requirements.txt    ← Python packages needed
├── README.md           ← This file
└── data/               ← Auto-created on first run
    ├── rooms.json
    ├── bookings.json
    ├── bills.json
    └── expenses.json
```

---

## 🚀 Step-by-Step Setup

### Step 1 — Install Python
Download from https://python.org (version 3.9 or newer)
Check it works:
```bash
python --version
```

### Step 2 — Open Terminal / Command Prompt
- **Windows**: Press Win+R → type `cmd` → Enter
- **Mac**: Press Cmd+Space → type `Terminal` → Enter

### Step 3 — Go to your project folder
```bash
cd hotel_pms
```

### Step 4 — Install required packages
```bash
pip install -r requirements.txt
```

### Step 5 — Run the app
```bash
streamlit run app.py
```

The app will open automatically in your browser at:
**http://localhost:8501**

---

## 📋 Features

| Section       | What you can do                                              |
|---------------|--------------------------------------------------------------|
| Dashboard     | See live overview of rooms, revenue, pending checkouts       |
| Rooms         | Add/delete rooms, toggle status (available/occupied/cleaning)|
| Bookings      | Add new bookings, search, filter, one-click checkout         |
| Billing       | Generate bills with food/laundry/electricity charges         |
| Expenses      | Log all hotel expenses by category                           |
| Reports       | Revenue vs expenses, occupancy charts, booking summary       |

---

## 💾 Data Storage
All your data is saved automatically in the `data/` folder as JSON files.
No internet or database needed — works completely offline.

---

## 🔧 To Stop the App
Press `Ctrl + C` in the terminal window.

## 🔄 To Restart
```bash
streamlit run app.py
```

# 🎓 FedPoly Nasarawa — Student ID Card & QR Verification System

> **A Web-Based Student ID Card Generation System with Scannable QR Codes for Online and Offline Identity Verification**
>
> *A Case Study of the Department of Computer Science, School of Information Technology, The Federal Polytechnic Nasarawa*
>
> *HND Final Year Project — 2024/2025 Academic Session*

---

## 📋 Project Overview

This system allows the Federal Polytechnic Nasarawa to:
- Register students and generate beautiful, printable ID cards
- Embed encrypted QR codes on each card
- Verify student identity by scanning the QR code with **any phone camera** — no special app needed
- Scan works both **online (web scanner)** and **offline (printed card)**
- Generate and print comprehensive admin reports

---

## 🚀 Quick Start (Local Setup)

### Requirements
- Python 3.10 or higher
- pip

### Step 1 — Clone or download the project
```bash
cd fedpoly_idcard
```

### Step 2 — Create a virtual environment
```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Mac/Linux:
source venv/bin/activate
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Set up environment variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env and set your values (especially SECRET_KEY and BASE_URL)
```

### Step 5 — Run the app
```bash
python run.py
```

### Step 6 — Open in browser
```
http://localhost:5000
```

---

## 🔐 Default Login Credentials

| Role | Username | Password | Action Required |
|------|----------|----------|-----------------|
| Admin | `admin` | `Admin@FedPoly2024` | Change password on first login |
| Staff | (set by admin) | `Staff@FedPoly2024` | Change password on first login |
| Student | (matric number, e.g. `csc2024001`) | `Student@2024` | Change password on first login |

---

## 📱 How QR Scanning Works

1. Admin registers a student → system generates an **encrypted QR code**
2. Student downloads their ID card as **PDF or PNG**
3. Student prints the card at any business center
4. Anyone scans the QR code with **any phone camera** (Google Lens, iPhone Camera, any QR app)
5. The phone opens a browser page showing the student's **full verified profile**

### For Local Network Use (Project Defense):
1. Turn on **hotspot** on your phone
2. Connect your **laptop** to the hotspot
3. Connect the **supervisor's phone** to the same hotspot
4. Run the app and set `BASE_URL=http://YOUR_LAPTOP_IP:5000` in `.env`
5. Find your laptop IP: run `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

---

## 🌐 Deploying to Render.com (Free Online Hosting)

### Step 1 — Create a GitHub repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/fedpoly-id-system.git
git push -u origin main
```

### Step 2 — Go to render.com
- Sign up at https://render.com (free)
- Click **New → Web Service**
- Connect your GitHub repository

### Step 3 — Configure the service
| Setting | Value |
|---------|-------|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `gunicorn wsgi:app` |
| Environment | Python 3 |

### Step 4 — Add environment variables in Render dashboard
| Key | Value |
|-----|-------|
| `SECRET_KEY` | (generate a random long string) |
| `ENCRYPTION_KEY` | (generate a random long string) |
| `BASE_URL` | `https://your-app-name.onrender.com` |
| `FLASK_ENV` | `production` |

### Step 5 — Add a PostgreSQL database
- In Render dashboard: **New → PostgreSQL**
- Copy the connection string and add as `DATABASE_URL` environment variable

### Step 6 — Deploy
Render will automatically deploy. Your app will be live at:
`https://your-app-name.onrender.com`

---

## 🗂️ Project Structure

```
fedpoly_idcard/
│
├── run.py                    # Development server entry point
├── wsgi.py                   # Production (Gunicorn) entry point
├── config.py                 # App configuration
├── requirements.txt          # Python dependencies
├── render.yaml               # Render.com deployment config
├── .env.example              # Environment variables template
│
├── app/
│   ├── __init__.py           # App factory
│   │
│   ├── models/
│   │   └── models.py         # Database models (User, Student, Staff, ScanLog)
│   │
│   ├── routes/
│   │   ├── auth.py           # Login, logout, change password
│   │   ├── admin.py          # Admin dashboard, student/staff management, reports
│   │   └── routes.py         # Staff scanner, student portal, public verify
│   │
│   ├── utils/
│   │   ├── qr_utils.py       # QR code generation, AES encryption, ID card image
│   │   ├── report_utils.py   # PDF report generation with ReportLab
│   │   ├── helpers.py        # File upload, stats, utilities
│   │   └── seed.py           # Default admin account creation
│   │
│   ├── templates/
│   │   ├── base.html         # Base layout with sidebar
│   │   ├── auth/             # Landing page, login, change password
│   │   ├── admin/            # All admin pages
│   │   ├── staff/            # Staff dashboard, scanner, scan logs
│   │   ├── student/          # Student dashboard, ID card, profile
│   │   └── public/           # QR verification result page
│   │
│   └── static/
│       ├── css/main.css      # Main stylesheet
│       ├── js/main.js        # Main JavaScript
│       ├── images/           # School logo
│       ├── photos/           # Student passport photos
│       ├── qrcodes/          # Generated QR code images
│       └── idcards/          # Generated ID card files (PDF & PNG)
│
└── instance/
    └── fedpoly.db            # SQLite database (auto-created)
```

---

## 🔑 System Roles

### Admin
- Register and manage students
- Upload student passport photos
- Generate/regenerate QR codes
- Download ID cards (PDF & PNG)
- Register and manage staff accounts
- View all scan logs
- Generate and print reports

### Staff
- Open web-based camera scanner
- Scan and verify student QR codes
- View personal scan history

### Student
- View personal profile
- Preview ID card on screen
- Download ID card as **PDF** (for printing)
- Download ID card as **PNG** (for digital use)
- View scan history

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Database | SQLite (dev) / PostgreSQL (production) |
| ORM | SQLAlchemy + Flask-SQLAlchemy |
| Authentication | Flask-Login + Flask-Bcrypt |
| QR Generation | qrcode[pil] library |
| Encryption | AES-256 via Python cryptography library |
| ID Card Image | Pillow (PIL) |
| PDF Generation | ReportLab |
| Camera Scanner | html5-qrcode (JavaScript) |
| Frontend | HTML5, CSS3, JavaScript |
| Fonts | Google Fonts (Cinzel, Nunito) |
| Icons | Font Awesome 6 |
| Production Server | Gunicorn |
| Hosting | Render.com |

---

## 📞 Support

For any technical issues, contact the Department of Computer Science,
School of Information Technology, The Federal Polytechnic Nasarawa.

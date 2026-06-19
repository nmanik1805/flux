# Flux Creatives — Advertising Company Web App

A full-stack Python (Flask) + HTML web application for an AI advertising company,
with a public-facing portfolio site, customer request form, and admin console.

---

## Tech Stack
- **Backend:** Python 3 + Flask
- **Database:** MongoDB
- **Frontend:** HTML5 + CSS3 + Vanilla JS (no heavy frameworks)
- **Auth:** Session-based admin authentication (Werkzeug password hashing)

---

## Project Structure
```
ai_advert_app/
├── app.py                   # Main Flask application
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── templates/
    ├── index.html           # Public website (portfolio + request form)
    ├── admin_login.html     # Admin login page
    └── admin_dashboard.html # Admin console (projects + user management)
```

---

## Setup Instructions

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Start MongoDB
Make sure MongoDB is running on `localhost:27017` (default), or set the env variable:
```bash
export MONGO_URI="mongodb://your-mongo-host:27017/"
```

### 3. (Optional) Set a custom secret key
```bash
export SECRET_KEY="your-very-secret-key-here"
```

### 4. Run the application
```bash
python app.py
```

The app runs on **http://localhost:5000** by default.

---

## Pages

| URL                  | Description                              |
|----------------------|------------------------------------------|
| `/`                  | Public website with portfolio & request form |
| `/admin/login`       | Admin login page                         |
| `/admin`             | Admin dashboard (requires login)         |

---

## Default Admin Credentials
```
Username: admin
Password: admin123
```
**⚠️ Change this immediately after first login via User Management.**

---

## Admin Features

### Projects Tab
- **Active Projects** — shows all requests where status ≠ `completed`
- **All Projects** — shows every request
- Inline dropdowns to update **Status** and **Assignee** without opening a modal
- Edit button opens a modal for status/assignee changes
- Delete button with confirmation
- Eye button to view full project details

### Status Values
`New` → `Discussion` → `Draft` → `Confirmation` → `Payment` → `Completed`

### Assignee Values
`CRM`, `Dev1`, `Dev2`

### User Management (Super Admin only)
- View all admin users
- Add new users with role (Admin / Super Admin)
- Reset passwords
- Delete users (cannot delete own account)

---

## Customer Request Form Fields
| Field           | Type     | Notes                          |
|-----------------|----------|--------------------------------|
| Requestor Name  | Text     | Required                       |
| Company Name    | Text     | Required                       |
| Email           | Email    | Required, validated            |
| Phone Number    | Number   | Required, exactly 10 digits    |
| How Contacted   | Dropdown | Google Search / Social Media / Referral / Other |
| Requirement     | Textarea | Required                       |

On submit, MongoDB stores the record with:
- `status: "New"`
- `assignee: null`
- `created_at`, `updated_at` timestamps

---

## Environment Variables

| Variable    | Default                        | Description            |
|-------------|--------------------------------|------------------------|
| `MONGO_URI` | `mongodb://localhost:27017/`   | MongoDB connection URI |
| `SECRET_KEY`| `advert-ai-secret-2025`        | Flask session key      |

---

## MongoDB Collections (auto-created)

| Collection          | Description                 |
|---------------------|-----------------------------|
| `customer_requests` | All customer request forms  |
| `admin_users`       | Admin user accounts         |

# Vutto Bike Auction Platform

A full-stack, real-time motorcycle auction platform built as part of the Vutto Software Engineering Internship Assignment.

This application allows users to browse verified used motorcycles, participate in live, real-time auctions, and seamlessly place bids. The platform features an aesthetic, dynamic, and responsive user interface, paired with a robust backend.

---

## 🛠️ Tech Stack

### Frontend
- **React (Vite)**: Lightning-fast frontend tooling and component-based architecture.
- **Vanilla CSS (Custom Design System)**: A comprehensive, premium design system featuring glassmorphism, responsive grid layouts, hardware-accelerated animations, and a cohesive vibrant color palette.
- **WebSockets**: Native browser WebSocket API for real-time bid updates.
- **React Router v6**: Client-side routing.

### Backend
- **Django & Django REST Framework (DRF)**: High-performance Python backend for the core API and business logic.
- **Django Channels**: Asynchronous WebSocket support for real-time, low-latency live auctions.
- **SQLite**: Default lightweight database for easy local setup.
- **SimpleJWT**: Secure JSON Web Token authentication.

---

## ✨ Key Features Implemented

1. **User Authentication System**: Registration, login, and secure JWT-based authentication.
2. **Live Bidding via WebSockets**: Real-time push updates for bids across all connected clients. No polling required!
3. **Advanced Auction Logic**:
   - Auctions dynamically switch from `SCHEDULED` to `ACTIVE` to `COMPLETED` based on time.
   - Minimum bid increments are enforced.
   - Users cannot bid on their own auctions.
   - Anti-sniping logic (optional extension capability built-in).
4. **Premium UI/UX**:
   - Modern, dark-mode racing aesthetic.
   - High-performance scrolling and CSS hardware acceleration.
   - Toast notifications for system events and WebSocket updates.
5. **Database Seeding**: A custom Django management command that instantly populates the platform with realistic bikes, active/completed auctions, users, and bids using high-quality Wikimedia Commons images.

---

## 🚀 Local Setup Instructions

Follow these steps to run the platform on your local machine.

### 1. Backend Setup

Open a terminal and navigate to the backend directory:
```bash
cd backend
```

Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run database migrations:
```bash
python manage.py makemigrations accounts auctions
python manage.py migrate
```

Seed the database with test data (Users, Bikes, Auctions, Bids):
```bash
python manage.py seed_data
```

Start the Django Development Server:
```bash
python manage.py runserver
```
*The backend API will run at http://127.0.0.1:8000*

### 2. Frontend Setup

Open a **new** terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the Vite Development Server:
```bash
npm run dev
```
*The frontend will run at http://localhost:5173*

---

## 👥 Demo Accounts

If you ran the `seed_data` command, the following test users are available:

| Role / User | Email | Password |
| :--- | :--- | :--- |
| **Admin/Seller** | `admin@vutto.com` | `admin123` |
| **Buyer 1** | `buyer1@test.com` | `buyer123` |
| **Buyer 2** | `buyer2@test.com` | `buyer123` |
| **Buyer 3** | `buyer3@test.com` | `buyer123` |

*Tip: To test the real-time WebSocket functionality, open two different browsers (or one Incognito window), log in as two different buyers, and bid on the same active auction!*

---

## 🧪 Running Tests

The backend includes a comprehensive Pytest test suite covering serializers, models, views, and WebSocket consumers.

To run the tests:
```bash
cd backend
pytest
```

---

## 🏗️ Architecture & Design Document

### System Architecture
The application follows a standard **Client-Server architecture** with a decoupled frontend and backend, communicating via RESTful HTTP APIs and persistent WebSocket connections.

* **Frontend Layer**: A React Single Page Application (SPA) built with Vite. It manages client-side state, handles user interactions, and renders dynamic UI components based on real-time data feeds.
* **Backend Layer**: A monolithic Django application exposing endpoints via Django REST Framework (DRF). 
* **Real-time Layer**: Django Channels, utilizing ASGI, handles long-lived WebSocket connections to push bid updates and timer events to connected clients instantaneously.
* **Data Layer**: SQLite (development) stores relational data (Users, Bikes, Auctions, Bids). 

### Database Schema (Core Models)
1. **User**: Custom user model extending Django's AbstractUser. Handles authentication and role-based access.
2. **Bike**: Represents the physical asset. Contains details like make, model, year, and images.
3. **Auction**: The core bidding entity. Links a Bike to a Seller (User). Tracks status (Scheduled, Active, Completed), reserve price, and timestamps.
4. **Bid**: A transactional record linking a Buyer (User) to an Auction, including the bid amount and timestamp.

---

## 🚀 Deployment Instructions

### Prerequisites
* A cloud provider (e.g., AWS, DigitalOcean, Heroku, or Render).
* A production-ready database (e.g., PostgreSQL).
* Redis (required for Django Channels channel layer in production).

### Backend Deployment (General Steps)
1. **Database**: Swap SQLite for PostgreSQL by updating the `DATABASES` setting in `settings.py`.
2. **Redis Layer**: Install `channels-redis` and configure the `CHANNEL_LAYERS` in `settings.py` to point to your Redis instance. This allows WebSockets to scale across multiple worker nodes.
3. **ASGI Server**: Deploy the backend using an ASGI server like **Daphne** or **Uvicorn** (Gunicorn cannot handle WebSockets natively without an ASGI worker class).
4. **Static Files**: Run `python manage.py collectstatic` and serve static files via Nginx, AWS S3, or WhiteNoise.

### Frontend Deployment
1. Update the `VITE_API_URL` and `VITE_WS_URL` environment variables in the frontend to point to your production backend domains.
2. Run the build command:
   ```bash
   npm run build
   ```
3. Deploy the generated `dist/` folder to a static hosting service like Vercel, Netlify, or AWS S3/CloudFront.

---

## ⚖️ Assumptions & Trade-offs

1. **Vanilla CSS vs. Frameworks**: 
   * *Trade-off*: Decided to use Vanilla CSS to build a custom, premium design system from scratch rather than relying on Bootstrap or TailwindCSS. 
   * *Reasoning*: This provided maximum control over custom micro-animations (e.g., 3D hover effects, glassmorphism) to achieve a "WOW" factor, at the cost of slightly more verbose stylesheets.

2. **SQLite for Development**: 
   * *Assumption*: SQLite is sufficient for the prototype and internship assignment evaluation.
   * *Trade-off*: In memory channel layers are used instead of Redis for WebSockets. This limits the app to a single process locally. For production, PostgreSQL and Redis must be swapped in.

3. **Optimistic UI Updates vs. Server Truth**: 
   * *Trade-off*: When a user places a bid, the UI explicitly waits for the WebSocket broadcast or API response before updating the "Current Bid" amount, rather than doing an optimistic UI update.
   * *Reasoning*: In high-frequency auctions, optimistic updates can lead to severe UI desync if multiple users bid simultaneously. Relying on the server's WebSocket broadcast as the single source of truth ensures all clients see the exact same state.

4. **Image Storage**: 
   * *Assumption*: For the prototype, bikes are seeded using direct URLs to Wikimedia Commons rather than handling local file uploads.
   * *Reasoning*: This avoids the complexity of configuring AWS S3 or local media storage and keeps the repository lightweight while still providing high-quality, realistic bike images for the UI.

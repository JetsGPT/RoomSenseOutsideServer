# RoomSense Outside Server

A full-stack secure gateway, proxy, and web frontend for the RoomSense application. 

This project consists of a FastAPI backend with Supabase authentication and a React frontend. The server acts as an outside gateway that proxies requests to local RoomSense boxes via WebSockets, manages user-to-box assignments, and features a robust notification relay system.

## 🌟 Features

### Backend (FastAPI)
- 🔒 **HTTPS Support:** Secure API with SSL/TLS encryption for all traffic.
- 🔐 **Supabase Authentication:** Secure user registration, login, and profile management.
- 📡 **WebSocket Gateway:** Real-time proxying of requests (`/proxy/{box_id}/*`) to local RoomSense servers using WebSockets.
- 📦 **Box Management:** Claim unclaimed boxes, assign access to other users, and view server statuses.
- 🔔 **Notification Relay System:** Centralized notification routing (ntfy, email, SMS) with logging and server-specific configurations.
- 📖 **Auto-generated API Docs:** Interactive documentation available at `/docs`.

### Frontend (React)
- ⚛️ **Modern React Stack:** Built with React 19, Vite, and React Router.
- 🖥️ **Dashboard Interface:** Manage your boxes, check statuses, and configure settings.
- 📊 **Notification Center:** View and manage server alerts and logs.
- 🛠️ **Demo Mode:** A built-in mock server to test UI layouts without spinning up the full database.

---

## 📋 Prerequisites

- **Python 3.12+**
- **Node.js 18+** (for the React frontend)
- **Supabase Account** (for database and auth)
- **OpenSSL** (for generating local HTTPS certificates)

---

## 🚀 Quick Start Setup

### 1. Clone the Repository

```bash
git clone [https://github.com/JetsGPT/RoomSenseOutsideServer.git](https://github.com/JetsGPT/RoomSenseOutsideServer.git)
cd RoomSenseOutsideServer

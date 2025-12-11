# RoomSense Outside Server

FastAPI server with Supabase authentication for the RoomSense application.

## Features

- 🔒 **HTTPS Support** - Secure API with SSL/TLS encryption
- 🔐 **Supabase Authentication** - User registration and login with secure password hashing
- 📊 **Automatic User Management** - Database triggers for user data synchronization
- 📖 **Auto-generated API Documentation** - Interactive docs at `/docs`

## Prerequisites

- Python 3.12+
- Supabase account and project
- OpenSSL (for HTTPS certificates)

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/JetsGPT/RoomSenseOutsideServer.git
cd RoomSenseOutsideServer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

Get these values from your [Supabase Dashboard](https://supabase.com/dashboard) → Project Settings → API.

### 4. Set Up Database

Run this SQL in your Supabase SQL Editor to create the users table and triggers:

```sql
-- Create users table
CREATE TABLE IF NOT EXISTS public.users (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  username TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own profile
CREATE POLICY "Users can view own profile"
  ON public.users FOR SELECT
  USING (auth.uid() = id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
  ON public.users FOR UPDATE
  USING (auth.uid() = id);

-- Function that runs when a new user is created in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.users (id, email, username, created_at)
  VALUES (
    new.id,
    new.email,
    new.raw_user_meta_data->>'username',
    new.created_at
  );
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger that calls the function after INSERT on auth.users
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

### 5. Generate SSL Certificates

For HTTPS support, generate self-signed certificates:

```bash
pip install pyOpenSSL
python -c "from OpenSSL import crypto; k=crypto.PKey(); k.generate_key(crypto.TYPE_RSA, 2048); cert=crypto.X509(); cert.get_subject().CN='localhost'; cert.set_serial_number(1000); cert.gmtime_adj_notBefore(0); cert.gmtime_adj_notAfter(365*24*60*60); cert.set_issuer(cert.get_subject()); cert.set_pubkey(k); cert.sign(k, 'sha256'); open('cert.pem', 'wb').write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert)); open('key.pem', 'wb').write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))"
```

## Running the Server

### Development Mode (HTTPS)

```bash
python main.py
```

Server will run at: **https://localhost:8443**

### Development Mode (HTTP - FastAPI CLI)

```bash
fastapi dev fastapi_code.py
```

Server will run at: **http://localhost:8000**

## API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "running"
}
```

### `POST /register`
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "username": "johndoe"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user": { ... }
}
```

### `POST /login`
Authenticate a user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Login successful",
  "access_token": "...",
  "user_id": "..."
}
```

## API Documentation

Interactive API documentation is automatically available at:
- Swagger UI: **https://localhost:8443/docs**
- ReDoc: **https://localhost:8443/redoc**

## Project Structure

```
RoomSenseOutsideServer/
├── main.py              # HTTPS server entry point
├── fastapi_code.py      # FastAPI application and routes
├── supabase_code.py     # Supabase client initialization and auth functions
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .gitignore          # Git ignore rules
├── cert.pem            # SSL certificate (generated, not in git)
├── key.pem             # SSL private key (generated, not in git)
└── README.md           # This file
```

## Security Notes

- ⚠️ Self-signed certificates will show browser warnings - this is normal for development
- 🔒 Passwords are automatically hashed by Supabase Auth - never stored in plain text
- 🛡️ Row Level Security (RLS) is enabled to protect user data
- 🚫 Never commit `.env`, `cert.pem`, or `key.pem` to version control

## Production Deployment

For production, use:
- A proper SSL certificate from Let's Encrypt or a certificate authority
- A reverse proxy like Nginx or Caddy
- Environment variables configured in your hosting platform
- Consider platforms like Railway, Render, or Fly.io for easy deployment

## Troubleshooting

### Module not found errors
```bash
pip install --upgrade -r requirements.txt
```

### Certificate errors
Regenerate certificates:
```bash
rm cert.pem key.pem
# Then run the certificate generation command again
```

### Supabase connection errors
- Verify your `.env` file has correct `SUPABASE_URL` and `SUPABASE_KEY`
- Check your Supabase project is active
- Ensure your API key has the correct permissions

## License

MIT License

## Contributing

Pull requests are welcome! Please open an issue first to discuss proposed changes.

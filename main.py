import uvicorn
from pathlib import Path

if __name__ == "__main__":
    # SSL certificate paths
    cert_dir = Path(__file__).parent / "certs"
    ssl_keyfile = cert_dir / "privkey.pem"
    ssl_certfile = cert_dir / "fullchain.pem"
    
    # Check if certificates exist
    if not ssl_keyfile.exists() or not ssl_certfile.exists():
        print("\n" + "="*70)
        print("⚠️  SSL certificates not found!")
        print("="*70)
        print("\nTo generate self-signed certificates, run these commands:")
        print("\n1. Install OpenSSL (if not already installed):")
        print("   winget install OpenSSL.Light")
        print("\n2. Generate certificate and key:")
        print(f'   openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365 -subj "/CN=localhost"')
        print("\n" + "="*70 + "\n")
        exit(1)
    
    print("\n" + "="*70)
    print("🔒 Starting FastAPI server with HTTPS")
    print("="*70)
    print(f"📍 Server URL: https://localhost:8443")
    print(f"📖 API Docs: https://localhost:8443/docs")
    print("⚠️  Your browser will show a security warning - click 'Advanced' and proceed")
    print("="*70 + "\n")
    
    # Run FastAPI with HTTPS
    uvicorn.run(
        "fastapi_code:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile=str(ssl_keyfile),
        ssl_certfile=str(ssl_certfile),
        reload=True
    )

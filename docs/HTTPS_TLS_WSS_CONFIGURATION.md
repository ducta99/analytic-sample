# HTTPS/TLS and WSS Configuration Guide

Complete guide for implementing SSL/TLS certificates, HTTPS encryption, and secure WebSocket (WSS) connections across the microservices architecture.

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** January 2025

## Table of Contents

1. [SSL/TLS Overview](#ssltls-overview)
2. [Certificate Generation](#certificate-generation)
3. [Kubernetes Ingress Configuration](#kubernetes-ingress-configuration)
4. [API Gateway Setup](#api-gateway-setup)
5. [WebSocket Configuration](#websocket-configuration)
6. [Frontend Configuration](#frontend-configuration)
7. [Certificate Renewal](#certificate-renewal)
8. [Testing & Validation](#testing--validation)
9. [Troubleshooting](#troubleshooting)

---

## SSL/TLS Overview

### 1. HTTP vs HTTPS

```
HTTP (Unencrypted)
━━━━━━━━━━━━━━━━━━
Client → Server: GET /api/data
                 (credentials visible)

Server → Client: {"token": "sensitive_data"}
                 (data visible to anyone on network)


HTTPS (Encrypted with TLS 1.3)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Client → Server: [ENCRYPTED] GET /api/data
                 (credentials encrypted)

Server → Client: [ENCRYPTED] {"token": "..."}
                 (only client can decrypt)
```

### 2. TLS 1.3 Handshake

```
1. Client Hello
   - Supported TLS versions
   - Cipher suites
   - Random nonce

2. Server Hello + Certificate
   - Selected TLS version (1.3)
   - Certificate (public key)
   - Server nonce

3. Client Verifies Certificate
   - Check certificate chain
   - Verify domain matches
   - Check expiration

4. Shared Secret Established
   - Symmetric encryption key derived
   - All further communication encrypted

5. Encrypted Data Exchange
   ✅ All data encrypted with AES-256
```

### 3. Certificate Types

| Type | Use Case | Cost | Validation |
|------|----------|------|-----------|
| Self-Signed | Development/Testing | Free | ❌ Not trusted |
| Let's Encrypt | Production HTTP | Free | ✅ Trusted, 90-day renewal |
| Commercial CA | Production Enterprise | $ | ✅ Trusted, longer validity |
| Wildcard | Multiple Subdomains | $$ | ✅ *.example.com |

---

## Certificate Generation

### 1. Development: Self-Signed Certificates

**Generate self-signed certificate (valid for 365 days):**

```bash
#!/bin/bash
# scripts/generate-self-signed-cert.sh

set -e

CERT_DIR="certs"
DOMAIN="${1:-localhost}"
DAYS="${2:-365}"

mkdir -p "$CERT_DIR"

echo "Generating self-signed certificate for: $DOMAIN"

# Generate private key (2048-bit RSA)
openssl genrsa -out "$CERT_DIR/${DOMAIN}.key" 2048

# Generate certificate signing request
openssl req -new \
  -key "$CERT_DIR/${DOMAIN}.key" \
  -out "$CERT_DIR/${DOMAIN}.csr" \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"

# Self-sign the certificate
openssl x509 -req \
  -days "$DAYS" \
  -in "$CERT_DIR/${DOMAIN}.csr" \
  -signkey "$CERT_DIR/${DOMAIN}.key" \
  -out "$CERT_DIR/${DOMAIN}.crt"

# Create PEM file (contains both cert and key)
cat "$CERT_DIR/${DOMAIN}.crt" "$CERT_DIR/${DOMAIN}.key" > "$CERT_DIR/${DOMAIN}.pem"

# Display certificate info
echo -e "\n✅ Certificate generated:"
openssl x509 -in "$CERT_DIR/${DOMAIN}.crt" -noout -text | grep -E "Subject:|Not Before|Not After|Public-Key"

echo -e "\nCertificates created:"
echo "  - $CERT_DIR/${DOMAIN}.key (Private Key)"
echo "  - $CERT_DIR/${DOMAIN}.crt (Certificate)"
echo "  - $CERT_DIR/${DOMAIN}.pem (PEM - combined)"
```

Run:
```bash
chmod +x scripts/generate-self-signed-cert.sh

# For localhost
./scripts/generate-self-signed-cert.sh localhost 365

# For domain
./scripts/generate-self-signed-cert.sh analytics.example.com 365
```

Output:
```
Generating self-signed certificate for: localhost

✅ Certificate generated:
        Subject: C = US, ST = State, L = City, O = Organization, CN = localhost
        Not Before: Jan  1 00:00:00 2025 GMT
        Not After : Jan  1 00:00:00 2026 GMT
        Public-Key: (2048 bit)

Certificates created:
  - certs/localhost.key (Private Key)
  - certs/localhost.crt (Certificate)
  - certs/localhost.pem (PEM - combined)
```

### 2. Production: Let's Encrypt Certificates

**Using Certbot to generate Let's Encrypt certificate:**

```bash
#!/bin/bash
# scripts/generate-letsencrypt-cert.sh

set -e

DOMAIN="${1:-analytics.example.com}"
EMAIL="${2:-admin@example.com}"

echo "Generating Let's Encrypt certificate for: $DOMAIN"

# Install certbot if needed
# sudo apt-get install certbot python3-certbot-nginx

# Generate certificate (non-interactive)
# This assumes you've set up DNS validation or HTTP challenge
sudo certbot certonly \
  --standalone \
  --agree-tos \
  --email "$EMAIL" \
  -d "$DOMAIN" \
  -d "www.$DOMAIN"

echo "✅ Certificate generated"
echo "Cert: /etc/letsencrypt/live/$DOMAIN/fullchain.pem"
echo "Key: /etc/letsencrypt/live/$DOMAIN/privkey.pem"
```

### 3. Certificate Verification

```bash
# View certificate details
openssl x509 -in certs/localhost.crt -noout -text

# Check certificate expiration
openssl x509 -in certs/localhost.crt -noout -dates
# Output:
# notBefore=Jan  1 00:00:00 2025 GMT
# notAfter=Jan  1 00:00:00 2026 GMT

# Test certificate chain
openssl verify -CAfile certs/ca.crt certs/localhost.crt

# Check private key
openssl rsa -in certs/localhost.key -check -noout
```

---

## Kubernetes Ingress Configuration

### 1. Create TLS Secret in Kubernetes

```bash
# Create secret from certificate files
kubectl create secret tls api-tls-secret \
  --cert=certs/localhost.crt \
  --key=certs/localhost.key \
  -n analytics

# Verify secret
kubectl get secret api-tls-secret -n analytics -o yaml

# Output:
# apiVersion: v1
# kind: Secret
# metadata:
#   name: api-tls-secret
#   namespace: analytics
# type: kubernetes.io/tls
# data:
#   tls.crt: [base64-encoded-cert]
#   tls.key: [base64-encoded-key]
```

### 2. Update Ingress for HTTPS

**k8s/03-ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: analytics
  annotations:
    # TLS configuration
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"  # For production
    
    # Security headers
    nginx.ingress.kubernetes.io/ssl-protocols: "TLSv1.2 TLSv1.3"
    nginx.ingress.kubernetes.io/ssl-ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
    
    # Redirect HTTP to HTTPS
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    
    # Security headers
    nginx.ingress.kubernetes.io/configuration-snippet: |
      more_set_headers "Strict-Transport-Security: max-age=31536000; includeSubDomains; preload";
      more_set_headers "X-Frame-Options: DENY";
      more_set_headers "X-Content-Type-Options: nosniff";
      more_set_headers "X-XSS-Protection: 1; mode=block";

spec:
  # TLS Configuration
  tls:
  - hosts:
    - analytics.example.com
    - www.analytics.example.com
    - api.analytics.example.com
    secretName: api-tls-secret  # Reference to TLS secret

  rules:
  # HTTPS Rules
  - host: api.analytics.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000

  - host: analytics.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000

---
# HTTP to HTTPS Redirect Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: http-redirect
  namespace: analytics
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

spec:
  rules:
  - host: analytics.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000

  - host: api.analytics.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

Deploy:
```bash
kubectl apply -f k8s/03-ingress.yaml

# Verify ingress
kubectl get ingress -n analytics
kubectl describe ingress api-ingress -n analytics
```

### 3. Cert-Manager for Automatic Renewal (Production)

**Install cert-manager:**

```bash
# Add helm repository
helm repo add jetstack https://charts.jetstack.io

# Install cert-manager
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Verify
kubectl get pods -n cert-manager
```

**Create ClusterIssuer for Let's Encrypt:**

```yaml
# k8s/cert-issuer.yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx

---
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-staging
    solvers:
    - http01:
        ingress:
          class: nginx
```

Deploy:
```bash
kubectl apply -f k8s/cert-issuer.yaml

# Cert-manager will automatically renew certificates before expiration
# Monitor certificate status
kubectl describe certificate api-tls-secret -n analytics
```

---

## API Gateway Setup

### 1. FastAPI with HTTPS (Development)

**api-gateway/app/main.py:**

```python
from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Production: HTTPS with cert-manager managed certificates
        # Run behind Kubernetes Ingress (no SSL config needed here)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
        )
    else:
        # Development: Self-signed certificates
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8443,
            ssl_keyfile="certs/localhost.key",
            ssl_certfile="certs/localhost.crt",
            ssl_keyfile_password=None,
            ssl_version=17,  # TLS 1.3
        )
```

Run:
```bash
# Development (HTTPS)
python -m uvicorn api-gateway.app.main:app \
  --ssl-keyfile=certs/localhost.key \
  --ssl-certfile=certs/localhost.crt \
  --ssl-version=17

# Production (plain HTTP behind Ingress)
python -m uvicorn api-gateway.app.main:app --host 0.0.0.0 --port 8000
```

### 2. Docker Configuration

**api-gateway/Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy source
COPY app/ ./app/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)"

# Run API Gateway (plain HTTP - Ingress handles TLS)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Docker Compose for Development

**docker-compose.yml (HTTPS support):**

```yaml
version: '3.8'

services:
  api-gateway:
    build: ./api-gateway
    ports:
      - "8443:8443"  # HTTPS
      - "8000:8000"  # HTTP (for health checks)
    environment:
      ENVIRONMENT: development
      SSL_CERTFILE: /certs/localhost.crt
      SSL_KEYFILE: /certs/localhost.key
    volumes:
      - ./certs:/certs:ro  # Mount certificates (read-only)
    command: >
      uvicorn app.main:app
      --host 0.0.0.0
      --port 8443
      --ssl-certfile /certs/localhost.crt
      --ssl-keyfile /certs/localhost.key
      --ssl-version 17

  # Other services (HTTP behind docker network)
  user-service:
    build: ./user-service
    ports:
      - "8001:8001"
    environment:
      ENVIRONMENT: development
```

---

## WebSocket Configuration

### 1. WebSocket Protocol

```
HTTP → WebSocket Upgrade
━━━━━━━━━━━━━━━━━━━━━━

Client Request:
GET /ws?token=eyJ... HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: ...

Server Response (101 Switching Protocols):
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: ...

➜ Persistent connection established
➜ Can be upgraded to WSS (WebSocket over TLS)
```

### 2. FastAPI WebSocket with WSS

**api-gateway/app/websocket.py:**

```python
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import asyncio
from typing import Dict, Set
from app.auth import verify_token

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)

    async def broadcast(self, message: dict, channel: str):
        if channel in self.active_connections:
            # Send to all subscribers of this channel
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting: {e}")

manager = ConnectionManager()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time price updates.
    
    Query parameters:
    - token: JWT token for authentication
    - channels: Comma-separated list of channels (prices, portfolio, sentiment)
    - coins: Comma-separated list of coins to subscribe to
    
    Example:
    wss://api.example.com/ws?token=eyJ...&channels=prices&coins=bitcoin,ethereum
    """
    
    try:
        # Get token from query parameters
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return
        
        # Verify token
        user = await verify_token(token)
        if not user:
            await websocket.close(code=4003, reason="Invalid token")
            return
        
        # Accept connection
        await websocket.accept()
        
        # Get subscription parameters
        channels = websocket.query_params.get("channels", "prices").split(",")
        coins = websocket.query_params.get("coins", "bitcoin").split(",")
        
        print(f"✅ WebSocket connected: user={user.id}, channels={channels}, coins={coins}")
        
        # Handle incoming messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("action") == "subscribe":
                # Subscribe to specific channel and coins
                channel = message.get("channel", "prices")
                new_coins = message.get("coins", [])
                coins.extend(new_coins)
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel,
                    "coins": coins
                })
            
            elif message.get("action") == "unsubscribe":
                # Unsubscribe from channel
                channel = message.get("channel")
                await manager.disconnect(websocket, channel)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "channel": channel
                })
            
            elif message.get("action") == "ping":
                # Respond to ping (keep-alive)
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"❌ WebSocket disconnected: user={getattr(user, 'id', 'unknown')}")
        # Cleanup handled automatically
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await websocket.close(code=1000)
```

### 3. WebSocket Ingress Configuration for WSS

**Update k8s/03-ingress.yaml:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: analytics
  annotations:
    kubernetes.io/ingress.class: "nginx"
    
    # WebSocket support
    nginx.ingress.kubernetes.io/websocket-services: "api-gateway"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-connection-timeout: "3600"
    
    # TLS/SSL
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"

spec:
  tls:
  - hosts:
    - api.analytics.example.com
    secretName: api-tls-secret

  rules:
  - host: api.analytics.example.com
    http:
      paths:
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
      
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api-gateway
            port:
              number: 8000
```

---

## Frontend Configuration

### 1. Update Frontend API Client

**frontend/src/utils/api-client.ts:**

```typescript
import axios, { AxiosInstance } from 'axios';

/**
 * API client with automatic HTTPS/WSS protocol selection
 */
class APIClient {
  private baseURL: string;
  private wsBaseURL: string;
  private axiosInstance: AxiosInstance;

  constructor() {
    // Determine protocol based on current window location
    const isSecure = window.location.protocol === 'https:';
    
    // REST API base URL
    this.baseURL = isSecure
      ? `https://${window.location.host}`
      : `http://${window.location.host}`;
    
    // WebSocket base URL
    this.wsBaseURL = isSecure
      ? `wss://${window.location.host}`
      : `ws://${window.location.host}`;
    
    // Create axios instance
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Add JWT token to all requests
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Get REST API base URL
   */
  getBaseURL(): string {
    return this.baseURL;
  }

  /**
   * Get WebSocket base URL
   */
  getWSBaseURL(): string {
    return this.wsBaseURL;
  }

  /**
   * Make HTTP request
   */
  async request<T = any>(
    method: string,
    path: string,
    data?: any,
    config?: any
  ): Promise<T> {
    return this.axiosInstance({
      method,
      url: path,
      data,
      ...config,
    }).then((res) => res.data);
  }

  /**
   * Connect to WebSocket
   */
  connectWebSocket(channels: string[], coins: string[]): WebSocket {
    const token = localStorage.getItem('access_token');
    const params = new URLSearchParams({
      token: token || '',
      channels: channels.join(','),
      coins: coins.join(','),
    });
    
    const wsURL = `${this.wsBaseURL}/ws?${params}`;
    console.log(`Connecting to WebSocket: ${wsURL}`);
    
    return new WebSocket(wsURL);
  }
}

export const apiClient = new APIClient();
```

### 2. Frontend WebSocket Hook

**frontend/src/hooks/useWebSocket.ts:**

```typescript
import { useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { apiClient } from '../utils/api-client';
import { updatePrices } from '../store/slices/prices';

export const useWebSocket = (channels: string[], coins: string[]) => {
  const wsRef = useRef<WebSocket | null>(null);
  const dispatch = useDispatch();

  useEffect(() => {
    // Connect to WebSocket
    wsRef.current = apiClient.connectWebSocket(channels, coins);

    // Handle connection open
    wsRef.current.onopen = () => {
      console.log('✅ WebSocket connected');
      dispatch(updatePrices([])); // Signal connection established
    };

    // Handle incoming messages
    wsRef.current.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'price_update') {
          // Update prices in Redux
          dispatch(updatePrices(message.data));
        } else if (message.type === 'subscribed') {
          console.log('✅ Subscribed to channels:', message.channel);
        } else if (message.type === 'pong') {
          console.log('Pong received (keep-alive)');
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    // Handle connection close
    wsRef.current.onclose = () => {
      console.log('❌ WebSocket disconnected');
      // Attempt reconnect after 5 seconds
      setTimeout(() => {
        useWebSocket(channels, coins);
      }, 5000);
    };

    // Handle errors
    wsRef.current.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [channels, coins, dispatch]);

  return wsRef.current;
};
```

### 3. Next.js Environment Configuration

**frontend/.env.production:**

```
# Production environment uses HTTPS/WSS automatically
# No protocol configuration needed - determined by window.location

NEXT_PUBLIC_API_URL=https://api.analytics.example.com
NEXT_PUBLIC_WS_URL=wss://api.analytics.example.com

# Will be automatically switched to:
# - HTTP/WS in development
# - HTTPS/WSS in production
```

### 4. next.config.js Update

```javascript
// frontend/next.config.js

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Force HTTPS headers in production
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },

  // Redirect HTTP to HTTPS in production
  async redirects() {
    if (process.env.NODE_ENV === 'production') {
      return [
        {
          source: '/:path*',
          destination: 'https://analytics.example.com/:path*',
          permanent: true,
          basePath: false,
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
```

---

## Certificate Renewal

### 1. Automatic Renewal with Cert-Manager

```bash
# Cert-manager automatically renews certificates 30 days before expiration
# No manual action required

# Monitor renewal status
kubectl describe certificate api-tls-secret -n analytics

# Output:
# Status:
#   Conditions:
#     Type       Status  LastProbeTime
#     -----      ------  -----
#     Ready      True    2025-01-15T12:34:56Z
#   Renewal Time: 2025-01-31T12:00:00Z
```

### 2. Manual Renewal for Let's Encrypt

```bash
#!/bin/bash
# scripts/renew-letsencrypt-cert.sh

DOMAIN="analytics.example.com"

# Renew certificate
sudo certbot renew --cert-name "$DOMAIN" --force-renewal

# Update Kubernetes secret
kubectl create secret tls api-tls-secret \
  --cert=/etc/letsencrypt/live/$DOMAIN/fullchain.pem \
  --key=/etc/letsencrypt/live/$DOMAIN/privkey.pem \
  -n analytics \
  --dry-run=client -o yaml | kubectl apply -f -

# Rollout restart to pick up new certificate
kubectl rollout restart ingress -n analytics
```

### 3. Certificate Expiration Monitoring

```python
# scripts/monitor_certificates.py
"""Monitor certificate expiration dates"""

import subprocess
import json
from datetime import datetime, timedelta

def get_certificate_expiration(cert_file):
    """Get certificate expiration date"""
    cmd = f"openssl x509 -in {cert_file} -noout -dates"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if 'notAfter' in line:
            date_str = line.split('=')[1]
            return datetime.strptime(date_str, '%b %d %H:%M:%S %Y %Z')
    return None

def check_expiration(cert_file, warning_days=30):
    """Check if certificate is expiring soon"""
    expiration = get_certificate_expiration(cert_file)
    if not expiration:
        return None
    
    days_until_expiration = (expiration - datetime.now()).days
    
    if days_until_expiration < 0:
        return {"status": "EXPIRED", "days": days_until_expiration}
    elif days_until_expiration < warning_days:
        return {"status": "WARNING", "days": days_until_expiration}
    else:
        return {"status": "OK", "days": days_until_expiration}

# Monitor certificates
certs = [
    "certs/localhost.crt",
    "/etc/letsencrypt/live/analytics.example.com/fullchain.pem",
]

for cert in certs:
    result = check_expiration(cert)
    if result:
        status = result["status"]
        days = result["days"]
        emoji = "✅" if status == "OK" else "⚠️" if status == "WARNING" else "❌"
        print(f"{emoji} {cert}: {status} ({days} days)")
```

---

## Testing & Validation

### 1. HTTPS Connection Test

```bash
#!/bin/bash
# scripts/test-https.sh

echo "=== HTTPS/TLS Testing ==="

API_URL="https://api.analytics.example.com"

# Test 1: Check certificate
echo -e "\n[Test 1] Certificate Details"
openssl s_client -connect api.analytics.example.com:443 -servername api.analytics.example.com \
  </dev/null | openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not Before|Not After"

# Test 2: Check TLS version
echo -e "\n[Test 2] TLS Version"
echo | openssl s_client -connect api.analytics.example.com:443 -tls1_3 2>/dev/null | grep "Protocol"

# Test 3: Check cipher suite
echo -e "\n[Test 3] Cipher Suite"
echo | openssl s_client -connect api.analytics.example.com:443 2>/dev/null | grep "Cipher"

# Test 4: HTTP to HTTPS redirect
echo -e "\n[Test 4] HTTP to HTTPS Redirect"
curl -I http://api.analytics.example.com/ 2>/dev/null | head -1

# Test 5: HTTPS GET request
echo -e "\n[Test 5] HTTPS GET Request"
curl -s "$API_URL/health" | jq .

# Test 6: Check security headers
echo -e "\n[Test 6] Security Headers"
curl -s -I "$API_URL/health" | grep -E "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options"
```

Run:
```bash
chmod +x scripts/test-https.sh
./scripts/test-https.sh
```

### 2. WSS (Secure WebSocket) Test

```python
#!/usr/bin/env python3
# scripts/test_wss.py
"""Test secure WebSocket connection"""

import asyncio
import json
import websockets
from typing import Optional

async def test_wss_connection(
    url: str,
    token: str,
    channels: list,
    coins: list,
    timeout: int = 10
) -> bool:
    """Test WSS connection"""
    
    # Build WebSocket URL
    params = f"?token={token}&channels={','.join(channels)}&coins={','.join(coins)}"
    ws_url = f"{url}{params}"
    
    print(f"Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(
            ws_url,
            ssl=True,  # Use TLS
            ping_interval=20,  # Keep-alive ping every 20 seconds
            ping_timeout=10,
        ) as websocket:
            print("✅ WebSocket connected")
            
            # Send subscription message
            await websocket.send(json.dumps({
                "action": "subscribe",
                "channel": "prices",
                "coins": coins
            }))
            print("Subscription request sent")
            
            # Wait for messages
            start_time = asyncio.get_event_loop().time()
            messages_received = 0
            
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1)
                    data = json.loads(message)
                    messages_received += 1
                    print(f"Message received: {data.get('type', 'unknown')}")
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed")
                    break
            
            print(f"✅ Test completed ({messages_received} messages received)")
            return True
    
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    # Parse arguments
    ws_url = sys.argv[1] if len(sys.argv) > 1 else "wss://api.analytics.example.com/ws"
    token = sys.argv[2] if len(sys.argv) > 2 else "your-jwt-token"
    
    # Run test
    success = asyncio.run(test_wss_connection(
        ws_url,
        token,
        channels=["prices"],
        coins=["bitcoin", "ethereum"],
    ))
    
    sys.exit(0 if success else 1)
```

Run:
```bash
python scripts/test_wss.py wss://api.analytics.example.com/ws your_jwt_token
```

### 3. Browser Testing

```javascript
// Test in browser console

// Test 1: Check protocol
console.log(`Current protocol: ${window.location.protocol}`);
// Output: https:

// Test 2: Make HTTPS request
fetch('https://api.analytics.example.com/health')
  .then(r => r.json())
  .then(data => console.log('✅ HTTPS working:', data))
  .catch(e => console.error('❌ HTTPS error:', e));

// Test 3: Connect to WSS
const ws = new WebSocket('wss://api.analytics.example.com/ws?token=your_token');
ws.onopen = () => console.log('✅ WSS connected');
ws.onerror = (e) => console.error('❌ WSS error:', e);
ws.onclose = () => console.log('WSS closed');

// Test 4: Check security headers
fetch('https://api.analytics.example.com/health')
  .then(r => {
    console.log('Headers:');
    console.log('HSTS:', r.headers.get('Strict-Transport-Security'));
    console.log('X-Frame-Options:', r.headers.get('X-Frame-Options'));
    console.log('CSP:', r.headers.get('Content-Security-Policy'));
  });
```

---

## Troubleshooting

### Issue 1: "ERR_CERT_AUTHORITY_INVALID" (Self-Signed in Development)

```
Solution:
1. Browser: Click "Advanced" → "Proceed to localhost"
2. Or: Add to chrome flags:
   chrome://flags/#allow-insecure-localhost
3. Or: Import cert to system trust store

# Linux
sudo cp certs/localhost.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/localhost.crt

# Windows
Double-click cert → Install → Trusted Root Certification Authorities
```

### Issue 2: "Peer certificate cannot be authenticated"

```
Solution:
1. Check certificate validity:
   openssl x509 -in certs/localhost.crt -noout -dates

2. Check certificate matches domain:
   openssl x509 -in certs/localhost.crt -noout -text | grep DNS

3. Regenerate if needed:
   ./scripts/generate-self-signed-cert.sh localhost 365
```

### Issue 3: WebSocket Connection Refused

```
Solution:
1. Check WebSocket endpoint exists:
   curl -i -N \
     -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     https://api.example.com/ws

2. Check JWT token is valid:
   token=$(curl -X POST https://api.example.com/login -d '{...}')
   echo $token

3. Check Ingress allows WebSocket:
   kubectl describe ingress api-ingress -n analytics

4. Check pod logs:
   kubectl logs -l app=api-gateway -n analytics
```

### Issue 4: Certificate Not Renewing

```
Solution:
1. Check cert-manager status:
   kubectl get pods -n cert-manager

2. Check certificate status:
   kubectl describe certificate api-tls-secret -n analytics

3. Check cert-manager logs:
   kubectl logs -n cert-manager deploy/cert-manager

4. Manual renewal:
   sudo certbot renew --force-renewal
   kubectl create secret tls api-tls-secret \
     --cert=/etc/letsencrypt/live/analytics.example.com/fullchain.pem \
     --key=/etc/letsencrypt/live/analytics.example.com/privkey.pem \
     -n analytics --dry-run=client -o yaml | kubectl apply -f -
```

---

## Deployment Checklist

### Development
- [ ] Self-signed certificate generated
- [ ] Docker Compose configured with SSL volumes
- [ ] FastAPI running on HTTPS port 8443
- [ ] Frontend configured for HTTPS/WSS
- [ ] Browser certificate warning acknowledged
- [ ] WebSocket connections working

### Staging
- [ ] Let's Encrypt certificate requested
- [ ] Cert-manager installed and configured
- [ ] ClusterIssuer configured for staging
- [ ] Ingress updated with TLS configuration
- [ ] HTTP redirects to HTTPS
- [ ] Certificate renewal automated
- [ ] WebSocket WSS connections verified

### Production
- [ ] Let's Encrypt production certificate issued
- [ ] HSTS preload list verification ready
- [ ] TLS 1.3 enforced
- [ ] Strong cipher suites configured
- [ ] Certificate renewal monitored
- [ ] Backup certificate renewal scripts in place
- [ ] Load testing for TLS handshake performance
- [ ] Security headers verified on all responses
- [ ] WebSocket secure connections validated

---

**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Updated:** January 2025

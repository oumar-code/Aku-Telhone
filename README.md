# Telhone

## Overview
Telhone is a microservice in the Aku platform ecosystem. It provides core telephony and communication features for users and other services.

## Features
- REST API for telephony actions
- Scalable Node.js backend

## Getting Started

### Prerequisites
- Node.js 20+
- Docker (optional)

### Development
```bash
git clone <repo-url>
cd Telhone
npm install
npm run dev
```

### Docker
```bash
docker build -t telhone:latest .
docker run -p 8080:8080 telhone:latest
```

### Testing
```bash
npm test
```

## Deployment
See `.github/workflows/ci.yml` for CI/CD pipeline.

## License
MIT
# Aku-Telhone
## Features - REST API for telephony actions - Scalable Node.js backend

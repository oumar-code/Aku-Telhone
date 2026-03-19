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

Aku Telhone is a microservice in the Aku platform ecosystem. It provides core telephony and communication features for users and other services via a scalable Node.js REST API.

## Features

- **REST API** for telephony actions (phone numbers, calls, SMS messages)
- **Scalable Node.js backend** built with Express
- **Input validation** via Joi schemas
- **Rate limiting** to protect against abuse
- **Structured error handling** with consistent JSON responses

## Getting Started

### Prerequisites

- Node.js ≥ 18
- npm ≥ 9

### Installation

```bash
npm install
```

### Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

| Variable               | Default       | Description                        |
| ---------------------- | ------------- | ---------------------------------- |
| `PORT`                 | `3000`        | Port the HTTP server listens on    |
| `NODE_ENV`             | `development` | Runtime environment                |
| `RATE_LIMIT_WINDOW_MS` | `60000`       | Rate-limit window in milliseconds  |
| `RATE_LIMIT_MAX`       | `100`         | Max requests per window per IP     |

### Running

```bash
# Production
npm start

# Development (with auto-reload)
npm run dev
```

## API Reference

### Health Check

```
GET /health
```

Response:
```json
{ "status": "ok", "service": "aku-telhone", "timestamp": "2026-01-01T00:00:00.000Z" }
```

---

### Phone Numbers

#### List phone numbers

```
GET /api/phone-numbers
```

Response:
```json
{ "status": "ok", "count": 2, "phoneNumbers": [ { "id": "pn-0001", "number": "+14155550100", "label": "Support line", "status": "active", "createdAt": "..." } ] }
```

#### Get a phone number

```
GET /api/phone-numbers/:id
```

#### Register a phone number

```
POST /api/phone-numbers
Content-Type: application/json
```

Body:
```json
{ "number": "+19995550123", "label": "My new line" }
```

---

### Calls

#### List calls

```
GET /api/calls
```

#### Get a call

```
GET /api/calls/:id
```

#### Initiate a call

```
POST /api/calls
Content-Type: application/json
```

Body:
```json
{ "from": "+14155550100", "to": "+12125550200", "options": { "record": false } }
```

Response:
```json
{ "status": "ok", "call": { "id": "call-...", "from": "+14155550100", "to": "+12125550200", "status": "ringing", "record": false, "startedAt": "..." } }
```

#### Update a call (hold / unhold / end)

```
PATCH /api/calls/:id
Content-Type: application/json
```

Body:
```json
{ "action": "end" }
```

Valid actions: `hold`, `unhold`, `end`.

---

### Messages

#### List messages

```
GET /api/messages
```

#### Get a message

```
GET /api/messages/:id
```

#### Send a message

```
POST /api/messages
Content-Type: application/json
```

Body:
```json
{ "from": "+14155550100", "to": "+12125550200", "body": "Hello from Aku Telhone!" }
```

Response:
```json
{ "status": "ok", "message": { "id": "msg-...", "from": "+14155550100", "to": "+12125550200", "body": "Hello from Aku Telhone!", "status": "sent", "sentAt": "..." } }
```

---

## Testing

```bash
npm test
```

## Linting

```bash
npm run lint
```

## License

MIT © UMAR ABUBAKAR

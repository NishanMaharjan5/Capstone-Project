# Receipt Analyzer Frontend

React app for the FastAPI backend. This replaced the legacy static HTML frontend.

## Development

```bash
cd frontend
npm install
npm run dev
```

The app expects the backend at:

```txt
http://localhost:8000
```

Override it with `.env` (see `.env.example`):

```txt
VITE_API_BASE_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

## Production

```bash
npm run build
```

FastAPI (`backend/main.py`) serves the build from `../frontend/dist`, with a fallback to
`index.html` for client-side routes (e.g. `/history`, `/login`) so hard refreshes/direct
links don't 404.

## Scope

- React Router routes for login, register, forgot password, dashboard, and history.
- Shared API client for the FastAPI endpoints (auth + receipts).
- Auth context backed by the localStorage token flow, with Google sign-in/sign-up.
- Protected routes for dashboard and history.
- Receipt upload/OCR review, manual receipt entry, and full history (view/expand/delete) actions.

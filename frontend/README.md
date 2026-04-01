# bruv-mail Frontend

A React inbox UI for the bruv-mail backend API.

## Tech Stack

- React 18 with TypeScript
- Vite for dev/build
- React Router v6 for navigation
- TanStack Query for server state management
- Zustand for client state
- Tailwind CSS for styling

## Quick Start (Local)

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create `.env.local` from `.env.example`:

```bash
cp .env.example .env.local
```

3. Start the dev server:

```bash
npm run dev
```

The frontend will run at `http://localhost:5173` and proxy API calls to `http://localhost:8000`.

## Building

```bash
npm run build
npm run preview
```

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Current Features (Phase 1)

- Login with API token
- Inbox view with message list
- Message filtering by tag
- Pagination
- Tag aggregation sidebar

## Future Phases

- Phase 2: Advanced filters (sender, date range)
- Phase 3: Task management view
- Phase 4: Account settings management
- Phase 5: Admin token management

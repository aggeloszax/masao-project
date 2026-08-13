# Masao Frontend

Next.js menu app for Masao's multilingual digital menu and waiter chat.

## Setup

```bash
npm install
npm run dev
```

The app runs at `http://localhost:3000`.

## Scripts

```bash
npm run dev
npm run lint
npm run test
npm run build
npm run start
```

## App Structure

- `src/app/page.tsx` renders the menu experience.
- `src/components/` contains the menu UI, language selector, and chat panel.
- `src/lib/menu-api.ts` loads the public menu from `GET /api/menu`.
- `src/data/menu-mock.json` is the local fallback menu used when the backend is unavailable.
- `src/data/menu.ts` groups menu items and resolves localized display fields.
- `src/i18n/config.ts` defines supported languages, UI copy, group labels, tag labels, and chat replies.
- `src/lib/recommend.ts` contains the local recommendation matcher used by tests and fallback logic.
- `src/lib/chat-api.ts` sends chat requests to the backend waiter API.

## Menu Data

Greek is the base language for menu records. English, German, Italian, Swedish, French, Russian, and Hebrew translations live under each item's `translations` object. The language contract is `el`, `en`, `de`, `it`, `sv`, `fr`, `ru`, and `he`. Hebrew is right-to-left; the app flips to `dir="rtl"` automatically via `isRtl()` in `src/i18n/config.ts`.

Each menu item should keep:

- a unique `id`
- a positive numeric `price`
- a base `name`, `description`, and `category`
- translated `name`, `description`, and `category` for `en`, `de`, `it`, `sv`, `fr`, `ru`, and `he`
- dietary/flavour tags that reflect the actual ingredients

## Chat Integration

The chat panel posts to the backend through `src/lib/chat-api.ts`. It includes the restaurant slug, table number, device id, user message, and active language code. If the API is unavailable, the UI shows a localized error message.

The menu page reads `NEXT_PUBLIC_API_BASE_URL` and calls `GET /api/menu?language_code=<lang>`. If the request fails during local development, the page renders the saved mock menu and shows a small fallback notice.

## Verification

Run these before handoff:

```bash
npm run lint
npm run test
npm run build
```

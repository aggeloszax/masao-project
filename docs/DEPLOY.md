# Masao — Deployment (Render backend + Vercel frontend)

## Αρχιτεκτονική production

```
Πελάτης (QR στο τραπέζι)
   │
   ▼
Vercel (Next.js frontend)  ──POST /api/chat──▶  Render (FastAPI backend)
                                                    │            │
                                              Supabase DB   Render Redis
                                              (μενού+chat)  (rate limiting)
                                                    │
                                              Anthropic API (AI σερβιτόρος)
```

## Βήμα 0 — Πριν από όλα (ασφάλεια)

1. Rotate το Supabase database password (Dashboard → Settings → Database).
2. Rotate το Anthropic API key (console.anthropic.com → API Keys).
3. Βεβαιώσου ότι κανένα `.env` δεν είναι μέσα στο git (`git status` δεν πρέπει να τα δείχνει).

## Βήμα 1 — GitHub

```bash
# Το repo είναι ήδη αρχικοποιημένο τοπικά. Ανέβασέ το:
gh repo create masao-project --private --source . --push
# ή χειροκίνητα: δημιούργησε repo στο github.com και
git remote add origin https://github.com/<USER>/masao-project.git
git push -u origin main
```

## Βήμα 2 — Backend στο Render

1. render.com → New → **Blueprint** → διάλεξε το GitHub repo.
   Το `render.yaml` στη ρίζα στήνει αυτόματα το web service + Redis.
2. Συμπλήρωσε τα secrets που ζητά το dashboard:
   - `DATABASE_URL` = το Supabase pooled connection string σε μορφή
     `postgresql+asyncpg://USER:PASSWORD@HOST:5432/postgres`
   - `ANTHROPIC_API_KEY` = το (νέο) Anthropic key
   - `CORS_ALLOWED_ORIGINS` = προσωρινά `http://localhost:3000` — θα το
     αλλάξεις στο Βήμα 4 με το πραγματικό Vercel URL.
3. Deploy. Όταν τελειώσει, δοκίμασε: `https://<service>.onrender.com/ready`
   → πρέπει να επιστρέφει `{"status":"ready",...}`.

Σημείωση free tier: το service «κοιμάται» μετά από 15' αδράνειας και το
πρώτο request μετά αργεί ~30-60s. Για πραγματικό εστιατόριο, το Starter
plan ($7/μήνα) το κρατάει πάντα ζεστό.

## Βήμα 3 — Frontend στο Vercel

1. vercel.com → Add New → Project → διάλεξε το repo.
2. **Root Directory: `frontend`** (σημαντικό — το Next.js app δεν είναι στη ρίζα).
3. Environment variable:
   - `NEXT_PUBLIC_API_BASE_URL` = `https://<service>.onrender.com`
4. Deploy.

## Βήμα 4 — Κλείσιμο του κύκλου

1. Πάρε το Vercel URL (π.χ. `https://masao.vercel.app`).
2. Render dashboard → masao-backend → Environment →
   `CORS_ALLOWED_ORIGINS=https://masao.vercel.app` → redeploy.
3. Δοκίμασε το chat από το Vercel URL.

## Βήμα 5 — QR codes

Κάθε τραπέζι δείχνει σε `https://<vercel-url>/?table=N` (N = 1-999).

## Checklist πριν ανοίξει για πελάτες

- [ ] `/ready` επιστρέφει ok (database + rate_limiter)
- [ ] Chat απαντά και στις 5 γλώσσες
- [ ] Rate limit δουλεύει (21ο μήνυμα σε 1 λεπτό → 429)
- [ ] Spend limit στο console.anthropic.com (π.χ. $25/μήνα)
- [ ] Admin endpoints απαντούν 403 χωρίς το X-API-Key

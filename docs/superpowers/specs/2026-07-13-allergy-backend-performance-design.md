# Allergy UX backend support + performance hardening — Design

Ημερομηνία: 2026-07-13
Κατάσταση: εγκεκριμένο από τον χρήστη (backend-only scope)

## Στόχος

Το προϊόν θα ρωτάει τον πελάτη για αλλεργίες στο πρώτο άνοιγμα του μενού
(bottom-sheet), θα αποθηκεύει το προφίλ, θα μαρκάρει πιάτα στο μενού και θα
υπενθυμίζει στο chat ότι μπορεί να ζητήσει αφαίρεση του συστατικού ή να
διαλέξει κάτι άλλο. **Το UI το υλοποιεί ο συνεργάτης· αυτό το spec καλύπτει
μόνο το backend**, με δύο ρητές μη-λειτουργικές απαιτήσεις από τον χρήστη:

1. Χωρίς αισθητή καθυστέρηση στα requests.
2. Να μην πέφτει με 200+ ταυτόχρονους χρήστες.

## Τι υπάρχει ήδη (δεν ξαναχτίζεται)

- `GET /api/allergens` — κατάλογος 14 αλλεργιογόνων ΕΕ, 5 γλώσσες.
- `PUT/GET /api/profile/allergies` — προφίλ ανά ανώνυμο device_id.
- `GET /api/menu` — κάθε πιάτο επιστρέφει `allergens`, `matched_allergens`,
  `allergen_alert` (τα δύο τελευταία μόνο με `device_id`).
- Chat: ντετερμινιστικό allergy warning σε κάθε reply path + allergy block
  στο system prompt του LLM.
- In-process TTL menu cache ανά γλώσσα με invalidation μετά το commit.

## Μετρημένη πραγματικότητα (production, 2026-07-13)

- Κάθε DB roundtrip Render↔Supabase κοστίζει ~200-250ms (cross-region).
  Ένα τετριμμένο SELECT μέσω request ≈ 0.9s server-side.
- Το allergy lookup στο chat (SAVEPOINT + SELECT + RELEASE) κοστίζει
  ~0.6-0.9s **ανά chat μήνυμα**.
- Το chat handler κρατά τη σύνδεση/transaction ανοιχτή σε όλη τη διάρκεια
  της κλήσης στο Claude (2-6s). Pool: size 10 + overflow 20 = 30 συνδέσεις.
  Άρα ταβάνι ≈ 30 ταυτόχρονα chat μηνύματα σε εξέλιξη· ο επόμενος περιμένει
  έως `pool_timeout` (30s) και μετά 500. Με 200 ενεργούς χρήστες
  (1 μήνυμα/30s, LLM ~4s) η μέση συν-ροή ≈ 27 — στο όριο, τα peaks πέφτουν.

## Αλλαγές

### 1. Commit πριν το LLM (κρίσιμο για τους 200+ χρήστες)

Στο `ChatService.handle_chat`: μετά το insert του user message και τα
reads (menu, allergens, history), γίνεται `await self.session.commit()`
ώστε η σύνδεση να επιστρέψει στο pool **πριν** την κλήση στο LLM. Το insert
του assistant message ανοίγει νέο transaction (autobegin) που το κλείνει το
`get_db_session` όπως σήμερα.

- Συνέπεια: αν το LLM path σκάσει με μη-αναμενόμενο σφάλμα, το user message
  έχει ήδη γραφτεί. Αποδεκτό — και σήμερα το fallback εγγυάται απάντηση,
  και η ημιτελής συνομιλία με γραμμένο user message είναι αβλαβής.
- Χρόνος κράτησης σύνδεσης: από 3-7s → μερικά queries (≈0.8s cross-region
  σήμερα, ~20ms αν συν-τοποθετηθούν τα regions). Κεφαλόρροια στα 30
  connections: από ~30 ταυτόχρονα μηνύματα → εκατοντάδες.

### 2. In-process TTL cache προφίλ αλλεργιών

Νέο `ProfileCache` στο `allergy_service.py`, ίδιο pattern με το
`MenuCache`:

- Key: `device_id` → `set[str]` allergens. Κρατάει και **κενά** προφίλ
  (negative caching — οι περισσότεροι πελάτες δεν έχουν δηλώσει τίποτα).
- TTL: νέο setting `allergy_profile_cache_ttl_seconds` (default 60, 0 στο
  test conftest, ίδια λογική με το menu cache).
- Φραγμένο μέγεθος: LRU, max 5000 entries (όπως τα rate-limit buckets) —
  δεν φουσκώνει η μνήμη στο 512MB free tier.
- Χρήση **μόνο** στο hot path των alerts: `try_get_customer_allergens`
  (chat + `/api/menu?device_id=`). Το `GET /api/profile/allergies` μένει
  DB-direct ώστε το prefill του UI να μη βλέπει ποτέ stale δεδομένα.
- Invalidation: το `upsert_profile` σημαδεύει `session.info` και listener
  `after_commit` καθαρίζει το entry (ακριβώς όπως το menu cache· pop του
  flag στο `after_rollback`). Multi-worker staleness φράσσεται από το TTL —
  ίδιο τεκμηριωμένο trade-off με το menu cache· στο free tier τρέχει 1
  worker, άρα πρακτικά άμεση συνέπεια.
- Το SAVEPOINT μένει μόνο στο cache-miss path (παραμένει fail-open).

Αποτέλεσμα: το allergy lookup μηδενίζεται για επαναλαμβανόμενα μηνύματα
ίδιας συσκευής — γλιτώνει ~0.6-0.9s ανά chat μήνυμα με το σημερινό latency.

### 3. Single-flight στο menu cache (προστασία από stampede)

Όταν λήγει το TTL και 200 χρήστες ανοίξουν το μενού ταυτόχρονα, σήμερα θα
τρέξουν 200 πανομοιότυπα 4-πινάκων queries. Προστίθεται ανά-γλώσσα
`asyncio.Lock` στο `MenuService.fetch_items`: ο πρώτος miss τρέχει το
query, οι υπόλοιποι περιμένουν και διαβάζουν το φρέσκο cache. (Double-check
του cache μέσα στο lock.)

### 4. Κείμενα υπενθύμισης (και στις 5 γλώσσες)

`FALLBACK_TEXTS[*]["allergy_warning"]` — νέο περιεχόμενο με το νόημα που
ζήτησε ο χρήστης: προειδοποίηση + «ζήτησε να αφαιρεθεί από το πιάτο αν
γίνεται, αλλιώς προτίμησε κάτι άλλο» + επιβεβαίωση με το προσωπικό.
Ενδεικτικά (el):

> « Προσοχή: το {name} περιέχει {allergens} που έχεις δηλώσει ως αλλεργία.
> Αν θες, ζήτησε από το προσωπικό να αφαιρεθεί από το πιάτο, αλλιώς
> προτίμησε κάτι άλλο.»

Αντίστοιχη φυσική απόδοση σε en, de, it, sv (όχι κατά λέξη μετάφραση).

### 5. Persona LLM

- `build_allergy_prompt`: προστίθεται οδηγία να προτείνει, όπου έχει νόημα,
  να ζητηθεί αφαίρεση του συστατικού από την κουζίνα ή ασφαλής εναλλακτική.
- `build_persona_prompt` (allergy bullet): ευθυγράμμιση με το ίδιο νόημα.
- Το ντετερμινιστικό warning μένει ως δίχτυ ασφαλείας σε όλα τα paths.

### 6. Τεκμηρίωση για τον συνεργάτη (frontend contract)

Νέα ενότητα στο `docs/FRONTEND_BACKEND_INTEGRATION_GR.md` με το
συμφωνημένο flow:

- Bottom-sheet στο πρώτο άνοιγμα: `GET /api/allergens?language_code=` για
  labels (ή στατική λίστα στο frontend), `PUT /api/profile/allergies` με το
  υπάρχον device_id του chat (`masao-device-id` στο localStorage),
  `GET /api/profile/allergies` για prefill στην επεξεργασία.
- Badges μενού: **χωρίς** `device_id` στο `/api/menu` — το response έχει ήδη
  `allergens` ανά πιάτο· το ταίριασμα γίνεται client-side με το αποθηκευμένο
  προφίλ (μηδέν επιπλέον DB κόστος, στιγμιαία ενημέρωση στα edits).
- Chat: καμία αλλαγή στο συμβόλαιο — τα warnings μπαίνουν αυτόματα, τα
  `recommended_items` έχουν ήδη `allergens/matched_allergens/allergen_alert`.

## Χωρητικότητα μετά τις αλλαγές (γιατί αντέχει 200+)

- Chat: η σύνδεση κρατιέται μόνο για τα γρήγορα queries. Με το σημερινό
  cross-region latency ≈0.8s hold → 30 συνδέσεις εξυπηρετούν ~37 μηνύματα/s·
  200 χρήστες × 1 μήνυμα/30s ≈ 6.7/s → ~5x περιθώριο. Με co-located
  regions το περιθώριο γίνεται >100x.
- Menu: cache hit = μηδέν DB· miss = 1 query ανά γλώσσα ανά 60s χάρη στο
  single-flight.
- Rate limiter: Redis-backed, fail-closed (υπάρχει) — φράσσει και το κόστος
  Anthropic.
- Εκτός scope αλλά καταγεγραμμένο: Render free tier (0.1 CPU, sleep μετά
  από 15') και co-location των regions είναι τα επόμενα λειτουργικά βήματα
  για πραγματικό φορτίο εστιατορίου.

## Testing

- `ProfileCache`: hit/miss/TTL expiry/LRU eviction/negative caching·
  invalidation μετά από commit, όχι μετά από rollback.
- Chat: test ότι κατά την κλήση του LLM το session **δεν** έχει ανοιχτό
  transaction (stub LLM που κάνει assert `not session.in_transaction()`) —
  αυτό κλειδώνει το commit-πριν-το-LLM ως συμπεριφορά, όχι ως υλοποίηση.
- Menu single-flight: N ταυτόχρονα `fetch_items` σε κρύο cache → 1 εκτέλεση
  query (μετρητής σε stub session).
- Κείμενα: το υπάρχον key-parity test καλύπτει τις 5 γλώσσες· προσαρμογή
  των tests που ελέγχουν το παλιό wording.
- Όλα τα υπάρχοντα 96 tests πρέπει να περνούν.

## Εκτός scope

- Οποιοδήποτε frontend (ο συνεργάτης).
- Αλλαγή Render region / πλάνου (λειτουργική απόφαση, συζητήθηκε χωριστά).
- Redis-backed κοινό cache προφίλ μεταξύ workers (YAGNI για 1 worker).

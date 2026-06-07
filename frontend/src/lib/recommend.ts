import { getLocalized, menu, type MenuItem } from "@/data/menu";
import { REPLY, type Lang } from "@/i18n/config";

/**
 * Localized mock-chatbot matching logic.
 *
 * Note on data shape: the mock has no `name_el` field — `name` is English only,
 * and the Greek content lives in `tags` and the Greek half of `description`.
 * So we scan name + category + description + tags. User input may be Greek,
 * English, so we (1) normalize away accents/final-sigma, (2) keep Unicode
 * letters during tokenization, (3) stem common Greek endings, and (4) expand
 * intent words via a synonym map (καυτερό → spicy).
 */

/** lowercase, strip Greek/Latin accents, unify final sigma. */
export function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "") // strip combining accent marks
    .replace(/ς/g, "σ"); // final sigma ς → σ
}

/** Strip common Greek inflectional endings so query words match either number. */
function stem(token: string): string {
  if (token.length <= 4) return token;
  return token.replace(/(αδες|ιδες|ουσ|ους|εων|ων|ασ|ησ|οσ|ες|οι|α|ο|η|ι|υ|ε|σ)$/, "");
}

const STOPWORDS = new Set([
  "θελω", "κατι", "εχετε", "εχεις", "εχει", "ειναι", "και", "για", "να", "το",
  "τα", "τη", "την", "τον", "της", "των", "μια", "ενα", "εναν", "μου", "σου",
  "σας", "μας", "θα", "πιο", "πολυ", "λιγο", "τι", "ποιο", "ποια", "που", "αν",
  "στο", "στη", "στην", "απο", "καποιο", "μπορω", "μπορειτε", "παρακαλω",
]);

/** Intent word → search terms found in the menu data. */
const SYNONYMS: Record<string, string[]> = {
  καυτερο: ["πικαντικο", "spicy"],
  καυτ: ["πικαντικο", "spicy"],
  πικαντικο: ["πικαντικο", "spicy"],
  spicy: ["πικαντικο", "spicy"],
  γλυκο: ["γλυκο", "dessert", "fondant"],
  επιδορπιο: ["γλυκο", "dessert"],
  dessert: ["γλυκο", "dessert"],
  δροσερο: ["δροσερο"],
  ελαφρυ: ["ελαφρυ"],
  vegan: ["vegan", "χορτοφαγ"],
  χορτοφαγικο: ["χορτοφαγ", "vegan"],
  χορτοφαγο: ["χορτοφαγ", "vegan"],
  γαριδα: ["γαριδ"],
  γαριδες: ["γαριδ"],
  σολομος: ["σολομ"],
  σουσι: ["maki", "nigiri", "roll", "uramaki"],
  sushi: ["maki", "nigiri", "roll", "uramaki"],
  μακι: ["maki"],
  noodles: ["noodle"],
  νουντλς: ["noodle"],
  noodle: ["noodle"],
  burger: ["burger", "sando"],
  μπεργκερ: ["burger", "sando"],
  μπιφτεκι: ["burger"],
  κοκτειλ: ["cocktail"],
  cocktail: ["cocktail"],
  ποτο: ["cocktail", "beer", "wine"],
  κρασι: ["wine"],
  μπυρα: ["beer"],
  beer: ["beer"],
  σισα: ["shisha"],
  ναργιλες: ["shisha"],
  shisha: ["shisha"],
};

function searchTerms(input: string): string[] {
  const tokens = normalize(input)
    .split(/[^\p{L}\p{N}]+/u)
    .filter((t) => t.length >= 3 && !STOPWORDS.has(t));

  const terms = new Set<string>();
  for (const token of tokens) {
    const s = stem(token);
    const synonyms = SYNONYMS[token] ?? SYNONYMS[s];
    if (synonyms) {
      for (const syn of synonyms) terms.add(normalize(syn));
    } else if (s.length >= 3) {
      terms.add(s);
    }
  }
  return [...terms];
}

/** Scan the menu and return the best matching items (highest term overlap). */
export function findMatches(input: string, limit = 3): MenuItem[] {
  const terms = searchTerms(input);
  if (terms.length === 0) return [];

  const scored = menu
    .map((item) => {
      const translated = Object.values(item.translations)
        .map((tr) => `${tr.name} ${tr.description} ${tr.category}`)
        .join(" ");
      const haystack = normalize(
        `${item.name} ${item.category} ${item.description} ${item.tags.join(" ")} ${translated}`,
      );
      const score = terms.reduce(
        (acc, term) => acc + (haystack.includes(term) ? 1 : 0),
        0,
      );
      return { item, score };
    })
    .filter((entry) => entry.score > 0)
    .sort((a, b) => b.score - a.score || a.item.price - b.item.price);

  return scored.slice(0, limit).map((entry) => entry.item);
}

/** Build the waiter's reply, localized to the active language. */
export function buildReply(items: MenuItem[], lang: Lang): string {
  const r = REPLY[lang];
  if (items.length === 0) return r.fallback;

  const [first, ...rest] = items;
  const { name, description } = getLocalized(first, lang);

  let reply = r.suggest(name, first.price.toFixed(2), description);
  if (rest.length > 0) {
    const list = rest.map((item) => getLocalized(item, lang).name).join(", ");
    reply += r.also(list);
  }
  return reply;
}

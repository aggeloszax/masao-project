from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal
from uuid import UUID

from sqlalchemy import RowMapping, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse, MenuItemResponse
from api.services.allergens import format_allergen_names, match_allergens
from api.services.allergy_service import AllergyService
from api.services.llm_service import LlmUnavailableError, get_llm_chat_service
from api.services.menu_service import MenuCandidate, MenuService
from api.utils import device_log_hash

logger = logging.getLogger(__name__)


STOPWORDS = {
    "i",
    "want",
    "with",
    "have",
    "something",
    "please",
    "the",
    "and",
    "a",
    "an",
    "one",
    "το",
    "τη",
    "την",
    "τον",
    "τα",
    "σε",
    "ενα",
    "ένα",
    "θελω",
    "κατι",
    "εχετε",
    "με",
    "και",
    "για",
    "παρακαλω",
}

SYNONYMS: dict[str, set[str]] = {
    "spicy": {"spicy", "hot", "chilli", "chili", "πικαντικο", "καυτερο"},
    "καυτερο": {"spicy", "πικαντικο", "καυτερο"},
    "φρουτωδες": {"φρουτωδες", "fruity", "fruit", "tropical", "τροπικο"},
    "φρουτωδεσ": {"φρουτωδες", "fruity", "fruit", "tropical", "τροπικο"},
    "fruity": {"φρουτωδες", "fruity", "fruit", "tropical", "τροπικο"},
    "vegan": {"vegan", "vegan-friendly", "vegetarian", "χορτοφαγικο"},
    "vegetarian": {"vegetarian", "vegan-friendly", "χορτοφαγικο"},
    "shrimp": {"shrimp", "γαριδα", "γαριδες"},
    "γαριδα": {"shrimp", "γαριδα", "γαριδες"},
    "salmon": {"salmon", "σολομος"},
    "chicken": {"chicken", "κοτοπουλο"},
    "dessert": {"dessert", "sweet", "chocolate", "γλυκο", "επιδορπιο"},
    "cocktail": {"cocktail", "cocktails", "κοκτειλ", "κοκτειλς"},
    "cocktails": {"cocktail", "cocktails", "κοκτειλ", "κοκτειλς"},
    "κοκτειλ": {"cocktail", "cocktails", "κοκτειλ", "κοκτειλς"},
    "drink": {"drink", "drinks", "ποτο", "ποτα"},
    "drinks": {"drink", "drinks", "ποτο", "ποτα"},
    "ποτο": {"drink", "drinks", "ποτο", "ποτα"},
    "ποτα": {"drink", "drinks", "ποτο", "ποτα"},
    "κρασι": {"wine", "wines", "κρασι", "κρασια"},
    "κρασια": {"wine", "wines", "κρασι", "κρασια"},
    "wine": {"wine", "wines", "κρασι", "κρασια"},
    "wines": {"wine", "wines", "κρασι", "κρασια"},
    "μπυρα": {"beer", "beers", "μπυρα", "μπυρες"},
    "μπυρες": {"beer", "beers", "μπυρα", "μπυρες"},
    "beer": {"beer", "beers", "μπυρα", "μπυρες"},
    "beers": {"beer", "beers", "μπυρα", "μπυρες"},
    "αναψυκτικο": {"soft drink", "soft drinks", "soda", "αναψυκτικο", "αναψυκτικα"},
    "αναψυκτικα": {"soft drink", "soft drinks", "soda", "αναψυκτικο", "αναψυκτικα"},
    "καφες": {"coffee", "espresso", "καφες"},
    "coffee": {"coffee", "espresso", "καφες"},
    "τσαι": {"tea", "τσαι"},
    "tea": {"tea", "τσαι"},
    "shisha": {"shisha", "ναργιλες"},
    "ναργιλες": {"shisha", "ναργιλες"},
}

QueryIntent = Literal["recommendation", "item_detail", "category_overview"]

MENU_GROUP_CATEGORIES: dict[str, set[str]] = {
    "cocktails": {"masao cocktails", "classic cocktails", "mocktails"},
    "drinks": {"soft drinks", "ciders", "beers", "whiskey"},
    "wines": {"white wines", "rose wines", "red wines", "champagne sparkling"},
    "shisha": {"shisha"},
}

GROUP_LABELS = {
    "cocktails": "Cocktails",
    "drinks": "Soft Drinks / Beers / Whiskey",
    "wines": "Wines",
    "shisha": "Shisha",
}

GROUP_KEYWORDS: dict[str, set[str]] = {
    "cocktails": {"cocktail", "cocktails", "κοκτειλ", "κοκτειλς"},
    "drinks": {
        "drink",
        "drinks",
        "ποτο",
        "ποτα",
        "soft drink",
        "soft drinks",
        "αναψυκτικο",
        "αναψυκτικα",
        "beer",
        "beers",
        "μπυρα",
        "μπυρες",
        "coffee",
        "espresso",
        "καφες",
        "tea",
        "τσαι",
    },
    "wines": {"wine", "wines", "κρασι", "κρασια"},
    "shisha": {"shisha", "ναργιλες"},
}

BROAD_DRINK_TERMS = {"drink", "drinks", "ποτο", "ποτα"}

DETAIL_PATTERNS = (
    "τι εχει",
    "τι περιεχει",
    "τι ειναι",
    "what is",
    "what does",
    "what's in",
    "ingredients",
    "contains",
)

OVERVIEW_PATTERNS = (
    "τι εχει",
    "τι εχετε",
    "τι υπαρχει",
    "τι επιλογες",
    "what do you have",
    "show me",
)

RECOMMENDATION_TERMS = {"προτεινεις", "προτεινε", "recommend", "suggest", "θελω", "want"}

# Κείμενα του deterministic fallback ανά γλώσσα (όταν το LLM δεν είναι διαθέσιμο).
FALLBACK_TEXTS: dict[str, dict[str, str]] = {
    "el": {
        "no_match": (
            "Μπορώ να βοηθήσω με sushi, bao, noodles, burgers, cocktails ή shisha. "
            "Πες μου αν θέλεις κάτι καυτερό, vegan, με γαρίδα, με κοτόπουλο ή κάτι γλυκό."
        ),
        "suggest": "Σου προτείνω το {name} ({price:.2f}€). {description}",
        "also": " Επίσης ταιριάζουν: {names}.",
        "detail": "Το {name} ({price:.2f}€) περιέχει: {description}.",
        "detail_generic": (
            "Για το {name} ({price:.2f}€), το μενού γράφει: {description}. "
            "δεν έχω αναλυτικά συστατικά για αυτό το item, οπότε δεν θα τα επινοήσω."
        ),
        "overview_intro": "Στα ποτά υπάρχουν οι εξής επιλογές: ",
        "overview_sample": "Ενδεικτικά",
        "overview_empty": "Δεν βρήκα διαθέσιμες επιλογές σε αυτή την κατηγορία.",
        "allergy_warning": (
            " Προσοχή: το {name} περιέχει {allergens} που έχεις δηλώσει ως αλλεργία. "
            "Επιβεβαίωσέ το με το προσωπικό."
        ),
    },
    "en": {
        "no_match": (
            "I can help with sushi, bao, noodles, burgers, cocktails or shisha. "
            "Tell me if you'd like something spicy, vegan, with shrimp, with chicken or something sweet."
        ),
        "suggest": "I recommend the {name} ({price:.2f}€). {description}",
        "also": " These also match: {names}.",
        "detail": "The {name} ({price:.2f}€) contains: {description}.",
        "detail_generic": (
            "For the {name} ({price:.2f}€), the menu says: {description}. "
            "I don't have detailed ingredients for this item, so I won't make them up."
        ),
        "overview_intro": "Here are the drink options: ",
        "overview_sample": "For example",
        "overview_empty": "I couldn't find available options in that category.",
        "allergy_warning": (
            " Warning: {name} contains {allergens}, which you have declared as an allergy. "
            "Please confirm with the staff."
        ),
    },
    "de": {
        "no_match": (
            "Ich kann mit Sushi, Bao, Noodles, Burgern, Cocktails oder Shisha helfen. "
            "Sagen Sie mir, ob Sie etwas Scharfes, Veganes, mit Garnelen, mit Hähnchen oder etwas Süßes möchten."
        ),
        "suggest": "Ich empfehle {name} ({price:.2f}€). {description}",
        "also": " Ebenfalls passend: {names}.",
        "detail": "{name} ({price:.2f}€) enthält: {description}.",
        "detail_generic": (
            "Zu {name} ({price:.2f}€) steht im Menü: {description}. "
            "Detaillierte Zutaten habe ich für diesen Artikel nicht, also erfinde ich keine."
        ),
        "overview_intro": "Bei den Getränken gibt es folgende Optionen: ",
        "overview_sample": "Zum Beispiel",
        "overview_empty": "Ich habe in dieser Kategorie keine verfügbaren Optionen gefunden.",
        "allergy_warning": (
            " Achtung: {name} enthält {allergens}, was Sie als Allergie angegeben haben. "
            "Bitte bestätigen Sie es beim Personal."
        ),
    },
    "it": {
        "no_match": (
            "Posso aiutarti con sushi, bao, noodles, burger, cocktail o shisha. "
            "Dimmi se preferisci qualcosa di piccante, vegano, con gamberi, con pollo o qualcosa di dolce."
        ),
        "suggest": "Ti consiglio {name} ({price:.2f}€). {description}",
        "also": " Si abbinano anche: {names}.",
        "detail": "{name} ({price:.2f}€) contiene: {description}.",
        "detail_generic": (
            "Per {name} ({price:.2f}€), il menu dice: {description}. "
            "Non ho gli ingredienti dettagliati per questo articolo, quindi non li inventerò."
        ),
        "overview_intro": "Per le bevande ci sono queste opzioni: ",
        "overview_sample": "Ad esempio",
        "overview_empty": "Non ho trovato opzioni disponibili in questa categoria.",
        "allergy_warning": (
            " Attenzione: {name} contiene {allergens}, che hai dichiarato come allergia. "
            "Conferma con il personale."
        ),
    },
    "sv": {
        "no_match": (
            "Jag kan hjälpa till med sushi, bao, noodles, burgare, cocktails eller shisha. "
            "Säg till om du vill ha något kryddigt, veganskt, med räkor, med kyckling eller något sött."
        ),
        "suggest": "Jag rekommenderar {name} ({price:.2f}€). {description}",
        "also": " Dessa passar också: {names}.",
        "detail": "{name} ({price:.2f}€) innehåller: {description}.",
        "detail_generic": (
            "För {name} ({price:.2f}€) säger menyn: {description}. "
            "Jag har inga detaljerade ingredienser för denna rätt, så jag hittar inte på några."
        ),
        "overview_intro": "Bland dryckerna finns följande alternativ: ",
        "overview_sample": "Till exempel",
        "overview_empty": "Jag hittade inga tillgängliga alternativ i den kategorin.",
        "allergy_warning": (
            " Varning: {name} innehåller {allergens}, som du har angett som allergi. "
            "Bekräfta med personalen."
        ),
    },
}


def fallback_texts(language_code: str) -> dict[str, str]:
    """Return fallback reply templates for a guest language.

    Args:
        language_code: Guest language code.

    Returns:
        dict[str, str]: Reply templates, defaulting to Greek.

    Raises:
        None.
    """
    return FALLBACK_TEXTS.get(language_code, FALLBACK_TEXTS["el"])


@dataclass(frozen=True)
class ChatAnswer:
    intent: QueryIntent
    reply: str
    recommendations: list[MenuCandidate]


def normalize_text(value: str) -> str:
    """Normalize user/menu text for multilingual matching.

    Args:
        value: Raw text from the user or menu database.

    Returns:
        str: Lowercase text without accents and with final sigma normalized.

    Raises:
        None.
    """
    normalized = unicodedata.normalize("NFD", value.lower())
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return without_marks.replace("ς", "σ")


def tokenize(value: str) -> list[str]:
    """Tokenize Latin and Greek text.

    Args:
        value: Raw text to tokenize.

    Returns:
        list[str]: Search tokens excluding common low-signal words.

    Raises:
        None.
    """
    tokens = re.findall(r"[0-9A-Za-zΑ-Ωα-ω]+", normalize_text(value))
    return [token for token in tokens if len(token) >= 2 and token not in STOPWORDS]


# Προϋπολογισμένα normalized group keywords: αποφεύγεται το normalize_text
# ανά keyword σε κάθε εισερχόμενο μήνυμα.
GROUP_KEYWORD_PHRASES: dict[str, set[str]] = {
    group: {normalize_text(keyword) for keyword in keywords if " " in normalize_text(keyword)}
    for group, keywords in GROUP_KEYWORDS.items()
}
GROUP_KEYWORD_WORDS: dict[str, set[str]] = {
    group: {normalize_text(keyword) for keyword in keywords if " " not in normalize_text(keyword)}
    for group, keywords in GROUP_KEYWORDS.items()
}


def expand_terms(tokens: list[str]) -> set[str]:
    """Expand user tokens with known menu-intent synonyms.

    Args:
        tokens: Normalized user query tokens.

    Returns:
        set[str]: Search terms used against menu names, descriptions and tags.

    Raises:
        None.
    """
    terms: set[str] = set()
    for token in tokens:
        terms.add(token)
        terms.update(SYNONYMS.get(token, set()))
    return {normalize_text(term) for term in terms}


@lru_cache(maxsize=256)
def _category_group(category: str) -> str | None:
    """Return the high-level menu group of a category name.

    Args:
        category: Raw category name from the database.

    Returns:
        str | None: Group id such as cocktails, drinks, wines or shisha.

    Raises:
        None.
    """
    # lru_cache: οι κατηγορίες είναι λίγες και επαναλαμβάνονται σε κάθε item,
    # οπότε το regex normalization τρέχει μία φορά ανά κατηγορία ανά process.
    normalized_category = normalize_text(category).replace("&", " ")
    normalized_category = re.sub(r"[^0-9a-zα-ω]+", " ", normalized_category).strip()
    for group, categories in MENU_GROUP_CATEGORIES.items():
        if normalized_category in categories:
            return group
    return None


def item_group(item: MenuCandidate) -> str | None:
    """Return the high-level menu group for a menu item.

    Args:
        item: Menu item candidate.

    Returns:
        str | None: Group id such as cocktails, drinks, wines or shisha.

    Raises:
        None.
    """
    return _category_group(item.category)


def requested_groups(user_message: str) -> set[str]:
    """Detect high-level menu groups requested by the guest.

    Args:
        user_message: Raw guest message.

    Returns:
        set[str]: Requested group ids.

    Raises:
        None.
    """
    normalized_message = normalize_text(user_message)
    tokens = tokenize(user_message)
    terms = expand_terms(tokens)

    if terms & BROAD_DRINK_TERMS:
        return {"cocktails", "drinks", "wines"}

    # Το expand_terms περιέχει ήδη κάθε token, οπότε αρκεί το terms.
    groups: set[str] = set()
    for group in GROUP_KEYWORDS:
        if GROUP_KEYWORD_WORDS[group] & terms:
            groups.add(group)
        elif any(phrase in normalized_message for phrase in GROUP_KEYWORD_PHRASES[group]):
            groups.add(group)
    return groups


def group_keyword_terms(groups: set[str]) -> set[str]:
    """Return normalized keywords that only identify requested groups.

    Args:
        groups: High-level menu group ids.

    Returns:
        set[str]: Normalized group/category keywords.

    Raises:
        None.
    """
    terms: set[str] = set()
    for group in groups:
        terms |= GROUP_KEYWORD_WORDS.get(group, set())
        terms |= GROUP_KEYWORD_PHRASES.get(group, set())
    return terms


def is_overview_question(user_message: str) -> bool:
    """Detect whether the guest asks what exists in a category.

    Args:
        user_message: Raw guest message.

    Returns:
        bool: True when the message asks for category availability.

    Raises:
        None.
    """
    normalized_message = normalize_text(user_message)
    if any(term in normalized_message for term in RECOMMENDATION_TERMS):
        return False
    return any(pattern in normalized_message for pattern in OVERVIEW_PATTERNS)


def is_item_detail_question(user_message: str) -> bool:
    """Detect whether the guest asks about a specific menu item.

    Args:
        user_message: Raw guest message.

    Returns:
        bool: True when the message asks about item ingredients/details.

    Raises:
        None.
    """
    normalized_message = normalize_text(user_message)
    return any(pattern in normalized_message for pattern in DETAIL_PATTERNS)


@lru_cache(maxsize=2048)
def _cached_haystack(name: str, description: str, category: str, tags: tuple[str, ...]) -> str:
    # lru_cache σε string keys: το unicode normalization ανά item τρέχει μία
    # φορά ανά μοναδικό κείμενο ανά process, όχι σε κάθε chat μήνυμα.
    return normalize_text(" ".join([name, description, category, " ".join(tags)]))


def item_haystack(item: MenuCandidate) -> str:
    """Build the normalized searchable text of a menu item.

    Args:
        item: Menu item candidate.

    Returns:
        str: Lowercase accent-free text of name, description, category and tags.

    Raises:
        None.
    """
    return _cached_haystack(item.name, item.description, item.category, tuple(item.tags))


def choose_recommendations(user_message: str, menu_items: list[MenuCandidate], limit: int = 3) -> list[MenuCandidate]:
    """Choose the best available menu recommendations for a user message.

    Args:
        user_message: Message sent by the guest.
        menu_items: Available menu candidates fetched from PostgreSQL.
        limit: Maximum number of recommendations to return.

    Returns:
        list[MenuCandidate]: Top ranked menu items.

    Raises:
        None.
    """
    terms = expand_terms(tokenize(user_message))
    if not terms:
        return []

    groups = requested_groups(user_message)
    preference_terms = terms - group_keyword_terms(groups)

    # Επιλογή πιάτων με βάση overlap σε όνομα, περιγραφή, κατηγορία και AI tags.
    # Ένα πέρασμα ανά item: το haystack χτίζεται μία φορά και για τα δύο σκορ.
    ranked: list[tuple[MenuCandidate, int]] = []
    for item in menu_items:
        if not item.is_available or (groups and item_group(item) not in groups):
            continue
        haystack = item_haystack(item)
        if preference_terms and not any(term in haystack for term in preference_terms):
            continue
        score = sum(1 for term in terms if term in haystack)
        if score > 0:
            ranked.append((item, score))

    ranked.sort(key=lambda pair: (-pair[1], item_group(pair[0]) or "", pair[0].price, pair[0].name))
    return [item for item, _score in ranked[:limit]]


def find_item_detail_match(user_message: str, menu_items: list[MenuCandidate]) -> MenuCandidate | None:
    """Find a specific item mentioned in a detail question.

    Args:
        user_message: Raw guest message.
        menu_items: Available menu candidates.

    Returns:
        MenuCandidate | None: Best exact item-name match.

    Raises:
        None.
    """
    normalized_message = normalize_text(user_message)
    matches = [
        item
        for item in menu_items
        if item.is_available and normalize_text(item.name) in normalized_message
    ]
    if not matches:
        return None
    return sorted(matches, key=lambda item: (-len(item.name), item.name))[0]


def build_item_detail_reply(item: MenuCandidate, language_code: str = "el") -> str:
    """Build a factual item detail reply without inventing missing ingredients.

    Args:
        item: Matched menu item.
        language_code: Guest language code.

    Returns:
        str: Assistant reply.

    Raises:
        None.
    """
    texts = fallback_texts(language_code)
    normalized_name = normalize_text(item.name)
    normalized_description = normalize_text(item.description)
    generic_descriptions = {
        normalized_name,
        f"classic {normalized_name}",
        f"{normalized_name} selection",
        f"classic {normalized_name} selection",
    }
    template = texts["detail_generic"] if normalized_description in generic_descriptions else texts["detail"]
    return template.format(name=item.name, price=item.price, description=item.description)


def build_category_overview_reply(
    groups: set[str],
    menu_items: list[MenuCandidate],
    language_code: str = "el",
    customer_allergens: set[str] | None = None,
) -> str:
    """Build a category overview for drinks/cocktails/wines style questions.

    Args:
        groups: Requested high-level group ids.
        menu_items: Available menu candidates.
        language_code: Guest language code.
        customer_allergens: Declared guest allergens; sampled items that match
            get a warning appended (π.χ. θειώδη στα κρασιά).

    Returns:
        str: Assistant reply with category names and sample items.

    Raises:
        None.
    """
    texts = fallback_texts(language_code)
    lines = []
    sampled_items: list[MenuCandidate] = []
    for group in ("cocktails", "drinks", "wines", "shisha"):
        if group not in groups:
            continue
        grouped_items = [item for item in menu_items if item.is_available and item_group(item) == group]
        if not grouped_items:
            continue
        categories = sorted({item.category for item in grouped_items})
        samples = grouped_items[:3]
        sampled_items.extend(samples)
        sample_names = ", ".join(item.name for item in samples)
        lines.append(f"{GROUP_LABELS[group]}: {', '.join(categories)}. {texts['overview_sample']}: {sample_names}.")

    if not lines:
        return texts["overview_empty"]
    reply = texts["overview_intro"] + " ".join(lines)
    return append_allergy_warnings(reply, sampled_items, customer_allergens or set(), language_code=language_code)


def append_allergy_warnings(
    reply: str,
    items: list[MenuCandidate],
    customer_allergens: set[str],
    language_code: str = "el",
) -> str:
    """Append localized allergy warnings for flagged recommended items.

    Args:
        reply: Assistant reply built so far.
        items: Menu items mentioned or recommended in the reply.
        customer_allergens: Canonical allergen codes declared by the guest.
        language_code: Guest language code.

    Returns:
        str: Reply with one warning sentence per flagged item.

    Raises:
        None.
    """
    if not customer_allergens:
        return reply

    texts = fallback_texts(language_code)
    for item in items:
        matched = match_allergens(item.allergens, customer_allergens)
        if matched:
            reply += texts["allergy_warning"].format(
                name=item.name,
                allergens=format_allergen_names(matched, language_code),
            )
    return reply


def answer_menu_query(
    user_message: str,
    menu_items: list[MenuCandidate],
    limit: int = 3,
    language_code: str = "el",
    customer_allergens: set[str] | None = None,
) -> ChatAnswer:
    """Answer a menu query using deterministic intent handling.

    Args:
        user_message: Raw guest message.
        menu_items: Available menu candidates.
        limit: Maximum recommendation count.
        language_code: Guest language code.
        customer_allergens: Declared guest allergens for reply warnings.

    Returns:
        ChatAnswer: Intent, assistant reply and recommended items.

    Raises:
        None.
    """
    declared = customer_allergens or set()
    if is_item_detail_question(user_message):
        item = find_item_detail_match(user_message, menu_items)
        if item is not None:
            reply = build_item_detail_reply(item, language_code=language_code)
            reply = append_allergy_warnings(reply, [item], declared, language_code=language_code)
            return ChatAnswer(intent="item_detail", reply=reply, recommendations=[item])

    groups = requested_groups(user_message)
    if groups and is_overview_question(user_message):
        return ChatAnswer(
            intent="category_overview",
            reply=build_category_overview_reply(
                groups,
                menu_items,
                language_code=language_code,
                customer_allergens=declared,
            ),
            recommendations=[],
        )

    recommendations = choose_recommendations(user_message, menu_items, limit=limit)
    reply = build_assistant_reply(user_message, recommendations, language_code=language_code)
    reply = append_allergy_warnings(reply, recommendations, declared, language_code=language_code)
    return ChatAnswer(intent="recommendation", reply=reply, recommendations=recommendations)


def build_assistant_reply(
    user_message: str,
    recommendations: list[MenuCandidate],
    language_code: str = "el",
) -> str:
    """Build a menu-aware assistant reply for the deterministic fallback.

    Args:
        user_message: Original user message.
        recommendations: Ranked menu recommendations.
        language_code: Guest language code.

    Returns:
        str: Assistant message to store and return to the frontend.

    Raises:
        None.
    """
    texts = fallback_texts(language_code)
    if not recommendations:
        return texts["no_match"]

    first = recommendations[0]
    also = recommendations[1:]
    reply = texts["suggest"].format(name=first.name, price=first.price, description=first.description)
    if also:
        names = ", ".join(item.name for item in also)
        reply += texts["also"].format(names=names)
    return reply


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def handle_chat(self, request: ChatRequest) -> ChatResponse:
        """Persist a user message and return a structured assistant response.

        Args:
            request: Validated chat request from the Next.js client.

        Returns:
            ChatResponse: Session id, full message list and recommended menu items.

        Raises:
            ValueError: If the restaurant slug is not supported.
            SQLAlchemyError: If database operations fail.
        """
        if request.restaurant_slug != settings.restaurant_slug:
            raise ValueError(f"Unsupported restaurant_slug: {request.restaurant_slug}")

        try:
            # Το μενού πρώτα, πριν ανοίξει transaction: σε cold cache το
            # request περιμένει το single-flight lock ΧΩΡΙΣ να κρατά pooled
            # connection (αλλιώς: lock holder χωρίς connection + waiters με
            # connections = αμοιβαία αναμονή μέχρι το pool_timeout).
            menu_items = await self._fetch_menu_items(request.language_code)
            session_id = await self._get_or_create_session(request.device_id, request.table_number)
            await self._insert_message(session_id, "user", request.user_message)
            customer_allergens = await self._fetch_customer_allergens(request.device_id)
            history = await self._fetch_messages(session_id)
            # Επιστροφή της σύνδεσης στο pool πριν το LLM: η κλήση κρατά
            # δευτερόλεπτα, το pool έχει 30 slots — με ανοιχτό transaction
            # εδώ, ~30 ταυτόχρονα μηνύματα αρκούν για pool exhaustion. Το
            # insert του assistant message ανοίγει νέο transaction μετά.
            await self.session.commit()
            assistant_content, recommendations = await self._generate_answer(
                request=request,
                menu_items=menu_items,
                history=history,
                customer_allergens=customer_allergens,
            )
            assistant_message = await self._insert_message(session_id, "assistant", assistant_content)
            # Το history περιέχει ήδη το τρέχον user μήνυμα· χτίζουμε τη λίστα
            # in-memory αντί για δεύτερο SELECT ανά chat μήνυμα.
            messages = (history + [assistant_message])[-settings.chat_history_limit :]
        except SQLAlchemyError:
            logger.exception(
                "Chat persistence failed for device_hash=%s table=%s",
                device_log_hash(request.device_id),
                request.table_number,
            )
            raise

        logger.info(
            "Chat handled for restaurant=%s table=%s device_hash=%s recommendations=%s",
            request.restaurant_slug,
            request.table_number,
            device_log_hash(request.device_id),
            len(recommendations),
        )
        return ChatResponse(
            session_id=session_id,
            restaurant_slug=request.restaurant_slug,
            table_number=request.table_number,
            device_id=request.device_id,
            language_code=request.language_code,
            assistant_message=assistant_message,
            messages=messages,
            recommended_items=[
                self._menu_response(item, customer_allergens) for item in recommendations
            ],
        )

    async def _generate_answer(
        self,
        request: ChatRequest,
        menu_items: list[MenuCandidate],
        history: list[ChatMessageResponse],
        customer_allergens: set[str] | None = None,
    ) -> tuple[str, list[MenuCandidate]]:
        """Produce the assistant reply, preferring the LLM over keyword matching.

        Args:
            request: Validated chat request.
            menu_items: Available menu candidates in the guest's language.
            history: Recent conversation messages ending with the current user message.
            customer_allergens: Declared guest allergens for warnings.

        Returns:
            tuple[str, list[MenuCandidate]]: Reply text and recommended items.

        Raises:
            None. LLM failures fall back to the deterministic answer.
        """
        declared = customer_allergens or set()
        llm = get_llm_chat_service()
        if llm.is_configured():
            try:
                llm_answer = await llm.answer(
                    history=[(message.role, message.content) for message in history],
                    menu_items=menu_items,
                    language_code=request.language_code,
                    customer_allergens=sorted(declared),
                )
            except LlmUnavailableError:
                logger.exception("LLM answer failed; using deterministic fallback")
            else:
                items_by_id = {item.id: item for item in menu_items}
                recommendations = [
                    items_by_id[item_id]
                    for item_id in llm_answer.recommended_item_ids
                    if item_id in items_by_id
                ]
                # Εγγυημένη προειδοποίηση και στο LLM path: το prompt ζητά
                # warning αλλά η ασφάλεια δεν αφήνεται στη συμμόρφωση του
                # μοντέλου. Τυχόν διπλή αναφορά είναι αποδεκτό κόστος.
                reply = append_allergy_warnings(
                    llm_answer.reply,
                    recommendations,
                    declared,
                    language_code=request.language_code,
                )
                return reply, recommendations

        answer = answer_menu_query(
            request.user_message,
            menu_items,
            language_code=request.language_code,
            customer_allergens=declared,
        )
        return answer.reply, answer.recommendations

    async def _get_or_create_session(self, device_id: str, table_number: int) -> UUID:
        result = await self.session.execute(
            text(
                """
                insert into chat_sessions (device_id, table_number, is_active)
                values (:device_id, :table_number, true)
                on conflict (device_id, table_number) where is_active = true
                do update set is_active = true
                returning id
                """
            ),
            {"device_id": device_id, "table_number": table_number},
        )
        return result.scalar_one()

    async def _insert_message(self, session_id: UUID, role: str, content: str) -> ChatMessageResponse:
        result = await self.session.execute(
            text(
                """
                insert into chat_messages (session_id, role, content)
                values (:session_id, :role, :content)
                returning id, session_id, role, content, created_at
                """
            ),
            {"session_id": session_id, "role": role, "content": content},
        )
        return self._message_response(result.mappings().one())

    async def _fetch_messages(self, session_id: UUID) -> list[ChatMessageResponse]:
        result = await self.session.execute(
            text(
                """
                select id, session_id, role, content, created_at
                from (
                    select id, session_id, role, content, created_at
                    from chat_messages
                    where session_id = :session_id
                    order by created_at desc, id desc
                    limit :limit
                ) recent_messages
                order by created_at asc, id asc
                """
            ),
            {"session_id": session_id, "limit": settings.chat_history_limit},
        )
        return [self._message_response(row) for row in result.mappings().all()]

    async def _fetch_menu_items(self, language_code: str) -> list[MenuCandidate]:
        return await MenuService(self.session).fetch_candidates(language_code=language_code)

    async def _fetch_customer_allergens(self, device_id: str) -> set[str]:
        return await AllergyService(self.session).try_get_customer_allergens(device_id)

    @staticmethod
    def _message_response(row: RowMapping) -> ChatMessageResponse:
        return ChatMessageResponse(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            created_at=row["created_at"],
        )

    @staticmethod
    def _menu_response(item: MenuCandidate, customer_allergens: set[str] | None = None) -> MenuItemResponse:
        matched = match_allergens(item.allergens, customer_allergens or set())
        return MenuItemResponse(
            id=item.id,
            external_id=item.external_id,
            category=item.category,
            name=item.name,
            description=item.description,
            price=item.price,
            tags=item.tags,
            is_available=item.is_available,
            language_code=item.language_code,
            allergens=item.allergens,
            matched_allergens=matched,
            allergen_alert=bool(matched),
        )

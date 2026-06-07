from __future__ import annotations

import logging
import re
import unicodedata
from uuid import UUID

from sqlalchemy import RowMapping, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse, MenuItemResponse
from api.services.menu_service import MenuCandidate, MenuService

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
    "vegan": {"vegan", "vegan-friendly", "vegetarian", "χορτοφαγικο"},
    "vegetarian": {"vegetarian", "vegan-friendly", "χορτοφαγικο"},
    "shrimp": {"shrimp", "γαριδα", "γαριδες"},
    "γαριδα": {"shrimp", "γαριδα", "γαριδες"},
    "salmon": {"salmon", "σολομος"},
    "chicken": {"chicken", "κοτοπουλο"},
    "dessert": {"dessert", "sweet", "chocolate", "γλυκο", "επιδορπιο"},
    "cocktail": {"cocktail", "drink", "κοκτειλ", "ποτο"},
    "shisha": {"shisha", "ναργιλες"},
}


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


def score_menu_item(item: MenuCandidate, terms: set[str]) -> int:
    """Score a menu item by term overlap.

    Args:
        item: Menu item candidate.
        terms: Expanded normalized search terms.

    Returns:
        int: Number of matched terms. Higher score means stronger recommendation.

    Raises:
        None.
    """
    haystack = normalize_text(" ".join([item.name, item.description, item.category, " ".join(item.tags)]))
    return sum(1 for term in terms if term and term in haystack)


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

    # Επιλογή πιάτων με βάση overlap σε όνομα, περιγραφή, κατηγορία και AI tags.
    scored = [
        (item, score_menu_item(item, terms))
        for item in menu_items
        if item.is_available
    ]
    ranked = sorted(
        ((item, score) for item, score in scored if score > 0),
        key=lambda pair: (-pair[1], pair[0].price, pair[0].name),
    )
    return [item for item, _score in ranked[:limit]]


def build_assistant_reply(user_message: str, recommendations: list[MenuCandidate]) -> str:
    """Build a menu-aware assistant reply for the MVP.

    Args:
        user_message: Original user message.
        recommendations: Ranked menu recommendations.

    Returns:
        str: Assistant message to store and return to the frontend.

    Raises:
        None.
    """
    if not recommendations:
        return (
            "Μπορώ να βοηθήσω με sushi, bao, noodles, burgers, cocktails ή shisha. "
            "Πες μου αν θέλεις κάτι καυτερό, vegan, με γαρίδα, με κοτόπουλο ή κάτι γλυκό."
        )

    first = recommendations[0]
    also = recommendations[1:]
    reply = (
        f"Σου προτείνω το {first.name} ({first.price:.2f}€). "
        f"{first.description}"
    )
    if also:
        names = ", ".join(item.name for item in also)
        reply += f" Επίσης ταιριάζουν: {names}."
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
            session_id = await self._get_or_create_session(request.device_id, request.table_number)
            await self._insert_message(session_id, "user", request.user_message)
            menu_items = await self._fetch_menu_items(request.language_code)
            recommendations = choose_recommendations(request.user_message, menu_items)
            assistant_content = build_assistant_reply(request.user_message, recommendations)
            assistant_message = await self._insert_message(session_id, "assistant", assistant_content)
            messages = await self._fetch_messages(session_id)
        except SQLAlchemyError:
            logger.exception("Chat persistence failed for device_id=%s table=%s", request.device_id, request.table_number)
            raise

        logger.info(
            "Chat handled for restaurant=%s table=%s device_id=%s recommendations=%s",
            request.restaurant_slug,
            request.table_number,
            request.device_id,
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
            recommended_items=[self._menu_response(item) for item in recommendations],
        )

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
    def _menu_response(item: MenuCandidate) -> MenuItemResponse:
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
        )

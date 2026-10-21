
import re
import sqlite3
from pathlib import Path


class ChatMemory:
    """Store chat history and persistent facts in SQLite."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as db:
            # Conversation history
            db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL
                        CHECK(role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Persistent facts
            db.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _connect(self):
        """Create a SQLite connection."""
        return sqlite3.connect(self.path, timeout=10)

    # --------------------------------------------------
    # CHAT HISTORY
    # --------------------------------------------------

    def add(self, role: str, content: str) -> None:
        """Save one message to conversation history."""
        if role not in {"user", "assistant"}:
            raise ValueError("role must be 'user' or 'assistant'")

        if not isinstance(content, str):
            raise TypeError("Message content must be a string.")

        content = content.strip()
        if not content:
            return

        with self._connect() as db:
            db.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)",
                (role, content),
            )

    def recent(self, limit: int = 12) -> list[dict[str, str]]:
        """Return recent messages in chronological order."""
        limit = max(0, int(limit))

        with self._connect() as db:
            rows = db.execute(
                """
                SELECT role, content
                FROM messages
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [
            {"role": role, "content": content}
            for role, content in reversed(rows)
        ]

    def clear(self) -> None:
        """Clear chat history without deleting saved facts."""
        with self._connect() as db:
            db.execute("DELETE FROM messages")

    # --------------------------------------------------
    # PERSISTENT FACTS MEMORY
    # --------------------------------------------------

    def remember(self, fact: str) -> None:
        """Save a fact permanently until explicitly forgotten."""
        if not isinstance(fact, str):
            raise TypeError("Fact must be a string.")

        fact = fact.strip()
        if not fact:
            raise ValueError("Fact cannot be empty.")

        with self._connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO facts (fact)
                VALUES (?)
                """,
                (fact,),
            )

    def recall(
        self,
        query: str = "",
        limit: int = 10,
    ) -> list[str]:
        """
        Retrieve saved facts.

        A query searches for a literal substring.
        An empty query returns the most recently saved facts.
        """
        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        query = query.strip()
        limit = max(0, int(limit))

        if limit == 0:
            return []

        with self._connect() as db:
            if query:
                rows = db.execute(
                    """
                    SELECT fact
                    FROM facts
                    WHERE instr(lower(fact), lower(?)) > 0
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (query, limit),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT fact
                    FROM facts
                    ORDER BY id DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [row[0] for row in rows]

    def search_relevant(
        self,
        query: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Rank facts by keyword overlap with a question.

        This is lightweight keyword search, not semantic search.
        """
        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        limit = max(0, int(limit))
        if limit == 0:
            return []

        # Remove punctuation and ignore common words.
        stop_words = {
            "the", "and", "for", "are", "was", "were", "what",
            "when", "where", "which", "who", "how", "does",
            "did", "you", "your", "about", "have", "has",
            "had", "that", "this", "with", "from", "tell",
            "me", "can", "could", "would", "should", "remember",
            "my", "is", "am", "i",
        }

        def words(text: str) -> set[str]:
            return {
                word
                for word in re.findall(r"\w+", text.casefold())
                if len(word) > 2 and word not in stop_words
            }

        query_words = words(query)
        if not query_words:
            return self.recall(limit=limit)

        # Read all facts so relevant older facts are not excluded merely
        # because newer facts were saved more recently.
        with self._connect() as db:
            rows = db.execute(
                "SELECT fact FROM facts ORDER BY id DESC"
            ).fetchall()

        ranked = []

        for position, (fact,) in enumerate(rows):
            fact_words = words(fact)
            overlap = len(query_words & fact_words)

            if overlap:
                # Prefer greater keyword overlap; use recency as a tie-breaker.
                ranked.append((overlap, -position, fact))

        ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)

        return [fact for _, _, fact in ranked[:limit]]

    def forget(self, fact: str) -> bool:
        """Delete one exact saved fact. Return whether it was deleted."""
        if not isinstance(fact, str):
            raise TypeError("Fact must be a string.")

        fact = fact.strip()
        if not fact:
            return False

        with self._connect() as db:
            cursor = db.execute(
                """
                DELETE FROM facts
                WHERE fact = ? COLLATE NOCASE
                """,
                (fact,),
            )
            return cursor.rowcount > 0

    def clear_facts(self) -> None:
        """Delete all saved facts without deleting chat history."""
        with self._connect() as db:
            db.execute("DELETE FROM facts")

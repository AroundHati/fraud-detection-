"""
InvestigationRepository — SQLite-backed persistence for completed investigations.

Architecture
~~~~~~~~~~~~
This module implements the Repository Pattern.  The rest of the application
talks to ``InvestigationRepository`` through its public API and never
imports ``sqlite3`` directly.  Swapping SQLite for PostgreSQL (or any other
backend) requires only a new repository class — no changes to callers.

Responsibilities
~~~~~~~~~~~~~~~~
- ``initialize_database()``  — create the ``storage/`` directory and
  ``investigations`` table if they do not yet exist.
- ``create_investigation()``  — insert a brand-new investigation row.
- ``save()``                 — update an existing investigation's data.
- ``get()``                  — fetch a single investigation by its ID.
- ``list()``                 — fetch all investigations (newest first).
- ``get_latest()``           — fetch the most recently created investigation.
- ``update_status()``        — update the ``status`` field.
- ``delete()``               — remove an investigation by ID.
- ``exists()``               — check whether an ID already exists.

Design Decisions
~~~~~~~~~~~~~~~~
- IDs are generated server-side in the format ``INV-YYYYMMDD-NNNN``.
- Complex objects (``results``, ``summary``) are serialised to JSON strings.
- The uploaded CSV file is never stored — only the processed results.
- All SQL uses parameterised queries to prevent injection.
- Timestamps use ISO-8601 strings (``datetime.datetime.isoformat()``).

Future Compatibility
~~~~~~~~~~~~~~~~~~~~
To migrate to PostgreSQL the only change required is a new
``InvestigationRepository`` subclass (or a standalone module) that
implements the same public API.  No caller needs to know which
backend is in use.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "storage"
_DATABASE_PATH = _STORAGE_DIR / "fraudshield.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS investigations (
    investigation_id   TEXT PRIMARY KEY,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL,
    uploaded_filename  TEXT,
    status             TEXT NOT NULL DEFAULT 'pending',
    provider_count     INTEGER NOT NULL DEFAULT 0,
    high_risk          INTEGER NOT NULL DEFAULT 0,
    medium_risk        INTEGER NOT NULL DEFAULT 0,
    low_risk           INTEGER NOT NULL DEFAULT 0,
    summary_json       TEXT,
    results_json       TEXT
)
"""

_STATUS_VALUES = frozenset({"pending", "running", "completed", "failed"})


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvestigationRepositoryError(Exception):
    """Base exception for all repository failures."""


class InvestigationNotFoundError(InvestigationRepositoryError):
    """Raised when the requested investigation does not exist."""


class DuplicateInvestigationError(InvestigationRepositoryError):
    """Raised when trying to insert an ID that already exists."""


class InvalidInvestigationError(InvestigationRepositoryError):
    """Raised when input data fails validation."""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Investigation:
    """Immutable representation of a persisted investigation."""

    investigation_id: str
    created_at: str
    updated_at: str
    uploaded_filename: Optional[str]
    status: str
    provider_count: int
    high_risk: int
    medium_risk: int
    low_risk: int
    summary: Optional[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]


@dataclass
class InvestigationCreate:
    """Data required to create a new investigation."""

    uploaded_filename: Optional[str] = None
    status: str = "pending"
    provider_count: int = 0
    high_risk: int = 0
    medium_risk: int = 0
    low_risk: int = 0
    summary: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None


@dataclass(frozen=True)
class InvestigationUpdate:
    """Mutable fields that can be written via ``save()``."""

    status: Optional[str] = None
    provider_count: Optional[int] = None
    high_risk: Optional[int] = None
    medium_risk: Optional[int] = None
    low_risk: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    results: Optional[List[Dict[str, Any]]] = None


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------

class InvestigationRepository:
    """SQLite-backed persistence for investigation records.

    Parameters
    ----------
    database_path : Path | None
        Override the default database location.  Primarily useful for
        testing — production code should use the default.

    Examples
    --------
    >>> repo = InvestigationRepository()
    >>> repo.initialize_database()
    >>> inv = repo.create_investigation(
    ...     InvestigationCreate(uploaded_filename="claims.csv")
    ... )
    >>> repo.exists(inv.investigation_id)
    True
    """

    def __init__(self, database_path: Optional[Path] = None) -> None:
        self._database_path = database_path or _DATABASE_PATH
        self._connection: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Return an open database connection, creating one if needed."""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(
                    str(self._database_path),
                    check_same_thread=False,
                )
                self._connection.row_factory = sqlite3.Row
                self._connection.execute("PRAGMA journal_mode=WAL")
                self._connection.execute("PRAGMA foreign_keys=ON")
                logger.info(
                    "[ml/repository] Connected to %s", self._database_path
                )
            except sqlite3.Error as exc:
                logger.error(
                    "[ml/repository] Failed to connect: %s", exc
                )
                raise InvestigationRepositoryError(
                    f"Database connection failed: {exc}"
                ) from exc
        return self._connection

    def close(self) -> None:
        """Close the database connection if open."""
        if self._connection is not None:
            try:
                self._connection.close()
                logger.info("[ml/repository] Connection closed")
            except sqlite3.Error as exc:
                logger.warning(
                    "[ml/repository] Error closing connection: %s", exc
                )
            finally:
                self._connection = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def initialize_database(self) -> None:
        """Create the storage directory and ``investigations`` table."""
        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                "[ml/repository] Storage directory ensured at %s",
                self._database_path.parent,
            )
        except OSError as exc:
            logger.error(
                "[ml/repository] Failed to create storage directory: %s", exc
            )
            raise InvestigationRepositoryError(
                f"Storage directory creation failed: {exc}"
            ) from exc

        try:
            conn = self._connect()
            conn.execute(_CREATE_TABLE_SQL)
            conn.commit()
            logger.info("[ml/repository] Database initialised")
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to create table: %s", exc
            )
            raise InvestigationRepositoryError(
                f"Table creation failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # ID generation
    # ------------------------------------------------------------------

    def _generate_id(self, conn: sqlite3.Connection) -> str:
        """Generate the next ``INV-YYYYMMDD-NNNN`` ID."""
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        prefix = f"INV-{today}-"

        row = conn.execute(
            "SELECT investigation_id FROM investigations "
            "WHERE investigation_id LIKE ? "
            "ORDER BY investigation_id DESC LIMIT 1",
            (f"{prefix}%",),
        ).fetchone()

        if row is None:
            seq = 1
        else:
            last_seq_str = row["investigation_id"].split("-")[-1]
            try:
                seq = int(last_seq_str) + 1
            except ValueError:
                seq = 1

        return f"{prefix}{seq:04d}"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_investigation_id(investigation_id: str) -> None:
        """Raise if *investigation_id* is malformed."""
        if not investigation_id or not isinstance(investigation_id, str):
            raise InvalidInvestigationError(
                "Investigation ID must be a non-empty string"
            )
        parts = investigation_id.split("-")
        if (
            len(parts) != 3
            or parts[0] != "INV"
            or len(parts[1]) != 8
            or not parts[1].isdigit()
            or not parts[2].isdigit()
        ):
            raise InvalidInvestigationError(
                f"Invalid investigation ID format: {investigation_id!r}. "
                "Expected INV-YYYYMMDD-NNNN"
            )

    @staticmethod
    def _validate_status(status: str) -> None:
        """Raise if *status* is not one of the allowed values."""
        if status not in _STATUS_VALUES:
            raise InvalidInvestigationError(
                f"Invalid status: {status!r}. "
                f"Must be one of {sorted(_STATUS_VALUES)}"
            )

    @staticmethod
    def _validate_counts(
        provider_count: int,
        high_risk: int,
        medium_risk: int,
        low_risk: int,
    ) -> None:
        """Raise if any risk count is negative."""
        for name, value in [
            ("provider_count", provider_count),
            ("high_risk", high_risk),
            ("medium_risk", medium_risk),
            ("low_risk", low_risk),
        ]:
            if not isinstance(value, int) or value < 0:
                raise InvalidInvestigationError(
                    f"{name} must be a non-negative integer, got {value!r}"
                )

    # ------------------------------------------------------------------
    # Row ↔ dataclass mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_investigation(row: sqlite3.Row) -> Investigation:
        """Map a database row to an ``Investigation`` dataclass."""
        return Investigation(
            investigation_id=row["investigation_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            uploaded_filename=row["uploaded_filename"],
            status=row["status"],
            provider_count=row["provider_count"],
            high_risk=row["high_risk"],
            medium_risk=row["medium_risk"],
            low_risk=row["low_risk"],
            summary=json.loads(row["summary_json"]) if row["summary_json"] else None,
            results=json.loads(row["results_json"]) if row["results_json"] else None,
        )

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------

    def create_investigation(
        self, data: InvestigationCreate
    ) -> Investigation:
        """Insert a new investigation and return the created record.

        Parameters
        ----------
        data : InvestigationCreate
            Fields for the new investigation.  An ``investigation_id`` is
            generated automatically.

        Returns
        -------
        Investigation
            The newly created record with its generated ID.

        Raises
        ------
        InvalidInvestigationError
            If *data* contains invalid values.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_status(data.status)
        self._validate_counts(
            data.provider_count, data.high_risk,
            data.medium_risk, data.low_risk,
        )

        try:
            conn = self._connect()
            inv_id = self._generate_id(conn)
            now = datetime.now(timezone.utc).isoformat()

            conn.execute(
                """
                INSERT INTO investigations
                    (investigation_id, created_at, updated_at,
                     uploaded_filename, status,
                     provider_count, high_risk, medium_risk, low_risk,
                     summary_json, results_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inv_id,
                    now,
                    now,
                    data.uploaded_filename,
                    data.status,
                    data.provider_count,
                    data.high_risk,
                    data.medium_risk,
                    data.low_risk,
                    json.dumps(data.summary) if data.summary is not None else None,
                    json.dumps(data.results) if data.results is not None else None,
                ),
            )
            conn.commit()

            logger.info(
                "[ml/repository] Created investigation %s", inv_id
            )

            return Investigation(
                investigation_id=inv_id,
                created_at=now,
                updated_at=now,
                uploaded_filename=data.uploaded_filename,
                status=data.status,
                provider_count=data.provider_count,
                high_risk=data.high_risk,
                medium_risk=data.medium_risk,
                low_risk=data.low_risk,
                summary=data.summary,
                results=data.results,
            )

        except (DuplicateInvestigationError, InvalidInvestigationError):
            raise
        except sqlite3.IntegrityError as exc:
            raise DuplicateInvestigationError(
                f"Investigation already exists: {exc}"
            ) from exc
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to create investigation: %s", exc
            )
            raise InvestigationRepositoryError(
                f"Create failed: {exc}"
            ) from exc

    def save(self, investigation: Investigation) -> None:
        """Overwrite an existing investigation record.

        Parameters
        ----------
        investigation : Investigation
            The full investigation to persist.  Must already have a valid
            ``investigation_id``.

        Raises
        ------
        InvestigationNotFoundError
            If no row with the given ID exists.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_investigation_id(investigation.investigation_id)
        self._validate_status(investigation.status)
        self._validate_counts(
            investigation.provider_count, investigation.high_risk,
            investigation.medium_risk, investigation.low_risk,
        )

        try:
            conn = self._connect()
            now = datetime.now(timezone.utc).isoformat()

            cursor = conn.execute(
                """
                UPDATE investigations
                SET    created_at        = ?,
                       updated_at        = ?,
                       uploaded_filename = ?,
                       status            = ?,
                       provider_count    = ?,
                       high_risk         = ?,
                       medium_risk       = ?,
                       low_risk          = ?,
                       summary_json      = ?,
                       results_json      = ?
                WHERE  investigation_id  = ?
                """,
                (
                    investigation.created_at,
                    now,
                    investigation.uploaded_filename,
                    investigation.status,
                    investigation.provider_count,
                    investigation.high_risk,
                    investigation.medium_risk,
                    investigation.low_risk,
                    json.dumps(investigation.summary) if investigation.summary is not None else None,
                    json.dumps(investigation.results) if investigation.results is not None else None,
                    investigation.investigation_id,
                ),
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise InvestigationNotFoundError(
                    f"Investigation not found: {investigation.investigation_id}"
                )

            logger.info(
                "[ml/repository] Saved investigation %s",
                investigation.investigation_id,
            )

        except (
            InvestigationNotFoundError,
            InvestigationRepositoryError,
            InvalidInvestigationError,
        ):
            raise
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to save investigation %s: %s",
                investigation.investigation_id,
                exc,
            )
            raise InvestigationRepositoryError(
                f"Save failed: {exc}"
            ) from exc

    def get(self, investigation_id: str) -> Investigation:
        """Fetch a single investigation by its ID.

        Parameters
        ----------
        investigation_id : str
            The investigation ID (e.g. ``INV-20260713-0001``).

        Returns
        -------
        Investigation

        Raises
        ------
        InvalidInvestigationError
            If *investigation_id* is malformed.
        InvestigationNotFoundError
            If no row matches.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_investigation_id(investigation_id)

        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()

            if row is None:
                raise InvestigationNotFoundError(
                    f"Investigation not found: {investigation_id}"
                )

            return self._row_to_investigation(row)

        except (
            InvestigationNotFoundError,
            InvestigationRepositoryError,
            InvalidInvestigationError,
        ):
            raise
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to get investigation %s: %s",
                investigation_id,
                exc,
            )
            raise InvestigationRepositoryError(
                f"Get failed: {exc}"
            ) from exc

    def list(self) -> List[Investigation]:
        """Return all investigations, newest first.

        Returns
        -------
        list[Investigation]

        Raises
        ------
        InvestigationRepositoryError
            On database failure.
        """
        try:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM investigations ORDER BY created_at DESC"
            ).fetchall()

            return [self._row_to_investigation(row) for row in rows]

        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to list investigations: %s", exc
            )
            raise InvestigationRepositoryError(
                f"List failed: {exc}"
            ) from exc

    def get_latest(self) -> Optional[Investigation]:
        """Return the most recently created investigation, or ``None``.

        Returns
        -------
        Investigation | None

        Raises
        ------
        InvestigationRepositoryError
            On database failure.
        """
        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM investigations "
                "ORDER BY created_at DESC LIMIT 1"
            ).fetchone()

            if row is None:
                return None

            return self._row_to_investigation(row)

        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to get latest investigation: %s", exc
            )
            raise InvestigationRepositoryError(
                f"Get latest failed: {exc}"
            ) from exc

    def update_status(
        self, investigation_id: str, status: str
    ) -> Investigation:
        """Update only the ``status`` field of an investigation.

        Parameters
        ----------
        investigation_id : str
            Target investigation.
        status : str
            New status value.

        Returns
        -------
        Investigation
            The updated record.

        Raises
        ------
        InvalidInvestigationError
            If *investigation_id* or *status* is invalid.
        InvestigationNotFoundError
            If no row matches.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_investigation_id(investigation_id)
        self._validate_status(status)

        try:
            conn = self._connect()
            now = datetime.now(timezone.utc).isoformat()

            cursor = conn.execute(
                """
                UPDATE investigations
                SET    status    = ?,
                       updated_at = ?
                WHERE  investigation_id = ?
                """,
                (status, now, investigation_id),
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise InvestigationNotFoundError(
                    f"Investigation not found: {investigation_id}"
                )

            logger.info(
                "[ml/repository] Updated status of %s to %s",
                investigation_id,
                status,
            )

            return self.get(investigation_id)

        except (
            InvestigationNotFoundError,
            InvestigationRepositoryError,
            InvalidInvestigationError,
        ):
            raise
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to update status for %s: %s",
                investigation_id,
                exc,
            )
            raise InvestigationRepositoryError(
                f"Update status failed: {exc}"
            ) from exc

    def delete(self, investigation_id: str) -> None:
        """Remove an investigation by ID.

        Parameters
        ----------
        investigation_id : str
            Target investigation.

        Raises
        ------
        InvalidInvestigationError
            If *investigation_id* is malformed.
        InvestigationNotFoundError
            If no row matches.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_investigation_id(investigation_id)

        try:
            conn = self._connect()
            cursor = conn.execute(
                "DELETE FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            )
            conn.commit()

            if cursor.rowcount == 0:
                raise InvestigationNotFoundError(
                    f"Investigation not found: {investigation_id}"
                )

            logger.info(
                "[ml/repository] Deleted investigation %s", investigation_id
            )

        except (
            InvestigationNotFoundError,
            InvestigationRepositoryError,
            InvalidInvestigationError,
        ):
            raise
        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to delete investigation %s: %s",
                investigation_id,
                exc,
            )
            raise InvestigationRepositoryError(
                f"Delete failed: {exc}"
            ) from exc

    def exists(self, investigation_id: str) -> bool:
        """Check whether an investigation with the given ID exists.

        Parameters
        ----------
        investigation_id : str
            The ID to check.

        Returns
        -------
        bool

        Raises
        ------
        InvalidInvestigationError
            If *investigation_id* is malformed.
        InvestigationRepositoryError
            On database failure.
        """
        self._validate_investigation_id(investigation_id)

        try:
            conn = self._connect()
            row = conn.execute(
                "SELECT 1 FROM investigations WHERE investigation_id = ?",
                (investigation_id,),
            ).fetchone()

            return row is not None

        except sqlite3.Error as exc:
            logger.error(
                "[ml/repository] Failed to check existence for %s: %s",
                investigation_id,
                exc,
            )
            raise InvestigationRepositoryError(
                f"Exists check failed: {exc}"
            ) from exc

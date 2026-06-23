import os
import sqlite3
from datetime import datetime
import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class KnowledgeRegistry:
    """Registry to keep track of ingested knowledge source files using a local SQLite database."""

    def __init__(self, db_path: str = None) -> None:
        if db_path is None:
            base_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            storage_dir = os.path.join(base_dir, "storage")
            os.makedirs(storage_dir, exist_ok=True)
            db_path = os.path.join(storage_dir, "knowledge_registry.db")

        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    file_hash TEXT,
                    ingested_at TEXT,
                    status TEXT
                )
                """
            )
            conn.commit()

    def is_file_processed(self, file_path: str, file_hash: str) -> bool:
        """Checks if a file with the given path and hash has already been successfully ingested."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_hash, status FROM registry WHERE file_path = ?",
                    (file_path,),
                )
                row = cursor.fetchone()
                if row:
                    existing_hash, status = row
                    return existing_hash == file_hash and status == "success"
                return False
        except Exception as e:
            logger.error(f"Error checking registry for {file_path}: {e}")
            return False

    def register_file(
        self, file_path: str, file_hash: str, status: str = "success"
    ) -> None:
        """Inserts or updates a file's ingestion status and hash in the registry."""
        ingested_at = datetime.utcnow().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO registry (file_path, file_hash, ingested_at, status)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(file_path) DO UPDATE SET
                        file_hash = excluded.file_hash,
                        ingested_at = excluded.ingested_at,
                        status = excluded.status
                    """,
                    (file_path, file_hash, ingested_at, status),
                )
                conn.commit()
            logger.info(f"Registered file in SQLite: {file_path} with status {status}")
        except Exception as e:
            logger.error(f"Failed to register file {file_path}: {e}")

    def get_all_registered(self) -> List[Dict[str, Any]]:
        """Retrieves all registered files from the SQLite store."""
        results = []
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_path, file_hash, ingested_at, status FROM registry"
                )
                for row in cursor.fetchall():
                    results.append(dict(row))
        except Exception as e:
            logger.error(f"Failed to fetch registered files: {e}")
        return results

import chromadb
from chromadb.config import Settings
import sqlite3
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class RAGStore:
    """manages command embeddings and retrieval using chromadb + sqlite"""

    def __init__(self, db_path: str = "lca_commands.db", chroma_path: str = "./chroma_data"):
        self.db_path = db_path
        self.chroma_path = chroma_path

        # init sqlite for metadata
        self._init_db()

        # init chromadb for embeddings
        self.chroma_client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.chroma_client.get_or_create_collection(
            name="commands",
            metadata={"hnsw:space": "cosine"}
        )

        logger.info("rag store initialized")

    def _init_db(self):
        """initialize sqlite schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                file_path TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT,
                last_used TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                intent TEXT,
                command_name TEXT,
                executed BOOLEAN,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def add_command(self, name: str, description: str, file_path: str):
        """add a new command to the store"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO commands (name, description, file_path, created_at)
                VALUES (?, ?, ?, ?)
            """, (name, description, file_path, datetime.now().isoformat()))

            conn.commit()

            # add to chromadb
            self.collection.add(
                documents=[description],
                metadatas=[{"name": name, "file_path": file_path}],
                ids=[name]
            )

            logger.info(f"added command: {name}")

        except sqlite3.IntegrityError:
            logger.warning(f"command already exists: {name}")
        finally:
            conn.close()

    def find_matching_command(self, intent: Dict[str, Any], threshold: float = 0.85) -> Optional[Dict]:
        """search for matching command using embeddings"""
        # create search query from intent
        query = json.dumps(intent)

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=1
            )

            if results['distances'][0] and results['distances'][0][0] < (1 - threshold):
                # found a match
                metadata = results['metadatas'][0][0]
                name = metadata['name']

                # get full info from sqlite
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM commands WHERE name = ?", (name,))
                row = cursor.fetchone()
                conn.close()

                if row:
                    return {
                        "name": row[1],
                        "description": row[2],
                        "file_path": row[3],
                        "usage_count": row[4]
                    }

        except Exception as e:
            logger.error(f"search failed: {e}")

        return None

    def increment_usage(self, name: str):
        """increment usage counter for command"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE commands
            SET usage_count = usage_count + 1,
                last_used = ?
            WHERE name = ?
        """, (datetime.now().isoformat(), name))
        conn.commit()
        conn.close()

    def log_command(self, query: str, intent: Dict, command_name: Optional[str], executed: bool):
        """log command execution to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO command_history (query, intent, command_name, executed, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (query, json.dumps(intent), command_name, executed, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def list_all_commands(self) -> List[Dict]:
        """get all commands ordered by usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM commands ORDER BY usage_count DESC")
        rows = cursor.fetchall()
        conn.close()

        return [{
            "name": row[1],
            "description": row[2],
            "file_path": row[3],
            "usage_count": row[4],
            "created_at": row[5],
            "last_used": row[6]
        } for row in rows]

    def get_history(self, limit: int = 10) -> List[Dict]:
        """get recent command history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM command_history
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [{
            "query": row[1],
            "intent": json.loads(row[2]),
            "command_name": row[3],
            "executed": bool(row[4]),
            "timestamp": row[5]
        } for row in rows]

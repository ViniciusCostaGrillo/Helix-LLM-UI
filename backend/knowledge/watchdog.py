import os
import time
import logging
import threading
from typing import Callable, Optional

from backend.knowledge.knowledge_builder import KnowledgeBuilderAgent
from backend.knowledge.knowledge_registry import KnowledgeRegistry

logger = logging.getLogger(__name__)


class KnowledgeWatchdog:
    """Watchdog service that periodically scans the 'knowledge_input/' folder

    and triggers builder updates for new/modified design files.
    """

    def __init__(
        self,
        watch_dir: Optional[str] = None,
        scan_interval: float = 2.0,
        on_ingest_callback: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self.base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if watch_dir is None:
            self.watch_dir = os.path.join(self.base_dir, "knowledge_input")
        else:
            self.watch_dir = watch_dir

        self.scan_interval = scan_interval
        self.on_ingest_callback = on_ingest_callback

        self.registry = KnowledgeRegistry()
        self.builder = KnowledgeBuilderAgent()
        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Starts the background directory watcher thread."""
        if self.is_running:
            logger.warning("KnowledgeWatchdog is already running.")
            return

        logger.info(f"Starting KnowledgeWatchdog on directory: {self.watch_dir}")
        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background directory watcher thread."""
        if not self.is_running:
            logger.warning("KnowledgeWatchdog is not running.")
            return

        logger.info("Stopping KnowledgeWatchdog...")
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("KnowledgeWatchdog stopped.")

    def _run_loop(self) -> None:
        while self.is_running:
            try:
                self.scan_once()
            except Exception as e:
                logger.error(f"Error during watchdog scan: {e}")
            time.sleep(self.scan_interval)

    def scan_once(self) -> None:
        """Performs a single complete scan of the watched directory structure."""
        if not os.path.exists(self.watch_dir):
            logger.debug(f"Watch directory {self.watch_dir} does not exist yet.")
            return

        logger.debug(f"Scanning directory: {self.watch_dir}")
        for root, _, files in os.walk(self.watch_dir):
            for file_name in files:
                # Skip helper files or hidden files
                if file_name.startswith(".") or file_name == ".gitkeep":
                    continue

                file_path = os.path.join(root, file_name)
                try:
                    file_hash = self.builder.generate_hash(file_path)
                    norm_path = os.path.relpath(file_path, self.base_dir).replace(
                        "\\", "/"
                    )

                    # If not processed or hash mismatched, ingest
                    if not self.registry.is_file_processed(norm_path, file_hash):
                        logger.info(
                            f"Watchdog: file changed/new detected at {norm_path}"
                        )
                        result = self.builder.ingest_file(file_path)

                        # Update registry
                        self.registry.register_file(
                            norm_path, file_hash, status="success"
                        )

                        # Trigger callback if set
                        if self.on_ingest_callback:
                            self.on_ingest_callback(norm_path, result)
                except Exception as e:
                    logger.error(
                        f"Failed to process file in watchdog scan '{file_name}': {e}"
                    )
                    # Register failure
                    try:
                        norm_path = os.path.relpath(file_path, self.base_dir).replace(
                            "\\", "/"
                        )
                        self.registry.register_file(
                            norm_path, "", status=f"failed: {str(e)}"
                        )
                    except Exception:
                        pass

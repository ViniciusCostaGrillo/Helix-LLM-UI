import os
import logging
import queue
from typing import Optional, Tuple, Dict, Any, Union
import redis

logger = logging.getLogger(__name__)

# Global singleton connection cache
_cached_redis_client = None


class MockRedis:
    """In-memory thread-safe mock client mimicking Redis list queue operations."""
    
    def __init__(self):
        self._queues: Dict[str, queue.Queue] = {}

    def ping(self) -> bool:
        return True

    def delete(self, *names: str) -> int:
        count = 0
        for name in names:
            if name in self._queues:
                del self._queues[name]
                count += 1
        return count

    def rpush(self, name: str, value: str) -> int:

        if name not in self._queues:
            self._queues[name] = queue.Queue()
        self._queues[name].put(value)
        return self._queues[name].qsize()

    def blpop(self, keys: Any, timeout: int = 0) -> Optional[Tuple[str, str]]:
        if isinstance(keys, str):
            keys = [keys]
        if not keys:
            return None
        
        import time
        start_time = time.time()
        while True:
            for name in keys:
                if name in self._queues:
                    try:
                        val = self._queues[name].get_nowait()
                        return (name, val)
                    except queue.Empty:
                        pass
            
            elapsed = time.time() - start_time
            if timeout > 0 and elapsed >= timeout:
                return None
            elif timeout <= 0:
                return None
            
            time.sleep(0.05)


    def llen(self, name: str) -> int:
        if name not in self._queues:
            return 0
        return self._queues[name].qsize()


class RedisClientManager:
    """Manages connection to the Redis container or local dev instance."""
    
    def __init__(self):
        global _cached_redis_client
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        
        if _cached_redis_client is None:
            _cached_redis_client = self._connect()
        self.client = _cached_redis_client

    def _connect(self) -> Union[redis.Redis, MockRedis]:
        logger.info(f"Attempting connection to Redis server at {self.host}:{self.port}...")
        try:
            # Set quick socket connection, timeout, and execution timeout parameters
            client = redis.Redis(
                host=self.host,
                port=self.port,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            client.ping()
            logger.info("Successfully connected to Redis.")
            return client
        except Exception as e:
            logger.warning(
                f"Failed to connect to Redis server: {str(e)}. "
                "Falling back to local in-memory MockRedis..."
            )
            return MockRedis()

    def get_client(self) -> Union[redis.Redis, MockRedis]:
        return self.client

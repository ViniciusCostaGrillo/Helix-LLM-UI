import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from backend.database.redis_client import RedisClientManager

logger = logging.getLogger(__name__)


class TaskQueue:
    """Lightweight custom task queue backed by Redis or local MockRedis."""
    
    def __init__(self):
        self.redis_manager = RedisClientManager()
        self.client = self.redis_manager.get_client()

    def enqueue(self, queue_name: str, task_type: str, payload: Dict[str, Any]) -> str:
        """Pushes a new task to the tail of the list.
        
        Returns:
            str: Generated unique task ID.
        """
        task_id = str(uuid.uuid4())
        task_envelope = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat()
        }
        
        serialized_task = json.dumps(task_envelope)
        logger.info(f"Enqueueing task: ID={task_id}, Type={task_type} to queue '{queue_name}'")
        self.client.rpush(queue_name, serialized_task)
        return task_id

    def dequeue(self, queue_name: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Blocks until a task is available at the head of the list, then pops it.
        
        Returns:
            Optional[Dict[str, Any]]: Deserialized task envelope or None if timed out.
        """
        # blpop returns a tuple: (list_key, value) or None
        result = self.client.blpop(queue_name, timeout=timeout)
        if not result:
            return None
        
        _, serialized_task = result
        try:
            task_envelope = json.loads(serialized_task)
            return task_envelope
        except Exception as e:
            logger.error(f"Failed to deserialize task from queue: {e}")
            return None

    def length(self, queue_name: str) -> int:
        """Returns the number of elements in the queue."""
        return self.client.llen(queue_name)

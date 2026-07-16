import json
from pathlib import Path
import uuid


def load_or_create_instance_id(state_path: Path) -> uuid.UUID:
    if state_path.exists():
        return uuid.UUID(json.loads(state_path.read_text(encoding="utf-8"))["agent_instance_id"])
    instance_id = uuid.uuid4()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"agent_instance_id": str(instance_id)}), encoding="utf-8"
    )
    return instance_id

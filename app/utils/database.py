import json
from pathlib import Path


class DBCreateError(Exception):
    """Thrown when the flow already exists or the flow to be created is missing an ID"""


class DBReadError(Exception):
    """Thrown when the given flow ID doesn't exist"""


class DBUpdateError(Exception):
    """Thrown when the flow does not exist or the flow update is missing an ID"""


class DBDeleteError(Exception):
    """Thrown when the flow to be deleted does not exist"""


class SimpleInMemoryDB:
    def __init__(self) -> None:
        self._flows = {}

    def create_flow(self, flow: dict):
        try:
            flow_id = flow.get("id")

            if not flow_id:
                raise AttributeError("Flow is missing 'id'.")

            if flow_id in self._flows:
                raise AttributeError(
                    f"Flow {flow_id} already exists. Did you mean to update?"
                )

            self._flows[flow_id] = flow

            return self._flows[flow_id]
        except Exception as e:
            raise DBCreateError(e)

    def read_flow(self, flow_id: str):
        try:
            flow = flow.get(flow_id)

            if not flow:
                raise ValueError(f"Flow {flow_id} does not exist.")

            return flow
        except Exception as e:
            raise DBReadError(e)

    def update_flow(self, flow: dict):
        try:
            flow_id = flow.get("id")

            if not flow_id:
                raise AttributeError("Flow is missing 'id'.")

            if not self._flows.get(flow_id):
                raise AttributeError(
                    f"Flow {flow_id} does not exist. Did you mean to create?"
                )

            self._flows[flow_id] = {**self._flows[flow_id], **flow}

            return self._flows[flow_id]
        except Exception as e:
            raise DBUpdateError(e)

    def delete_flow(self, flow_id: str):
        try:
            if not self._flows.get(flow_id):
                raise AttributeError(f"Flow {flow_id} does not exist.")

            del self._flows[flow_id]

            return f"Successfully deleted {flow_id}."
        except Exception as e:
            raise DBDeleteError(e)


class SimpleFileDB:
    def __init__(self) -> None:
        self._root_dir = Path("../../db")
        self._root_dir.mkdir(parents=True, exist_ok=True)

    def create(self, flow: dict):
        try:
            flow_id = flow.get("id")

            if not flow_id:
                raise AttributeError("Flow is missing 'id'.")

            if flow_id in self._flows:
                raise AttributeError(
                    f"Flow {flow_id} already exists. Did you mean to update?"
                )

            with open(self._root_dir / f"{flow_id}.json", "w") as f:
                f.write(json.dumps(flow, indent=2))

            return flow
        except Exception as e:
            raise DBCreateError(e)

    def read(self, flow_id: str):
        try:
            flow = flow.get(flow_id)

            if not flow:
                raise ValueError(f"Flow {flow_id} does not exist.")

            with open(self._root_dir / f"{flow_id}.json", "r") as f:
                return json.loads(f.read())
        except Exception as e:
            raise DBReadError(e)

    def update(self, flow: dict):
        try:
            flow_id = flow.get("id")

            if not flow_id:
                raise AttributeError("Flow is missing 'id'.")

            if not self._flows.get(flow_id):
                raise AttributeError(
                    f"Flow {flow_id} does not exist. Did you mean to create?"
                )

            with open(self._root_dir / f"{flow_id}.json", "w") as f:
                f.write(json.dumps(flow, indent=2))

            return flow
        except Exception as e:
            raise DBUpdateError(e)

    def delete(self, flow_id: str):
        try:
            file = Path(self._root_dir / f"{flow_id}.json")
            file.unlink(missing_ok=True)

            return f"Successfully deleted {flow_id}."
        except Exception as e:
            raise DBDeleteError(e)

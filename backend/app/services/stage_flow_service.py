from datetime import datetime, timedelta
from uuid import uuid4


STAGE2_ACCESS_TTL_MINUTES = 10


class StageFlowService:
    def __init__(self):
        self._active_flows: dict[str, datetime] = {}

    def create_stage2_access(self) -> str:
        flow_id = str(uuid4())

        expires_at = (
            datetime.utcnow()
            + timedelta(
                minutes=STAGE2_ACCESS_TTL_MINUTES
            )
        )

        self._active_flows[flow_id] = expires_at

        return flow_id

    def validate_stage2_access(
        self,
        flow_id: str,
    ) -> bool:
        expires_at = self._active_flows.get(
            flow_id
        )

        if expires_at is None:
            return False

        if datetime.utcnow() > expires_at:
            del self._active_flows[flow_id]
            return False

        return True


stage_flow_service = StageFlowService()
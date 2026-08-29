from fastapi import Header, HTTPException, status

from backend.app.services.stage_flow_service import (
    stage_flow_service,
)


def require_stage2_access(
    stage2_access_token: str = Header(
        ...,
        alias="X-Stage2-Access-Token",
    ),
):
    is_valid = (
        stage_flow_service
        .validate_stage2_access(
            stage2_access_token
        )
    )

    if not is_valid:
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail={
                "message": (
                    "Stage 2 access denied. "
                    "Complete Stage 1 URL verification first."
                )
            },
        )

    return stage2_access_token
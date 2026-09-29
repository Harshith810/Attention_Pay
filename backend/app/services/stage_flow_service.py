from datetime import datetime, timedelta, timezone
import hashlib
import secrets

from sqlalchemy.orm import Session

from backend.app.models.stage2_access_token import (
    Stage2AccessToken,
)


STAGE2_ACCESS_TTL_MINUTES = 10


class StageFlowService:
    """
    Shared, database-backed Stage 2 authorization state.
    """

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(
            token.encode("utf-8")
        ).hexdigest()

    def create_stage2_access(
        self,
        db: Session,
    ) -> str:
        """
        Generate a secure Stage 2 access token,
        store only its hash in PostgreSQL,
        and return the raw token to the client.
        """

        raw_token = secrets.token_urlsafe(32)

        now = datetime.now(timezone.utc)

        access_token = Stage2AccessToken(
            token_hash=self._hash_token(raw_token),
            created_at=now,
            expires_at=(
                now
                + timedelta(
                    minutes=STAGE2_ACCESS_TTL_MINUTES
                )
            ),
            is_revoked=False,
        )

        db.add(access_token)
        db.commit()

        return raw_token

    def validate_stage2_access(
        self,
        db: Session,
        token: str,
    ) -> bool:
        """
        Validate a Stage 2 access token against
        shared PostgreSQL state.
        """

        token_hash = self._hash_token(token)

        access_token = (
            db.query(Stage2AccessToken)
            .filter(
                Stage2AccessToken.token_hash
                == token_hash
            )
            .first()
        )

        if access_token is None:
            return False

        now = datetime.now(timezone.utc)

        if access_token.is_revoked:
            return False

        if now >= access_token.expires_at:
            db.delete(access_token)
            db.commit()
            return False

        return True


stage_flow_service = StageFlowService()
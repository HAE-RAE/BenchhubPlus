"""Service layer for securely storing and retrieving model credentials."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Dict, Iterable, List

from sqlalchemy.orm import Session

from .db import ModelCredential
from .schemas import ModelInfo
from .security import decrypt_secret, encrypt_secret, hash_api_key


@dataclass
class StoredCredential:
    """Lightweight representation of a stored credential."""

    id: int
    credential_hash: str
    model_name: str
    api_base: str
    model_type: str


class CredentialService:
    """Service responsible for persisting and retrieving credentials."""

    def __init__(self, db: Session):
        self.db = db

    def register_models(self, models: Iterable[ModelInfo]) -> List[StoredCredential]:
        """Persist credentials for the provided models."""

        stored: List[StoredCredential] = []
        for model in models:
            stored.append(self._register_single_model(model))
        # Flush to guarantee IDs are assigned without committing yet.
        self.db.flush()
        return stored

    def _register_single_model(self, model: ModelInfo) -> StoredCredential:
        credential_hash = hash_api_key(model.api_key)
        encrypted = encrypt_secret(model.api_key)
        now = datetime.now(UTC)

        existing: ModelCredential | None = (
            self.db.query(ModelCredential)
            .filter(ModelCredential.credential_hash == credential_hash)
            .one_or_none()
        )

        if existing:
            existing.model_name = model.name
            existing.api_base = model.api_base
            existing.model_type = model.model_type
            existing.encrypted_api_key = encrypted
            existing.updated_at = now
            record = existing
        else:
            record = ModelCredential(
                model_name=model.name,
                model_type=model.model_type,
                api_base=model.api_base,
                credential_hash=credential_hash,
                encrypted_api_key=encrypted,
                created_at=now,
            )
            self.db.add(record)

        # Ensure the primary key is populated for new records
        self.db.flush([record])

        return StoredCredential(
            id=int(record.id),
            credential_hash=credential_hash,
            model_name=record.model_name,
            api_base=record.api_base,
            model_type=record.model_type or "",
        )

    def hydrate_models(self, models: Iterable[Dict[str, str]]) -> List[Dict[str, str]]:
        """Attach decrypted API keys to models using stored credentials."""

        hydrated: List[Dict[str, str]] = []
        for model in models:
            credential_id = model.get("credential_id")
            if credential_id is None:
                raise ValueError("Model payload missing credential_id")

            record = self.db.get(ModelCredential, int(credential_id))
            if record is None:
                raise ValueError(f"Credential {credential_id} not found")

            api_key = decrypt_secret(record.encrypted_api_key)
            record.last_used_at = datetime.now(UTC)
            hydrated_model = dict(model)
            hydrated_model["api_key"] = api_key
            hydrated.append(hydrated_model)

        self.db.flush()
        return hydrated

    def get_api_key(self, credential_id: int) -> str:
        """Return decrypted API key for a credential identifier."""

        record = self.db.get(ModelCredential, int(credential_id))
        if record is None:
            raise ValueError(f"Credential {credential_id} not found")

        record.last_used_at = datetime.now(UTC)
        self.db.flush()
        return decrypt_secret(record.encrypted_api_key)

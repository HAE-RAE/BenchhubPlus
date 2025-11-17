import pytest

from apps.core.credential_service import CredentialService
from apps.core.db import ModelCredential
from apps.core.schemas import ModelInfo


def test_register_and_hydrate_credentials(test_db):
    service = CredentialService(test_db)

    model_info = ModelInfo(
        name="secure-model",
        api_base="https://api.secure.example", 
        api_key="top-secret-key",
        model_type="openai",
    )

    stored_records = service.register_models([model_info])
    assert stored_records

    stored = stored_records[0]
    assert stored.credential_hash != "top-secret-key"

    db_record = test_db.query(ModelCredential).filter(ModelCredential.id == stored.id).one()
    assert db_record.encrypted_api_key != "top-secret-key"

    hydrated = service.hydrate_models([
        {
            "name": model_info.name,
            "api_base": model_info.api_base,
            "model_type": model_info.model_type,
            "credential_id": stored.id,
        }
    ])

    assert hydrated[0]["api_key"] == "top-secret-key"

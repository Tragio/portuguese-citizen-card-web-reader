from typing import Any

from pydantic import BaseModel


class ReadRequest(BaseModel):
    cms: str
    agent: str


class ReadResponse(BaseModel):
    AgentToken: str
    AuthTokenId: str
    AuthDataRequested: str
    AuthGovCertificate: str
    AuthSignature: str


class DeliveryRequest(BaseModel):
    sod: str
    id: str
    nonce: str
    iv: str
    key: str
    foto: str | None = None


class DeliveryResponse(BaseModel):
    success: bool
    data: dict[str, Any]
    error: str | None = None

####################################################################################################
# Description: Read and decrypt data from the Citizen Card.
# Author: Tragio.pt
####################################################################################################

import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from models import (
    DeliveryRequest,
    DeliveryResponse,
    ReadRequest,
    ReadResponse,
)
from utils.card_attributes import CitizenCardAttributes
from utils.ciphers import Ciphers
from utils.helpers import convert_image_to_base64

app = FastAPI()

# Remove in production; this is for development only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ciphers
ciphers = Ciphers(settings.KEY_STORE_PATH, settings.KEY_STORE_PASSWORD)


@app.post("/read/request", response_model=ReadResponse)
async def read_request(request: ReadRequest) -> ReadResponse:
    try:
        # Get agent token
        agent_token = request.agent

        # Get frontend generated token; should be generated every time to avoid CSRF
        auth_token = request.cms

        # Data to be requested
        auth_data_requested = "id;foto"

        # Get the government certificate
        gov_certificate = ciphers.get_certificate()

        # Sign data with the agent's private key
        auth_signature = ciphers.sign_data(agent_token, auth_token, auth_data_requested)

        response = ReadResponse(
            AgentToken=agent_token,
            AuthTokenId=auth_token,
            AuthDataRequested=auth_data_requested,
            AuthGovCertificate=gov_certificate,
            AuthSignature=auth_signature,
        )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/read/delivery", response_model=DeliveryResponse)
async def read_delivery(request: DeliveryRequest) -> DeliveryResponse:
    try:
        # Make type checker happy
        if not isinstance(ciphers.private_key, rsa.RSAPrivateKey):
            raise TypeError("private_key must be an instance of RSAPrivateKey")

        # Decrypt the AES key using RSA with OAEP (matching Java's RSA/ECB/OAEPWithSHA-256AndMGF1Padding)
        encrypted_aes_key = base64.b64decode(request.key)
        decrypted_key = ciphers.private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA1()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        # Base64 decode the encrypted data and IV
        encrypted_data = base64.b64decode(request.id)
        iv = base64.b64decode(request.iv)

        # Use the decrypted AES key to decrypt data
        decrypted_data = ciphers.decrypt_aes_gcm(decrypted_key, iv, encrypted_data)

        # Use the decrypted AES key to decrypt the photo
        photo_base64 = None
        if request.foto:
            photo = base64.b64decode(request.foto)
            decrypted_photo = ciphers.decrypt_aes_gcm(decrypted_key, iv, photo)
            photo_base64 = convert_image_to_base64(decrypted_photo)

        card_attributes = CitizenCardAttributes(decrypted_data)

        if not card_attributes:
            raise HTTPException(
                status_code=500,
                detail="Error parsing Citizen Card data",
            )

        response_data = {
            "card": card_attributes.as_dict(),
            "photo": photo_base64,
        }

        return DeliveryResponse(success=True, data=response_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve the frontend (is at the end to avoid conflicts with the other routes)
app.mount("/", StaticFiles(directory="frontend", html=True))

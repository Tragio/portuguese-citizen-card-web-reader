import base64

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import pkcs12


class Ciphers:
    def __init__(self, key_store_path: str, key_store_password: str):
        """
        Load the private key and certificate from a PKCS#12 keystore.
        """

        if not key_store_path:
            raise ValueError("Key store path is required.")

        if not key_store_password:
            raise ValueError("Key store password is required.")

        # Load the PKCS#12 keystore
        with open(key_store_path, "rb") as p12_file:
            p12_data = p12_file.read()

        # Convert password to bytes
        password_bytes = (
            key_store_password.encode("utf-8") if key_store_password else None
        )
        # Load the private key and certificate from the PKCS#12 keystore
        self.private_key, self.certificate, _ = pkcs12.load_key_and_certificates(
            p12_data, password_bytes
        )

        if self.private_key is None:
            raise ValueError("No private key found in the PKCS#12 keystore.")
        if self.certificate is None:
            raise ValueError("No certificate found in the PKCS#12 keystore.")

    def get_certificate(self) -> str:
        """
        Return certificate as base64 encoded DER bytes
        """
        if self.certificate is None:
            raise ValueError("Certificate is not available.")

        cert_der = self.certificate.public_bytes(encoding=serialization.Encoding.DER)
        return base64.b64encode(cert_der).decode("utf-8")

    def sign_data(self, agent: str, cms: str, auth_data: str) -> str:
        """
        Signs data using SHA256withRSA.
        Data is signed in the order: agent + cms + auth_data.
        """
        if not [agent, cms, auth_data]:
            raise ValueError("Agent, CMS, and auth_data are required.")

        data_to_sign = (
            agent.encode("utf-8") + cms.encode("utf-8") + auth_data.encode("utf-8")
        )
        signature = self.private_key.sign(
            data_to_sign, padding.PKCS1v15(), hashes.SHA256()
        )
        return base64.b64encode(signature).decode("utf-8")

    def decrypt_aes_gcm(self, key: bytes, iv: bytes, encrypted_data: bytes) -> bytes:
        try:
            # Take only the first 16 bytes of the decrypted RSA key for AES-128
            aes_key = key[:16]

            # Create a GCM mode context with a 128-bit tag (16 bytes)
            gcm = modes.GCM(iv, min_tag_length=16)

            # Create cipher instance
            cipher = Cipher(algorithms.AES(aes_key), gcm, backend=default_backend())

            # Create the decryptor
            decryptor = cipher.decryptor()

            # Assume that the last 16 bytes of encrypted_data are the tag.
            ciphertext = encrypted_data[:-16]
            tag = encrypted_data[-16:]

            # Decrypt the bulk of the ciphertext.
            plaintext = decryptor.update(ciphertext)

            plaintext += decryptor.finalize_with_tag(tag)

            return plaintext

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

import base64
import io

from PIL import Image


def convert_image_to_base64(decrypted_photo: bytes) -> str:
    """
    Convert a decrypted JP2 image to base64 encoded JPEG
    """

    # Find JP2 signature and extract data
    jp2_start = decrypted_photo.find(b"\x00\x00\x00\x0cjP  ")
    if jp2_start == -1:
        raise ValueError("Invalid JP2 format")

    # Changed from p2_data to jp2_data
    jp2_data = decrypted_photo[jp2_start:]  #

    # Convert using PIL
    image = Image.open(io.BytesIO(jp2_data))
    output = io.BytesIO()
    image.save(output, format="JPEG")
    jpeg_data = output.getvalue()

    # Encode to base64 with proper header
    return f"data:image/jpeg;base64,{base64.b64encode(jpeg_data).decode('ascii')}"

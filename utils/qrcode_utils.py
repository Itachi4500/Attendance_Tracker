import qrcode
import cv2
import numpy as np
from PIL import Image
import io

def generate_qr_code(data: str) -> bytes:
    """
    Generate a QR code for the given data.
    Returns QR code as bytes.
    """
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    return buf.getvalue()

def decode_qr_from_image(uploaded_image) -> str:
    """
    Decode QR code from an uploaded image.
    Returns the decoded data as string.
    """
    image = Image.open(uploaded_image)
    img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img_array)
    return data

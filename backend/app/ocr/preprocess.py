import cv2
import numpy as np

def preprocess_receipt(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image from {image_path}")

    height, width = img.shape[:2]

    # Upscale small/narrow receipts for better OCR
    if width < 1000:
        scale = 1000 / width
        img = cv2.resize(img, (int(width * scale), int(height * scale)),
                         interpolation=cv2.INTER_CUBIC)
    elif width > 2400:
        scale = 2400 / width
        img = cv2.resize(img, (int(width * scale), int(height * scale)),
                         interpolation=cv2.INTER_AREA)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise gently
    denoised = cv2.fastNlMeansDenoising(gray, h=8)

    # Sharpen to make text crisper
    kernel = np.array([[0, -1,  0],
                       [-1, 5, -1],
                       [0, -1,  0]])
    sharpened = cv2.filter2D(denoised, -1, kernel)

    return sharpened
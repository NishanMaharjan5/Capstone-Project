import cv2
import numpy as np

def preprocess_receipt(image_path: str):
    """
    Preprocess receipt image for better OCR results
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image from {image_path}")
    
    # Resize if too large (better for OCR)
    height, width = img.shape[:2]
    if width > 1200:
        scale = 1200 / width
        new_width = 1200
        new_height = int(height * scale)
        img = cv2.resize(img, (new_width, new_height))
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    
    # Denoise
    denoised = cv2.medianBlur(enhanced, 3)
    
    # Adaptive thresholding (works better for varying lighting)
    thresh = cv2.adaptiveThreshold(denoised, 255, 
                                   cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY, 11, 2)
    
    # Invert if needed (black text on white background)
    # Count black vs white pixels
    black_pixels = np.sum(thresh == 0)
    white_pixels = np.sum(thresh == 255)
    
    if white_pixels > black_pixels:  # If mostly white, invert
        thresh = cv2.bitwise_not(thresh)
    
    return thresh





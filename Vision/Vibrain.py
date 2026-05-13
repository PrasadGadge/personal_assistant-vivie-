import os
import time
import base64
from TextToSpeech.Fast_DF_TTS import speak

try:
    import cv2
    _HAS_CV2 = True
except Exception:
    cv2 = None
    _HAS_CV2 = False

try:
    from google import genai
    from google.genai import types
    _HAS_GENAI = True
except Exception:
    genai = None
    types = None
    _HAS_GENAI = False

# --- CONFIGURATION ---
# Gemini 2.0 Flash is the best for real-time vision in 2026
MODEL_ID = "gemini-2.0-flash"

def vision_brain(image_path):
    """
    Analyzes the image using Google Gemini 2.0 Flash.
    """
    if not _HAS_GENAI:
        return "Vision system unavailable (google-genai not installed)."
    # The SDK automatically looks for GEMINI_API_KEY or GOOGLE_API_KEY in .env
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        return "Error: Gemini API Key missing in .env file."

    client = genai.Client(api_key=api_key)

    try:
        # Load image from the saved file
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Generate response
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[
                "Describe what you see in this image clearly for a voice assistant response. Keep it brief.",
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            ]
        )
        
        if response.text:
            return response.text.strip()
        else:
            return "I can see the image, but I'm having trouble describing it."

    except Exception as e:
        print(f"Gemini Vision Error: {e}")
        return "My vision system is currently experiencing a technical glitch."

def capture_image_and_save(image_path="captured_image.jpg"):
    if not _HAS_CV2:
        print("[Vision] OpenCV not available; skipping image capture.")
        return False
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Camera not found!")
        return False

    # 1.5s delay is perfect for auto-focus/exposure in 2026 webcams
    time.sleep(1.5) 
    
    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()

    if ret:
        cv2.imwrite(image_path, frame)
        return True
    return False

if __name__ == "__main__":
    print(f"--- Vivie Vision System Active (Using {MODEL_ID}) ---")
    while True:
        x = input("\nEnter command (e.g., 'see'): ").lower()
        if "see" in x or "what is this" in x:
            print("[VIVIE]: One moment, let me look...")
            
            img_path = "captured_image.jpg"
            if capture_image_and_save(img_path):
                # Gemini handles files/bytes directly, so we pass the path
                answer = vision_brain(img_path)
                print(f"\nVivie: {answer}")
                speak(answer)

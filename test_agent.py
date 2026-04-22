# import customtkinter as ctk
# import threading
# import time

# # --- 1. Global App Settings ---
# ctk.set_appearance_mode("dark")       # Options: "system" (standard), "dark", "light"
# ctk.set_default_color_theme("blue")   # Options: "blue" (standard), "green", "dark-blue"

# class VivieApp(ctk.CTk):
#     def __init__(self):
#         super().__init__()

#         # --- 2. Window Configuration ---
#         self.title("Vivie AI Assistant")
#         self.geometry("600x700") # Width x Height
#         self.minsize(400, 500)

#         # Make the layout stretchable
#         self.grid_columnconfigure(0, weight=1)
#         self.grid_rowconfigure(0, weight=1)

#         # --- 3. Chat Display Area ---
#         # This is where the conversation history will show up
#         self.chat_display = ctk.CTkTextbox(self, state="disabled", wrap="word", font=("Helvetica", 15))
#         self.chat_display.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")

#         # --- 4. User Input Field ---
#         self.input_field = ctk.CTkEntry(self, placeholder_text="Type a message to Vivie...", font=("Helvetica", 14), height=40)
#         self.input_field.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="ew")
        
#         # Bind the 'Enter' key so you don't always have to click the button
#         self.input_field.bind("<Return>", lambda event: self.handle_user_input())

#         # --- 5. Send Button ---
#         self.send_button = ctk.CTkButton(self, text="Send", command=self.handle_user_input, font=("Helvetica", 14, "bold"), width=80, height=40)
#         self.send_button.grid(row=1, column=1, padx=(0, 20), pady=(0, 20))

#         # Greet the user on startup
#         self.display_message("Vivie", "Systems online. How can I assist you today?")

#     # --- 6. Core Functions ---
#     def display_message(self, sender, message):
#         """Helper function to cleanly print text to the chat box."""
#         self.chat_display.configure(state="normal") # Unlock the box to type
#         self.chat_display.insert("end", f"{sender}: {message}\n\n")
#         self.chat_display.configure(state="disabled") # Lock it back
#         self.chat_display.see("end") # Auto-scroll to the bottom

#     def handle_user_input(self):
#         """Grabs the text from the input field and triggers the AI."""
#         user_text = self.input_field.get().strip()
#         if not user_text:
#             return # Don't send empty messages

#         # Show user message and clear the input box
#         self.display_message("You", user_text)
#         self.input_field.delete(0, "end")

#         # CRITICAL: We run the AI response in a separate thread.
#         # If we don't do this, the UI will freeze while Vivie processes the AI API.
#         threading.Thread(target=self.get_vivie_response, args=(user_text,)).start()

#     def get_vivie_response(self, user_text):
#         """This acts as a placeholder for your actual AI backend logic."""
#         # Right now, this just simulates "thinking" for 2 seconds
#         # Later, you will replace the time.sleep() with your actual Gemini/AI API call!
        
#         time.sleep(1.5) # Simulating API processing time
        
#         # Temporary hardcoded responses just to test the UI flow
#         if "hello" in user_text.lower():
#             reply = "Hello there! I am ready to work."
#         elif "upgrade" in user_text.lower():
#             reply = "I am loving this new desktop interface!"
#         else:
#             reply = f"I received your message: '{user_text}'. I am currently a UI prototype, but my brain will be connected soon!"

#         self.display_message("Vivie", reply)

# # --- 7. Run the App ---
# if __name__ == "__main__":
#     app = VivieApp()
#     app.mainloop()







# test_stt.py — run this directly to test
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000

print("Loading model...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Model loaded.")

print("Recording 3 seconds... speak now")
audio = sd.rec(
    int(3 * SAMPLE_RATE),
    samplerate = SAMPLE_RATE,
    channels   = 1,
    dtype      = 'int16'
)
sd.wait()
print("Recording done.")

audio_flat  = audio.flatten()
audio_float = audio_flat.astype(np.float32) / 32768.0

print("Transcribing...")
segments, _ = model.transcribe(
    audio_float,
    language  = "en",
    beam_size = 3
)
text = " ".join(s.text.strip() for s in segments)
print(f"You said: '{text}'")
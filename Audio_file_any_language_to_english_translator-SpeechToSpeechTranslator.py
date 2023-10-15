from tkinter import Tk, Label, Button, filedialog, StringVar, OptionMenu, messagebox, ttk, DoubleVar
import threading
import time
from PIL import Image, ImageTk
import pygame
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from gtts import gTTS
import torchaudio
import logging

class CustomTranslator:
    def __init__(self):
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")

    def translate_audio(self, input_path, output_path):
        try:
            # Load input audio file using torchaudio
            input_waveform, input_sampling_rate = torchaudio.load(input_path)

            # Ensure the input audio has a proper frame rate
            if input_sampling_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=input_sampling_rate, new_freq=16000)
                input_waveform = resampler(input_waveform)

            # Process the input audio with the Whisper processor
            input_features = self.processor(input_waveform.numpy(), sampling_rate=16000, return_tensors="pt")

            # Generate token ids
            predicted_ids = self.model.generate(input_features["input_features"])

            # Decode token ids to text
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            # Save the translated text to an MP3 file
            tts = gTTS(transcription, lang='en')
            tts.save(output_path)

            # Log success
            logging.info(f"Translation successful for {input_path}. Translated text: {transcription}")

        except Exception as e:
            # Log errors
            logging.error(f"Error processing audio: {e}")
            raise  # Re-raise the exception
            
    def play_audio(self, audio_path):
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        
    def stop_audio(self):
        pygame.mixer.music.stop()
        
class TranslatorGUI:
    def __init__(self, master):
        master.title("Audio file from any language to english translator - S2S translator")
        master.geometry("540x580")  # Increased height for progress bar and label

        # Load and display banner image
        banner_image = Image.open("Flag_of_Palestine.svg.png")
        banner_image = banner_image.resize((480, 200))
        banner_photo = ImageTk.PhotoImage(banner_image)
        banner_label = Label(master, image=banner_photo)
        banner_label.image = banner_photo
        banner_label.pack()

        # Create a frame to center everything
        center_frame = ttk.Frame(master)
        center_frame.pack(expand=True)

        self.label_input = Label(center_frame, text="Select Audio File:")
        self.label_input.pack(side="top", pady=10)

        self.browse_button = Button(center_frame, text="Browse", command=self.browse)
        self.browse_button.pack(side="top", pady=10)
        
        self.label_file_title = Label(center_frame, text="Selected File Title:")
        self.label_file_title.pack(side="top", pady=5)
        
        self.translate_button = Button(center_frame, text="Translate", command=self.translate)
        self.translate_button.pack(side="top", pady=10)

        self.play_button = Button(center_frame, text="Play Selected File", command=self.play_selected)
        self.play_button.pack(side="top", pady=5)

        self.stop_button = Button(center_frame, text="Stop playing Selected File", command=self.stop_playing)
        self.stop_button.pack(side="top", pady=5)

        self.progress_bar = ttk.Progressbar(center_frame, variable=DoubleVar(), mode='indeterminate')
        self.progress_bar.pack(side="top", pady=5)

        self.label_status = Label(center_frame, text="")
        self.label_status.pack(side="top", pady=5)

        self.audio_path = ""
    
    def browse(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.*")])
        print(f"Selected file: {file_path}")
        self.audio_path = file_path
        
        # Display file title
        file_title = file_path.split("/")[-1]  # Extract the file name from the path
        self.label_file_title.config(text=f"Selected File Title: {file_title}")

    def translate(self):
        if self.audio_path:
            output_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
            if output_path:
                translation_thread = threading.Thread(target=self.run_translation, args=(output_path,))
                translation_thread.start()
                self.progress_bar.start()
                self.label_status.config(text="Translation in progress...")

    def run_translation(self, output_path):
        translator_instance = CustomTranslator()
        translator_instance.translate_audio(self.audio_path, output_path)
        
        PlayOutputFile = CustomTranslator()
        PlayOutputFile.play_audio(output_path)
        
        self.progress_bar.stop()
        self.label_status.config(text="Translation complete!")
        
        # Show success message
        messagebox.showinfo("Success", f"Translation saved successfully at:\n{output_path}")
        
    def play_selected(self):
        if self.audio_path:
            translator_instance = CustomTranslator()
            translator_instance.play_audio(self.audio_path)

    def stop_playing(self):
        translator_instance = CustomTranslator()
        translator_instance.stop_audio()
        
# Initialize pygame mixer
pygame.mixer.init()

# Example usage
if __name__ == "__main__":
    root = Tk()
    app = TranslatorGUI(root)
    root.mainloop()

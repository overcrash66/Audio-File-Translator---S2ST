from tkinter import Tk, Label, Button, filedialog, StringVar, OptionMenu, messagebox, ttk, DoubleVar
import threading
from PIL import Image, ImageTk
import pygame
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from gtts import gTTS
import torchaudio
import logging
import os
import requests

class SpeechRecognizer:
    def __init__(self, language="en", rate=48000, retries=3, api_key="AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw", timeout=30,
                 error_messages_callback=None):
        self.language = language
        self.rate = rate
        self.api_key = api_key
        self.retries = retries
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback

    def __call__(self, data):
        try:
            for i in range(self.retries):
                url = f"http://www.google.com/speech-api/v2/recognize?client=chromium&lang={self.language}&key={self.api_key}"
                headers = {"Content-Type": "audio/x-flac rate=%d" % self.rate}

                try:
                    resp = requests.post(url, data=data, headers=headers, timeout=self.timeout)
                    # print(resp.text)
                except requests.exceptions.ConnectionError:
                    try:
                        resp = httpx.post(url, data=data, headers=headers, timeout=self.timeout)
                    except httpx.exceptions.NetworkError:
                        continue

                for line in resp.content.decode('utf-8').split("\n"):
                    try:
                        line = json.loads(line)
                        line = line['result'][0]['alternative'][0]['transcript']
                        return line[:1].upper() + line[1:]
                    except:
                        # no result
                        continue

        except KeyboardInterrupt:
            if self.error_messages_callback:
                self.error_messages_callback("Cancelling all tasks")
            else:
                print("Cancelling all tasks")
            return

        except Exception as e:
            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)
            return


class SentenceTranslator:
    def __init__(self, src, dst, patience=-1, timeout=30, error_messages_callback=None):
        self.src = src
        self.dst = dst
        self.patience = patience
        self.timeout = timeout
        self.error_messages_callback = error_messages_callback

    def __call__(self, sentence):
        try:
            translated_sentence = []
            # handle the special case: empty string.
            if not sentence:
                return None
            translated_sentence = self.GoogleTranslate(sentence, src=self.src, dst=self.dst, timeout=self.timeout)
            fail_to_translate = translated_sentence[-1] == '\n'
            while fail_to_translate and self.patience:
                translated_sentence = self.GoogleTranslate(translated_sentence, src=self.src, dst=self.dst,
                                                            timeout=self.timeout).text
                if translated_sentence[-1] == '\n':
                    if self.patience == -1:
                        continue
                    self.patience -= 1
                else:
                    fail_to_translate = False

            return translated_sentence

        except KeyboardInterrupt:
            if self.error_messages_callback:
                self.error_messages_callback("Cancelling all tasks")
            else:
                print("Cancelling all tasks")
            return

        except Exception as e:
            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)
            return

    def GoogleTranslate(self, text, src, dst, timeout=30):
        url = 'https://translate.googleapis.com/translate_a/'
        params = 'single?client=gtx&sl=' + src + '&tl=' + dst + '&dt=t&q=' + text
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://translate.google.com', }

        try:
            response = requests.get(url + params, headers=headers, timeout=timeout)
            if response.status_code == 200:
                response_json = response.json()[0]
                length = len(response_json)
                translation = ""
                for i in range(length):
                    translation = translation + response_json[i][0]
                return translation
            return

        except requests.exceptions.ConnectionError:
            with httpx.Client() as client:
                response = client.get(url + params, headers=headers, timeout=timeout)
                if response.status_code == 200:
                    response_json = response.json()[0]
                    length = len(response_json)
                    translation = ""
                    for i in range(length):
                        translation = translation + response_json[i][0]
                    return translation
                return

        except KeyboardInterrupt:
            if self.error_messages_callback:
                self.error_messages_callback("Cancelling all tasks")
            else:
                print("Cancelling all tasks")
            return

        except Exception as e:
            if self.error_messages_callback:
                self.error_messages_callback(e)
            else:
                print(e)
            return

class CustomTranslator:
    def __init__(self):
        self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
        self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")
        self.target_language = StringVar()
        self.target_language.set("en")  # Default target language

        
    def transcribe_audio(self, input_path, target_language, output_path):
        try:
            # Load input audio file using torchaudio
            input_waveform, input_sampling_rate = torchaudio.load(input_path)
            
            forced_decoder_ids = self.processor.get_decoder_prompt_ids(language=target_language, task="translate")
            
            # Ensure the input audio has a proper frame rate
            if input_sampling_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=input_sampling_rate, new_freq=16000)
                input_waveform = resampler(input_waveform)
        
            # Process the input audio with the processor
            input_features = self.processor(input_waveform.numpy(), sampling_rate=16000, return_tensors="pt")

            # Generate token ids
            predicted_ids = self.model.generate(input_features["input_features"], forced_decoder_ids=forced_decoder_ids)

            # Decode token ids to text
            transcription = self.processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]

            # print("Translated Text:", transcription)
            
            # Use SpeechRecognizer for translation (modify as needed)
            translator = SentenceTranslator(src="en", dst=target_language)
            translated_text = translator(transcription)

            # Generate final audio output from translated text
            self.generate_audio(translated_text, output_path, target_language)

            logging.info(f"Processing successful. Translated text: {translated_text}")
           
        except Exception as e:
            logging.error(f"Error transcribing audio: {e}")
            raise

    def generate_audio(self, text, output_path, target_language):
        tts = gTTS(text, lang=target_language)
        tts.save(output_path)

    def play_audio(self, audio_path):
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

    def stop_audio(self):
        pygame.mixer.music.stop()

class TranslatorGUI:
    def __init__(self, master):
        master.title("Audio File Translator - S2ST")
        master.geometry("640x680")

        banner_image = Image.open("Flag_of_Palestine.svg.png")
        banner_image = banner_image.resize((480, 200))
        banner_photo = ImageTk.PhotoImage(banner_image)
        banner_label = Label(master, image=banner_photo)
        banner_label.image = banner_photo
        banner_label.pack()

        center_frame = ttk.Frame(master)
        center_frame.pack(expand=True)

        self.label_input = Label(center_frame, text="Select Audio File:")
        self.label_input.pack(side="top", pady=10)

        self.browse_button = Button(center_frame, text="Browse", command=self.browse)
        self.browse_button.pack(side="top", pady=10)

        self.label_file_title = Label(center_frame, text="Selected File Title:")
        self.label_file_title.pack(side="top", pady=5)

        # Language selection drop-down menu for target language
        self.label_target_language = Label(center_frame, text="Select Target Language:")
        self.label_target_language.pack(side="top", pady=5)

        languages = ["en", "es", "fr", "de", "ja", "ko", "tr", "ar", "ru", "he", "hi", "it", "pt"]
        self.translator = CustomTranslator()
        self.target_language_dropdown = OptionMenu(center_frame, self.translator.target_language, *languages)
        self.target_language_dropdown.pack(side="top", pady=5)

        # Language selection drop-down menu for gTTS language
        # self.label_tts_language = Label(center_frame, text="Select gTTS Language:")
        # self.label_tts_language.pack(side="top", pady=5)

        # self.tts_language_dropdown = OptionMenu(center_frame, self.translator.tts_language, *languages)
        # self.tts_language_dropdown.pack(side="top", pady=5)

        self.translate_button = Button(center_frame, text="Translate", command=self.translate)
        self.translate_button.pack(side="top", pady=10)

        # self.play_button = Button(center_frame, text="Play Translated File", command=self.play_translated)
        # self.play_button.pack(side="top", pady=5)

        self.stop_button = Button(center_frame, text="Stop Playing Translated File", command=self.stop_playing)
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

        file_title = file_path.split("/")[-1]
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
        translator_instance.transcribe_audio(self.audio_path, self.translator.target_language.get(), output_path)

        PlayOutputFile = CustomTranslator()
        PlayOutputFile.play_audio(output_path)

        self.progress_bar.stop()
        self.label_status.config(text="Translation complete!")

        messagebox.showinfo("Success", f"Translation saved successfully at:\n{output_path}")

    def play_translated(self):
        if self.audio_path:
            output_path = "temp_translated_output.mp3"
            translator_instance = CustomTranslator()
            translator_instance.transcribe_audio(self.audio_path, self.translator.target_language.get(), output_path)
            translator_instance.play_audio(output_path)

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

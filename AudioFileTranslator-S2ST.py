"""
###############################################################################################################################
#                                        Audio File Translator - S2ST                                                         #
###############################################################################################################################
# File:         AudioFileTranslator-S2ST.py
# Author:       WAEL SAHLI
# Date:         October 18, 2023
#  
# Description:   Audio file translator, Speech To Speech Translator is a tool 
#                that allows you to translate the content of an Audio file using:
#                 - S2T: OpenAI's Whisper multilingual
#                 - T2T: Google Speech Recognizer
#                 - TTS: python gtts
#
# Version:      1.3
#
# Change Log:
# October 14, 2023     1.0 - Initial version
# October 17, 2023     1.1 - Better memory management
#                          - Add support for large audio files translation
#                          - Add FFMpeg to split large audio files and avoid out of memory errors and bad translation quality
#                          - Add audio to mp3 conversion tool
#                          - Fix freezing issue with stop play Translated audio file 
#                          - Update GUI style
# October 18, 2023     1.2 - Fix audio to mp3 conversion + Add MP4 to mp3 converter + Add youtube downloader
# October 19, 2023     1.3 - Minor GUI updates, fix extract audio from video exception
##############################################################################################################################
"""
from tkinter import Tk, Label, Button, filedialog, StringVar, OptionMenu, messagebox, ttk, DoubleVar, Menu, Entry
import threading
from PIL import Image, ImageTk
import pygame
from transformers import WhisperProcessor, WhisperForConditionalGeneration
from gtts import gTTS
import torchaudio
import logging
import os
import requests
import math
from pydub import AudioSegment
from pytube import YouTube
from pydub.utils import mediainfo
import subprocess
import time

def YouTubeDownloader():
    new_window = Tk()
    new_window.title("YouTube Downloader")
    new_window.resizable(False, False)
    new_window.attributes('-fullscreen', False)
    new_window.attributes("-topmost", True)
    def download():
        url = url_entry.get()
        format_selected = "mp4"

        if not url:
            messagebox.showerror("Error", "Please enter a valid YouTube URL.")
            return

        try:
            yt = YouTube(url)
            video_title = yt.title

            output_path = f"{video_title}.mp4"
            subprocess.run(["ffmpeg", "-i", yt.streams.filter(file_extension='mp4').first().download(), output_path])

            messagebox.showinfo("Success", f"Download complete!\nFile saved as {output_path}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    url_label = Label(new_window, text="YouTube URL:")
    url_label.grid(row=0, column=0, padx=10, pady=10)

    url_entry = Entry(new_window, width=40)
    url_entry.grid(row=0, column=1, padx=10, pady=10)

    download_button = Button(new_window, text="Download", command=download)
    download_button.grid(row=2, column=0, columnspan=2, pady=10)
    new_window.mainloop()
    
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
        self.processor = None
        self.model = None
        self.target_language = StringVar()
        self.target_language.set("en")  # Default target language

    def load_model(self):
        # Load the model if it hasn't been loaded
        if self.processor is None:    
            self.processor = WhisperProcessor.from_pretrained("openai/whisper-large-v2")
            
        if self.model is None:
            self.model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-large-v2")
        

    def unload_model(self):
        # Unload the model if it has been loaded
        if self.processor is not None:
            del self.processor
            self.processor = None
        
        if self.model is not None:
            del self.model
            self.model = None  
        
    def process_audio_chunk(self, input_path, target_language, chunk_idx, output_path):
        try:
            self.load_model()
            
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
            
            Translation_chunk_output_path = f"{output_path}_Translation_chunk{chunk_idx + 1}.mp3"
            
            # Use SpeechRecognizer for translation (modify as needed)
            if target_language != "en":
                translator = SentenceTranslator(src="en", dst=target_language)
                translated_text = translator(transcription)

                # Generate final audio output from translated text
                self.generate_audio(translated_text, Translation_chunk_output_path, target_language)
                logging.info(f"Processing successful. Translated text: {translated_text}")
            else:
                self.generate_audio(transcription, Translation_chunk_output_path, target_language)
                logging.info(f"Processing successful. Translated text: {transcription}")

            # Log success
            logging.info(f"Translation successful for {input_path}. Translated text: {transcription}")

        except Exception as e:
            # Log errors
            logging.error(f"Error processing audio: {e}")
            raise  # Re-raise the exception
        
        finally:
            # Ensure model is unloaded and memory is cleared even if an exception occurs
            self.unload_model()    

    def generate_audio(self, text, output_path, target_language):
        tts = gTTS(text, lang=target_language, slow=False)
        tts.save(output_path)

    def play_audio(self, audio_path): # disabled for now
        pygame.mixer.init()
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

    def stop_audio(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        try:    
            pygame.mixer.music.stop()
        except:
            pass
            

class TranslatorGUI:
    def __init__(self, master):
        master.title("Audio File Translator - S2ST")
        master.geometry("500x580")
        master.maxsize(700, 700)
        master.attributes('-fullscreen', False)
        self.label = Label(master, text="Audio File Translator - S2ST", font=("Arial", 12, "bold"), fg="red", pady=18)
        self.label.pack()
        
        # Menu Bar
        menubar = Menu(master)
        master.config(menu=menubar)

        # File Menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Convert Audio file to MP3", command=self.Convert_Audio_Files)
        file_menu.add_command(label="Extract audio from Video", command=self.extract_audio)
        
        file_menu.add_command(label="Youtube Downloader", command=YouTubeDownloader)
        file_menu.add_command(label="Exit", command=master.destroy)

        # Help Menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        banner_image = Image.open("Flag_of_Palestine.svg.png")
        banner_image = banner_image.resize((200, 100))
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
        self.translator_instance = CustomTranslator()  # Use the same instance for translation
        self.target_language_dropdown = OptionMenu(center_frame, self.translator_instance.target_language, *languages)
        self.target_language_dropdown.pack(side="top", pady=5)
        
        self.translate_button = Button(center_frame, text="Translate", command=self.translate)
        self.translate_button.pack(side="top", pady=10)

        self.stop_button = Button(center_frame, text="Stop Playing Translated File", command=self.stop_playing)
        self.stop_button.pack(side="top", pady=5)

        self.progress_bar = ttk.Progressbar(center_frame, variable=DoubleVar(), mode='indeterminate')
        self.progress_bar.pack(side="top", pady=10)

        self.label_status = Label(center_frame, text="")
        self.label_status.pack(side="top", pady=5)
        
        self.audio_path = ""
    
    def extract_audio(self):
        input_video = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
        if input_video != '':
            input_video_file = input_video.split("/")[-1]
            input_video_file = str(input_video_file).replace('.mp4','')
            output_audio = f"{input_video_file}.mp3"
            
            command = [
                'ffmpeg',
                '-i', input_video,
                '-vn',  # Disable video recording
                '-ac', '2',  # Set the number of audio channels to 2
                '-ar', '44100',  # Set the audio sample rate to 44100 Hz
                '-ab', '192k',  # Set the audio bitrate to 192 kbps
                '-f', 'mp3',  # Set the output format to mp3
                output_audio
            ]

            # Run the command
            subprocess.run(command)
            
            print(f"Conversion successful: {output_audio}")
            messagebox.showinfo("Info", f"Conversion successful: {output_audio}")
        
    def Convert_Audio_Files(self):
        def is_mp3(file_path):
            try:
                result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=format_name', '-of', 'default=noprint_wrappers=1:nokey=1', file_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                return result.stdout.strip() == 'mp3'
            except Exception as e:
                print(f"Error checking file format: {e}")
                messagebox.showinfo("Error", f"Error checking file format: {e}")
                return False

        def convert_to_mp3(input_file, output_file):
            try:
                subprocess.run(['ffmpeg', '-i', input_file, '-codec:a', 'libmp3lame', output_file], check=True)
                print(f"Conversion successful: {output_file}")
                messagebox.showinfo("Info", f"Conversion successful: {output_file}")
            except subprocess.CalledProcessError as e:
                print(f"Error converting to MP3: {e}")
                messagebox.showinfo("Error", f"Error converting to MP3: {e}")

        def Start(Input_file_path):
            input_file = Input_file_path
            file_title = Input_file_path.split("/")[-1]
            output_file = f"{file_title}-Converted.mp3"

            if not is_mp3(input_file):
                print(f"The input file is not a valid MP3. Converting to MP3...")
                convert_to_mp3(input_file, output_file)
            else:
                print("The input file is already an MP3.")
                messagebox.showinfo("Error", "The input file is already an MP3.")
        
        Input_file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.*")])
        
        if Input_file_path != '':
            Start(Input_file_path)
    
    def show_about(self):
        messagebox.showinfo("About", "Audio File Translator - S2ST v1.3\n\nCreated by Wael Sahli")
    
    def browse(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3")])
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
        try:
            input_file = self.audio_path
            # Get the duration of the input audio file
            ffprobe_cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{input_file}"'
            input_duration = float(subprocess.check_output(ffprobe_cmd, shell=True))
            
            # Set the maximum duration for each chunk (30 seconds in this case)
            max_chunk_duration = 30

            # Calculate the number of chunks required
            num_chunks = int(input_duration / max_chunk_duration)
            print("num_chunks: "+str(num_chunks))
            chunk_files = []  # List to store individual chunk files
            Translation_chunk_files = []
            
            # Split the audio file into chunks and process each chunk
            for chunk_idx in range(num_chunks):
                
                # Calculate start and end times for each chunk
                start_time = chunk_idx * max_chunk_duration
                end_time = min((chunk_idx + 1) * max_chunk_duration, input_duration)

                # Use a consistent naming pattern for chunk files
                chunk_output_path = f"{output_path}_chunk{chunk_idx + 1}.mp3"

                # Split the audio file into a chunk
                self.split_audio_chunk(self.audio_path, chunk_output_path, start_time, end_time)
                
                # Process the audio chunk using the translator instance
                self.translator_instance.process_audio_chunk(chunk_output_path, self.translator_instance.target_language.get(),chunk_idx, output_path)
                chunk_files.append(chunk_output_path)
                
                Translation_chunk_output_path = f"{output_path}_Translation_chunk{chunk_idx + 1}.mp3"
                Translation_chunk_files.append(Translation_chunk_output_path)
                
            # Merge individual chunk files into the final output file
            final_output_path = f"{output_path}"
            self.merge_audio_files(Translation_chunk_files, final_output_path)

            # Play the final merged audio file
            self.translator_instance.play_audio(final_output_path)

            # Cleanup: Delete individual chunk files
            self.delete_chunk_files(chunk_files)
            self.delete_chunk_files(Translation_chunk_files)

            self.progress_bar.stop()
            self.label_status.config(text="Translation complete!")

            messagebox.showinfo("Success", f"Translation saved successfully at:\n{final_output_path}")

        except Exception as e:
            logging.error(f"Error during translation: {e}")
            raise

    # Function to split audio into a chunk using ffmpeg
    def split_audio_chunk(self, input_path, output_path, start_time, end_time):
        ffmpeg_cmd = f'ffmpeg -i "{input_path}" -ss {start_time} -to {end_time} -c copy "{output_path}"'
        subprocess.call(ffmpeg_cmd, shell=True)

    def get_audio_duration(self, file_path):
        audio_info = mediainfo(file_path)
        duration_ms_str = audio_info.get("duration", "0")
        duration_ms = float(duration_ms_str)
        duration_seconds = duration_ms / 1000
        return duration_seconds

    def merge_audio_files(self, input_files, output_file):
        merged_audio = AudioSegment.silent(duration=0)
        # print("Merge started")
        for input_file in input_files:
            try:
                # Load the chunk audio
                chunk_audio = AudioSegment.from_file(input_file, format="mp3")

                # Append the chunk audio to the merged audio
                merged_audio += chunk_audio
            except FileNotFoundError as e:
                logging.warning(f"Error merging audio file {input_file}: {e}")
            except Exception as e:
                logging.error(f"Error merging audio file {input_file}: {e}")

        # Export the merged audio to the final output file
        try:
            merged_audio.export(output_file, format="mp3")
        except Exception as e:
            logging.error(f"Error exporting merged audio: {e}")

    def delete_chunk_files(self, files):
        for file in files:
            try:
                os.remove(file)
            except FileNotFoundError as e:
                logging.warning(f"Error deleting file {file}: {e}")
            except Exception as e:
                logging.error(f"Error deleting file {file}: {e}")

    def stop_playing(self):
        self.translator_instance.stop_audio()

# Main function to run the GUI
def run_gui():
    root = Tk()
    app = TranslatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_gui()

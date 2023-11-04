"""
###############################################################################################################################
#										 Audio File Translator - S2ST														  #
###############################################################################################################################
# File:			AudioFileTranslator-S2ST.py
# Author:		WAEL SAHLI
#
# Description:	 Audio file translator, Speech To Speech Translator is a tool 
#				 that allows you to translate the content of an Audio file using:
#				  - S2T: OpenAI's Whisper multilingual
#				  - T2T: Google Speech Recognizer
#				  - TTS: python gtts
#
# Version:		1.6
#
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
import librosa
import torch
import customtkinter
import httpx
from CTkMenuBar import * #Addon Downloaded from #https://github.com/Akascape/CTkMenuBar

customtkinter.set_appearance_mode("System")	 # Modes: system (default), light, dark
customtkinter.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green
def YouTubeDownloader():
	new_window = customtkinter.CTk()
	new_window.iconbitmap("Flag.ico")
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
	
	url_label = customtkinter.CTkLabel(new_window, text="YouTube URL:")
	url_label.grid(row=0, column=0, padx=10, pady=10)

	url_entry = customtkinter.CTkEntry(new_window, width=500)
	url_entry.grid(row=0, column=1, padx=10, pady=10)

	download_button = customtkinter.CTkButton(new_window, text="Download", command=download)
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
		self.target_language.set("en")	# Default target language
		self.label_translated_text = StringVar()
		self.text_translated = StringVar()
		
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
			
			# Load input audio file using librosa
			input_waveform, input_sampling_rate = librosa.load(input_path, sr=None, mono=True)

			# Convert NumPy array to PyTorch tensor if needed
			if not isinstance(input_waveform, torch.Tensor):
				input_waveform = torch.tensor(input_waveform)
			
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
				return translated_text
			else:
				self.generate_audio(transcription, Translation_chunk_output_path, target_language)
				logging.info(f"Processing successful. Translated text: {transcription}")
				return transcription

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
		master.geometry("500x860")
		master.iconbitmap("Flag.ico")
		self.menubar = CTkMenuBar(master=master)
		self.file = self.menubar.add_cascade("File")
		self.help = self.menubar.add_cascade("Help")

		filedropdown = CustomDropdownMenu(widget=self.file,width=100)
		filedropdown.add_option(option="Convert Audio file to MP3",command=self.Convert_Audio_Files)
		filedropdown.add_option(option="Extract audio from Video", command=self.extract_audio)
		filedropdown.add_option(option="Youtube Downloader", command=YouTubeDownloader)
		filedropdown.add_option(option="Exit", command=master.destroy)

		helpdropdown = CustomDropdownMenu(widget=self.help,width=50)
		helpdropdown.add_option(option="About", command=self.show_about)
		# master.iconbitmap(r"Resources\icon.ico") Define icon to set window icon
		master.title("Audio File Translator - S2ST")
		master.geometry("500x860")
		master.minsize(500, 860)
		master.maxsize(700, 900)
		master.attributes('-fullscreen', False)
		self.label = customtkinter.CTkLabel(master=master,text="Audio File Translator - S2ST",font=("Arial", 18, "bold"),
							   text_color="red")
		self.label.pack(pady=18)

		try:
			banner_image = Image.open("Flag.png")
			banner_image = banner_image.resize((200, 100))
			banner_photo = ImageTk.PhotoImage(banner_image)
			banner_label = Label(master, image=banner_photo)
			banner_label.image = banner_photo
			banner_label.pack()
		except:
			pass

		self.label_input = customtkinter.CTkLabel(master, text="Select Audio File:")
		self.label_input.pack(side="top", pady=10)

		self.browse_button = customtkinter.CTkButton(master, text="Browse", command=self.browse)
		self.browse_button.pack(side="top", pady=10)

		self.label_file_title = customtkinter.CTkLabel(master, text="Selected File Title:",font=("Arial", 12, "bold"),text_color="green")
		self.label_file_title.pack(side="top", pady=5)

		# Language selection drop-down menu for target language
		self.label_target_language = customtkinter.CTkLabel(master, text="Select Target Language:")
		self.label_target_language.pack(side="top", pady=5)

		languages = ["en", "es", "fr", "de", "ja", "ko", "tr", "ar", "ru", "he", "hi", "it", "pt"]

		self.translator_instance = CustomTranslator() # Use the same instance for translation
		self.stringvarlanguage = customtkinter.StringVar()
		self.target_language_dropdown = customtkinter.CTkOptionMenu(master,variable=self.stringvarlanguage,
															   values=languages)
		self.target_language_dropdown.pack(side="top", pady=5)
		self.target_language_dropdown.set(languages[0])
		
		self.translate_button = customtkinter.CTkButton(master, text="Translate", command=self.translate)
		self.translate_button.pack(side="top", pady=10)

		self.stop_button = customtkinter.CTkButton(master, text="Stop Playing Translated File",
												   command=self.stop_playing)
		self.stop_button.pack(side="top", pady=5)

		self.progress_bar = customtkinter.CTkProgressBar(master, variable=DoubleVar(), mode='indeterminate')
		self.progress_bar.pack(side="top", pady=10)

		self.label_status = customtkinter.CTkLabel(master, text="")
		self.label_status.pack(side="top", pady=5)
		
		self.audio_path = ""

		self.label_translated_text = customtkinter.CTkLabel(master, text="Translated Text:",font=("Arial", 12, "bold"),text_color="green")
		self.label_translated_text.pack(side="top", pady=5)
		
		self.text_translated = customtkinter.CTkTextbox(master, height=200, width=400)
		self.text_translated.pack(side="top", pady=5)
		
		self.save_button = customtkinter.CTkButton(master, text="Save Text Translation", command=self.save_translation)
		self.save_button.pack(side="left", pady=5)
		self.save_button.pack_forget()
		
		self.clear_button = customtkinter.CTkButton(master, text="Clear", command=self.clear_text)
		self.clear_button.pack(side="right", pady=5)
		
	def translate(self):
		if self.audio_path:
			output_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 Files", "*.mp3")])
			if output_path:
				translation_thread = threading.Thread(target=self.run_translation, args=(output_path,))
				translation_thread.start()
				self.progress_bar.start()
				self.label_status.configure(text="Translation in progress...",font=("Arial", 12, "bold"),text_color="red")	 

	def extract_audio(self):
		input_video = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4")])
		if input_video != '':
			input_video_file = input_video.split("/")[-1]
			input_video_file = str(input_video_file).replace('.mp4','')
			output_audio = f"{input_video_file}.mp3"
			
			command = [
				'ffmpeg',
				'-i', input_video,
				'-vn',	# Disable video recording
				'-ac', '2',	 # Set the number of audio channels to 2
				'-ar', '44100',	 # Set the audio sample rate to 44100 Hz
				'-ab', '192k',	# Set the audio bitrate to 192 kbps
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
		messagebox.showinfo("About", "Audio File Translator - S2ST v1.6\n\nCreated by Wael Sahli\n\nSpecial Thanks TO: 7gxycn08 for GUI updates")
	
	def browse(self):
		file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3")])
		print(f"Selected file: {file_path}")
		self.audio_path = file_path

		file_title = file_path.split("/")[-1]
		if file_title != "":
			self.label_file_title.configure(text=f"Selected File Title: {file_title}")
	
	def clear_text(self):
		# Clear the text in the text widget
		self.text_translated.configure(state='normal')
		self.text_translated.delete("1.0", "end")
		self.text_translated.configure(state='disabled')
	
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
				# print(self.target_language_dropdown.get())

				translation_result = self.translator_instance.process_audio_chunk(chunk_output_path,
															 self.target_language_dropdown.get(),
															 chunk_idx, output_path)
				chunk_files.append(chunk_output_path)

				# Update translated text in text widget
				self.text_translated.configure(state='normal')
				self.text_translated.insert('end', f"{translation_result}\n\n")
				self.text_translated.configure(state='disabled')
				
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
			self.label_status.configure(text="Translation complete!",font=("Arial", 12, "bold"),text_color="green")
			self.save_button.pack()
			
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
	
	def save_translation(self):
		translation_text = self.text_translated.get("1.0", "end-1c")
		if translation_text:
			output_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
			if output_path:
				try:
					with open(output_path, "w", encoding="utf-8") as file:
						file.write(translation_text)
					print(f"Translation saved to: {output_path}")
				except Exception as e:
					print(f"Error saving translation to file: {e}")
			else:
				print("Save operation cancelled.")
	
# Main function to run the GUI
def run_gui():
	root = customtkinter.CTk()
	app = TranslatorGUI(root)
	root.mainloop()

if __name__ == "__main__":
	run_gui()

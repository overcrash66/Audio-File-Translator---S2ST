# Audio file translator - Speech To Speech and Speech to text Translator - Online mode (No api keys are needed )

Audio file translator, Speech To Speech Translator is a tool that allows you to translate the content of an Audio file using:
 - S2T: OpenAI's Whisper multilingual [whisper-large-v2](https://huggingface.co/openai/whisper-large-v2),
 - T2T: Google Speech Recognizer
 - TTS: Python gtts

## Features

1. Multi-Language Support

   - The translator supports various target languages, including English, Spanish, French, German, Japanese, Korean, Turkish, Arabic, Russian, Hebrew, Hindi, Italian, and Portuguese.

2. YouTube Downloader

   - Integrated YouTube downloader for downloading audio from YouTube videos. Users can choose between MP3 and MP4 formats.

3. Audio Conversion Tools

   - Convert Audio to MP3: Converts audio files to the MP3 format.
   - Extract Audio from Video: Extracts audio from video files and saves it as an MP3 file.

4. Memory Management Improvements

   - Improved memory management for better performance, especially with large audio files.
   - Added support for translating large audio files without running out of memory.

5. FFMpeg Integration

   - FFMpeg is utilized to split large audio files, preventing out-of-memory errors and enhancing translation quality.

6. GUI Improvements

   - Updated GUI style for a more user-friendly experience.
   - Stop button to halt the playback of translated audio files.

7. Version History

  - v1.0: Initial version.
  - v1.1: Improved memory management, support for large audio files, FFMpeg integration, audio-to-MP3 conversion, and GUI updates.
  - v1.2: Fixed audio-to-MP3 conversion, added MP4 to MP3 converter, and introduced YouTube downloader.
  - v1.3: Minor GUI updates, fix extract audio from video exception.
  - v1.4: Add missing Flag image, fix exception with Torchaudio backend not being able to handle the specified URI and format.
  - v1.5: 7gxycn08 GUI updates
  - v1.6: New GUI updates, Add Voice to text translation,
         Added a portable version (No python or package installs are needed, 
         you need to copy and replace 'AudioFileTranslator-S2ST.py' file from 'main' folder to '/AudioFileTranslatror-Portable/resources')
  - v1.7: New GUI updates.
  - V1.8: Some Youtube Downloader fixes and improvements.
  - V1.9: Add a tool who replaces mp4 Video file Audio with translation audio file. 
         (Go to: file > Replace Audio in Video)
         - Improve text translation by fixing a bug of duplicate successive words, except for English.
  - V2.0:- Fix Arabic translated text to be shown from right to left on textBox.
         - Fix Save to text file arabic translated text to be shown from right to left.
         - Fix a bug of duplicate successive words for English language.
  - V2.1:
        - Improve code readability.  
        - Add load model to GPU if available.  
        - Minor GUI updates.
        - Remove portable version.

## Requirements

Make sure you have the following dependencies installed:

- Python >= 3.10
- Pip (Python package installer)
- [FFmpeg](https://ffmpeg.org/download.html) #Should be installed manually 


## Dependencies

- pygame: Used for audio playback.
- transformers: OpenAI's Whisper for speech-to-text translation.
- gtts: Google Text-to-Speech for text-to-speech conversion.
- torchaudio: Audio processing library.
- pydub: Audio processing library.
- pytube: YouTube video download library.
- PIL: Python Imaging Library for image processing.
- Customtkinter
- httpx
- CTkMenuBar

## Usage

1- Install using pip
```
pip install audio-file-translator

```

2- Run
```
audio-file-translator

```

## Or Manual installation

1- Clone the repository:
```bash
git clone https://github.com/overcrash66/Audio-File-Translator---S2ST.git
```

2- Navigate to folder:
```
cd Audio-File-Translator---S2ST
```

3- Create a vitrual env:

```
py -3.10 -m venv venv
```

```
venv\Scripts\activate
```

4- Install the required Python packages using:

```bash
pip install -r requirements.txt
```

5- Run the Script:

```bash
python audio_file_translator.py
```

## Options:

1- File Menu:
- Convert Audio file to MP3
- Extract audio from Video
- YouTube Downloader
- Replace Audio in Video
- Exit

2- Help Menu:
- About

3- Select Audio File:
- Browse to choose the input audio file.

4- Select Target Language:
- Choose the target language from the dropdown menu.

5- Translate:
- Click the "Translate" button to start the translation process.

6- Stop Playing Translated File:
- Click the "Stop Playing Translated File" button to stop audio playback.

## GUI Preview

![Redesigned (Custom)](Screenshot2.png)

## Configuration

- You can customize the translation model and other settings by modifying the script.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) - see the [LICENSE](LICENSE) file for details.

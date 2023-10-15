# Audio file translator - Speech To Speech Translator

Audio file translator, Speech To Speech Translator is a simple tool that allows you to translate the content of an Audio file using:
 - OpenAI's Whisper ASR,
 - Google Speech Recognizer
 - TTS models.

## Features

- Translate the content of an Audio file from any language to:
    - English: en
    - Spanish: es
    - French: fr
    - German: de
    - Japanese: ja
    - Korean: ko
    - Turkish: tr
    - Arabic: ar
    - Russian: ru
    - Hebrew: he
    - Hindi: hi
    - Italian: it
    - Portuguese: pt

- User-friendly GUI for easy interaction.

## Requirements

Make sure you have the following dependencies installed:

- Python 3.x
- Pip (Python package installer)

Install the required Python packages using:

```bash
pip install -r requirements.txt
```

## Usage

Run the Script:

```bash
python AudioFileTranslator-S2ST.py
```

Select an MP3 File:
	Click the "Browse" button to choose an MP3 file.
	You can use 'segment_1.mp3' as example (with a spanish voice)

Select ouput language as needed. (FYI default language is English)

Translate Speech:
	Click the "Translate" button to translate the speech to English.

Save Translated Audio:
	Choose a save location using the "Save" dialog.


## GUI Preview

![AudioFileTranslator-S2ST GUI](Screenshot2.png)

## Configuration

- You can customize the translation model and other settings by modifying the script.

## Logging

- The script logs translation results and errors to a log file named log.txt.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT) - see the [LICENSE](LICENSE) file for details.
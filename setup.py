from setuptools import setup, find_packages

setup(
    name='audio-file-translator',
    url='https://github.com/overcrash66/Audio-File-Translator---S2ST',
    author='Wael SAHLI',
    author_email='speech2speechtranslation@gmail.com',
    description='audio-file-translator. For Windows, macOS, and Linux, on Python 3',
    version='2.1',
    keywords="gui audio video translator",
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'Pillow',
        'pygame',
        'transformers',
        'gtts',
        'torchaudio',
        'pydub',
        'pytube',
        'librosa',
        'torch',
        'customtkinter',
        'httpx',
        'CTkMenuBar'
    ],
    entry_points={
        'console_scripts': [
            'audio-file-translator=AudioFileTranslator_S2ST.main:run_gui',
        ],
    },
)


from setuptools import find_packages, setup

setup(
    name='ajman_job_connect',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'SpeechRecognition',
        'pyttsx3',
        'ffmpeg-python',
        'pymongo',
        'pandas',
        'sentence_transformers',
        'bcrypt',
        'pdfminer.six',
        'Pillow',
    ],
)

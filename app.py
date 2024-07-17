from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import pyttsx3
import ffmpeg
import os
from pymongo import MongoClient
import pandas as pd
from recommender_system import JobRecommender

app = Flask(__name__)

# MongoDB connection
MONGO_URI = "mongodb+srv://dda:ddainternship@data-jobs.l7kc2ku.mongodb.net/?retryWrites=true&w=majority&appName=data-jobs"

# Increase timeout settings
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=50000, connectTimeoutMS=50000, socketTimeoutMS=50000)

try:
    db = client['data']  
    collection = db['jobs']  

    jobs_data = list(collection.find())
    jobs_df = pd.DataFrame(jobs_data)

    print(jobs_df.columns)

    job_recommender = JobRecommender(jobs_df)

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    # Handle the error or re-raise it
    raise


r = sr.Recognizer()

def speaktext(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        audio_file = request.files['audio_data']
        audio_file.save('temp_audio.webm')

        input_audio = ffmpeg.input('temp_audio.webm')
        output_audio = ffmpeg.output(input_audio, 'temp_audio.wav')
        ffmpeg.run(output_audio)

        with sr.AudioFile('temp_audio.wav') as source:
            audio = r.record(source)
        
        mytext = r.recognize_google(audio)
        mytext = mytext.lower()

        speaktext(mytext)

        os.remove('temp_audio.webm')
        os.remove('temp_audio.wav')

        recommendations = job_recommender.recommend_jobs(mytext)
        
        return jsonify({"transcription": mytext, "recommendations": recommendations})
    
    except sr.RequestError as e:
        return jsonify({"error": f"Could not request results; {e}"}), 500
    
    except sr.UnknownValueError:
        return jsonify({"error": "Unknown error occurred"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process_text', methods=['POST'])
def process_text():
    try:
        data = request.get_json()
        job_title = data['jobTitle'].lower()

        recommendations = job_recommender.recommend_jobs(job_title)
        
        return jsonify({"transcription": job_title, "recommendations": recommendations})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

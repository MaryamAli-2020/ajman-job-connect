from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from pymongo import MongoClient
import pandas as pd
from recommender_system import JobRecommender  # This is for the recommender system
from applibs import *  # This is for the cv upload feature
import speech_recognition as sr
import pyttsx3
import ffmpeg
import os
import bcrypt
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64
import gridfs

app = Flask(__name__)
app.secret_key = "developer123"

MONGO_URI = "mongodb+srv://dda:ddainternship@data-jobs.l7kc2ku.mongodb.net/?retryWrites=true&w=majority&appName=data-jobs"

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=50000, connectTimeoutMS=50000, socketTimeoutMS=50000)

try:
    db = client['data']
    users_collection = db['users']
    jobs_collection = db['jobs']

    jobs_data = list(jobs_collection.find())
    jobs_df = pd.DataFrame(jobs_data)

    print(jobs_df.columns)

    job_recommender = JobRecommender(jobs_df)

except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

r = sr.Recognizer()

def speaktext(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'], active_page='index')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password'].encode('utf-8')
        if '@' in login:
            user = users_collection.find_one({"email": login})
        else:
            user = users_collection.find_one({"username": login})
        
        if user and bcrypt.checkpw(password, user['password']):
            session['username'] = user['username']
            return redirect(url_for('index'))
        flash('Invalid username/email or password')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        existing_user = users_collection.find_one({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            flash('User with this username or email already exists')
        else:
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            users_collection.insert_one({"username": username, "email": email, "password": hashed_password})
            session['username'] = username
            return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = users_collection.find_one({'username': session['username']})
    if not user:
        return redirect(url_for('login'))
    
    cv_info = user.get('cv_info', {})
    
    return render_template('profile.html', user=user, cv_info=cv_info, active_page='profile')

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' in session:
        user_id = session['username']
        phone = request.form.get('phone')
        skills = request.form.get('skills')
        education = request.form.get('education')

        users_collection.update_one(
            {'username': user_id},
            {'$set': {
                'cv_info.phone': phone,
                'cv_info.skills': skills,
                'cv_info.education': education
            }}
        )
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    else:
        return redirect(url_for('login'))

@app.route('/upload_cv', methods=['POST'])
def upload_cv():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if 'cv' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))
    
    file = request.files['cv']
    
    # Debug: Check if file is present and has a filename
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))
    
    # Ensure the file is a PDF
    if file and file.filename.endswith('.pdf'):
        # Sanitize the filename
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        
        # Debug: Print out file path to ensure it's correct
        print(f"Saving file to: {filepath}")
        
        try:
            # Save the file
            file.save(filepath)
            
            # Debug: Check if file is saved successfully
            if not os.path.isfile(filepath):
                flash('File was not saved successfully')
                return redirect(url_for('profile'))
            
            # Extract CV information
            user_info = extract_cv_info(filepath)
            
            # Debug: Print extracted information
            print(f"Extracted info: {user_info}")
            
            if not user_info or not any(user_info.values()):
                flash('Failed to extract information from CV')
                return redirect(url_for('profile'))
            
            # Update user profile with CV info
            users_collection.update_one(
                {'username': session['username']},
                {'$set': {'cv_info': user_info}}
            )
            
            # Remove the file after processing
            os.remove(filepath)
            
            flash('CV uploaded and information updated')
            return redirect(url_for('profile'))
        
        except Exception as e:
            # Handle any exceptions and return an error message
            flash(f'Error during file upload and processing: {e}')
            return redirect(url_for('profile'))
    
    flash('Invalid file format')
    return redirect(url_for('profile'))

@app.route('/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if 'profile_picture' not in request.files:
        flash('No file part')
        return redirect(url_for('profile'))
    
    file = request.files['profile_picture']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('profile'))
    
    if file and file.content_type.startswith('image/'):
        try:
            img = Image.open(file)
            img = img.resize((150, 150))
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
            
            users_collection.update_one(
                {'username': session['username']},
                {'$set': {'profile_picture': img_base64}}
            )
            
            flash('Profile picture uploaded successfully')
            return redirect(url_for('profile'))
        
        except Exception as e:
            flash(f'Error during file upload and processing: {e}')
            return redirect(url_for('profile'))
    
    flash('Invalid file format')
    return redirect(url_for('profile'))

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


def session_userskills():
    user_skills = []
    if 'username' in session:
        user = users_collection.find_one({'username': session['username']})
        if user:
           user_skills = user.get('cv_info', {}).get('skills', [])
           if not isinstance(user_skills, list):
              user_skills = [user_skills]
    return user_skills;
               
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

        user_skills = session_userskills()
        recommendations = job_recommender.recommend_jobs(mytext, user_skills)
        
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
        user_skills = session_userskills()


        recommendations = job_recommender.recommend_jobs(job_title, user_skills)

        return jsonify({"transcription": job_title, "recommendations": recommendations})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

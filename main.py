from flask import Flask, flash, request, redirect, render_template
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os.path import join, dirname
import moviepy.editor as mp
import pydub
import os
import json
import speech_recognition as sr
import pyrebase

config = {
    "apiKey": "AIzaSyC9un2vGUcmrC3T9DCrZNjUDhhKmq_KP4M",
    "authDomain": "bitgrit-api.firebaseapp.com",
    "databaseURL": "https://bitgrit-api.firebaseio.com",
    "projectId": "bitgrit-api",
    "storageBucket": "bitgrit-api.appspot.com",
    "messagingSenderId": "915449222893",
    "appId": "1:915449222893:web:df897137a0f6bc0ff5dee4",
    "measurementId": "G-XQRCNYG002"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()
r = sr.Recognizer()

UPLOAD_FOLDER = "/home/pi/bitgrit-personality-api/video/"

app = Flask(__name__)
CORS(app)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 24 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['mp4'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# video to mp3 file conversion


def video_converter(video_path):
    video_clip = mp.VideoFileClip(video_path)
    video_clip.audio.write_audiofile(
        "/home/pi/bitgrit-personality-api/audio/audio.mp3")
    return os.path.abspath("/home/pi/bitgrit-personality-api/audio/audio.mp3")

# mp3 to wav file conversion


def wav_conversion(audio_path):
    sound = pydub.AudioSegment.from_mp3(audio_path)
    sound.export(
        '/home/pi/bitgrit-personality-api/audio/audio.wav', format='wav')
    return os.path.abspath('/home/pi/bitgrit-personality-api/audio/audio.wav')

# wav to text file conversion


def speech_conversion(audio_path):
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
        val = r.recognize_google(audio)
        return val


@app.route('/firebase', methods=['GET'])
def firbase_db():
    # Fetching all entries from dB
    pyre_db = db.child("personality-data").get()
    final = pyre_db.val()
    return final, 200


@app.route('/', methods=['POST', 'GET'])
def get_text_from_video():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File successfully uploaded')
            video_path = "/home/pi/bitgrit-personality-api/video/video.mp4"
            audio_path = video_converter(video_path)
            wav_path = wav_conversion(audio_path)
            textvalue = speech_conversion(wav_path)

            # Writing Speech-to-Text response to a file
            f = open(
                "/home/pi/bitgrit-personality-api/speech-to-text/profile.txt", "w")
            f.write(textvalue)
            f.close()

            authenticator = IAMAuthenticator(
                'rTFTt7hpFyWaZ5SCGPaNhQi0PHs7c7WKf4ttC-VR9f-G')
            personality_insights = PersonalityInsightsV3(
                version='2017-10-13',
                authenticator=authenticator)

            personality_insights.set_service_url(
                'https://api.eu-gb.personality-insights.watson.cloud.ibm.com/instances/5261ab93-9fc2-4710-84fc-83c043c2ea34/v3/profile?version=2017-10-13')

            with open(join(dirname(__file__), '/home/pi/bitgrit-personality-api/speech-to-text/profile.txt')) as profile_txt:
                profile = personality_insights.profile(
                    profile_txt.read(),
                    'application/json',
                    content_type='text/plain',
                    consumption_preferences=True,
                    raw_scores=True
                ).get_result()

            value = json.dumps(profile, indent=2)
            name = request.form['username']
            question_number = request.form['question_no']
            data = {"text": textvalue, "json": value,
                    "username": name, "question_no": question_number}
            db.child("personality-data").push(data)
            # Fetching recent updated entry from firebase
            pyre_db = db.child("personality-data").get()
            for users in pyre_db.each():
                final = users.val()
            return final, 200
        else:
            flash('Allowed file type is video (.mp4)')
            return redirect(request.url)
    return render_template("upload.html")


if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, flash, request, redirect, render_template
from werkzeug.utils import secure_filename
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os.path import join, dirname
import moviepy.editor as mp
import pydub
import os
import json
import speech_recognition as sr
r = sr.Recognizer()

UPLOAD_FOLDER = "/mnt/c/Users/ashleymavericks/Documents/Covid-19-Break/bitgrit-personality-api/video"

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['mp4'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# movie to mp3 file conversion
def video_converter(video_path):
    video_clip = mp.VideoFileClip(video_path)
    video_clip.audio.write_audiofile(r"./audio/audio.mp3")
    return os.path.abspath(r"./audio/audio.mp3")

# mp3 to wav file conversion
def wav_conversion(audio_path):
    sound = pydub.AudioSegment.from_mp3(audio_path)
    sound.export('./audio/audio.wav', format='wav')
    return os.path.abspath('./audio/audio.wav')

# wav to text file conversion
def speech_conversion(audio_path):
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
        val = r.recognize_google(audio)
        return val

@app.route('/')
def upload_form():
    return render_template("upload.html")


@app.route("/", methods=['POST'])
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
            video_path = "./video/video.mp4"
            audio_path = video_converter(video_path)
            wav_path = wav_conversion(audio_path)
            textvalue = speech_conversion(wav_path)

            f = open("./speech-to-text/profile.txt", "w")
            f.write(textvalue)
            f.close()

            authenticator = IAMAuthenticator(
                'rTFTt7hpFyWaZ5SCGPaNhQi0PHs7c7WKf4ttC-VR9f-G')
            personality_insights = PersonalityInsightsV3(
                version='2017-10-13',
                authenticator=authenticator)

            personality_insights.set_service_url(
                'https://api.eu-gb.personality-insights.watson.cloud.ibm.com/instances/5261ab93-9fc2-4710-84fc-83c043c2ea34/v3/profile?version=2017-10-13')

            with open(join(dirname(__file__), './speech-to-text/profile.txt')) as profile_txt:
                profile = personality_insights.profile(
                    profile_txt.read(),
                    'application/json',
                    content_type='text/plain',
                    consumption_preferences=True,
                    raw_scores=True
                ).get_result()

            value = json.dumps(profile, indent=2)
            return value, 200, {'Content-Type': 'application/json'}

        else:
            flash('Allowed file type is video (.mp4)')
            return redirect(request.url)


if __name__ == '__main__':
    app.run(debug=True)

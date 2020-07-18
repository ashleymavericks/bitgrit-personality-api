from flask import Flask, json, request,redirect,render_template
from flask import request, redirect, url_for,flash
from werkzeug.utils import secure_filename
from ibm_watson import PersonalityInsightsV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from os.path import join, dirname
import json
import moviepy.editor as mp
import pydub
import os
import speech_recognition as sr
r = sr.Recognizer()

app = Flask(__name__)
app.config['VIDEO_UPLOAD']='./bitgrit-personality-api/video'

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


@app.route("/video", methods=['POST'])

def get_text_from_video():
    # Video input taking and storage
    if request.method == "POST":
        if request.files:
            video = request.files['video']
            video.save(os.path.join('app.config['VIDEO_UPLOAD']', video.filename))

    # Processing of video starts
    audio_path = video_converter(video_path)
    wav_path = wav_conversion(audio_path)
    fvalue = speech_conversion(wav_path)

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

    return value, 200


if __name__ == '__main__':
    app.run(debug=True)

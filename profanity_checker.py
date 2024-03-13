from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, render_template ,redirect, url_for
from moviepy.editor import VideoFileClip
import speech_recognition as sr
import profanity_check
import os
from werkzeug.utils import secure_filename
import http.client


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('upload.html')



# Store results in a global variable
results = []

@app.route('/process_video', methods=['POST'])
def process_video():
    global results
    videos = request.files.getlist('video')

    for video in videos:
        result = process_single_video(video)
        results.append(result)

    return redirect(url_for('show_results'))

@app.route('/show_results')
def show_results():
    global results
    return render_template('upload.html', results=results)

@app.route('/results.json')
def results_json():
    global results
    return jsonify(results)


def process_single_video(video):
    video_filename = secure_filename(video.filename)
    video.save(video_filename)
    print(f"Processing {video_filename}...")
    # Extract audio from video
    clip = VideoFileClip(video_filename)
    clip.audio.write_audiofile('output_audio.wav')

    # Convert audio to text
    r = sr.Recognizer()
    audio_file = sr.AudioFile('output_audio.wav')
    with audio_file as source:
        audio = r.record(source)
    try:
        text = r.recognize_google(audio, language='en-IN')
    except (sr.UnknownValueError, http.client.IncompleteRead):
        text = ""

    # Identify bad words
    words = text.split()
    identified_bad_words = [word for word in words if profanity_check.predict([word])[0]]

    # Calculate word counts and percentage
    all_words_count = len(words)
    bad_words_count = len(identified_bad_words)
    bad_words_percentage = (bad_words_count / all_words_count) * 100 if all_words_count else 0
    print(f"Finished processing {video_filename}. Bad words percentage: {bad_words_percentage}%")
    return {
        'filename': video_filename,
        'all_words_count': all_words_count,
        'bad_words_count': bad_words_count,
        'bad_words_percentage': bad_words_percentage,
        'bad_words': identified_bad_words,
        'all_words': words
    }
if __name__ == '__main__':
    app.run(debug=True)
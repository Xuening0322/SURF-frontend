from app import app

from flask import render_template, request, redirect, jsonify, make_response, url_for, flash, send_from_directory, send_file


from datetime import datetime

import os

import redis
from rq import Queue
import shutil
from zipfile import ZipFile
from pydub import AudioSegment


# redis with default connection (add password in production)
r = redis.Redis()
q = Queue(connection=r)



# index page
@app.route('/')
def index():
    print(app.config)
    return render_template('public/index.html')

# record page
@app.route('/record')
def record():
    return render_template('public/record.html')

# recorded audio waveform display page
@app.route('/display/<file_name>')
def display(file_name):
    if file_name == 'undefined':
        return render_template('public/record.html')
    path = app.config['UPLOADS']
    file_path = os.path.join(path, file_name)

    # input_file = open(file_path, 'rb')
    
    # dummy process
    processed_name = file_name + '.mp3'

    new_path = os.path.join(path, processed_name)
    if os.path.exists(new_path):
        return render_template('public/display.html', file_name=file_name)
    else:
        return render_template('public/queued.html', q_len=len(q), file_name=file_name)

# record's recieve post method
@app.route('/record/recieve', methods=['POST'])
def record_recieve():
    # upload via web front-end
    if request.files:
        file = request.files['file']
        if file.filename == '':
            print('ERROR: Audio must have a filename')
            return make_response(jsonify({'message':'Audio must have a filename'}), 400)

        else:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = timestamp+'.wav'
  
        
        path = app.config['UPLOADS']
        file.save(os.path.join(path, filename))
        print(file)

        print('Upload Success!')
        print('saved', filename)

        job = q.enqueue(process_wav, filename, on_success=report_success, on_failure=report_failure)

        return make_response(jsonify({'message':'Upload Success!', 'path_url': '/static/uploads/'+filename, 'timestamp': timestamp}), 200)


allowed_audio_extensions = ['mpeg', 'wav']
def isAudio(mimetype):
    if not '/' in mimetype:
        return False
    ext = mimetype.rsplit('/', 1)[1]
    return ext.lower() in allowed_audio_extensions

def isMP3(mimetype):
    if not '/' in mimetype:
        return False
    ext = mimetype.rsplit('/', 1)[1]
    return ext.lower() == 'mpeg'

# record's recieve post method
@app.route('/record/recieve_upload', methods=['POST'])
def record_recieve_upload():
    # upload via web front-end
    if request.files:
        file = request.files['file']
        if file.filename == '':
            print('ERROR: Audio must have a filename')
            return make_response(jsonify({'message':'Audio must have a filename'}), 400)

        else:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = timestamp+'.wav'
  
        # if file not audio make an error response
        if not isAudio(file.mimetype):
            print('ERROR: Uploaded audio must be a mp3 or wav')
            return make_response(jsonify({'message':'Uplaoded audio must be a mp3 or wav'}), 400)
        
        path = app.config['UPLOADS']
        upload_path = os.path.join(path, file.filename)
        file.save(upload_path)
        print(file)

        export_path = os.path.join(path, filename)

        # load audio and resize to 5~10 seconds
        if isMP3(file.mimetype):
            audio = AudioSegment.from_mp3(upload_path)
        else:
            audio = AudioSegment.from_wav(upload_path)
        if len(audio) < 5000:
            print('ERROR: audio less than 5 seconds long')
            return make_response(jsonify({'message':'audio less than 5 seconds long'}), 400)
        else:
            audio.set_frame_rate(441000) # explicitly set sample rate to 44.1kHz
            audio[:10000].export(export_path, format='wav')

        print('Upload Success!')
        print('saved', filename)

        job = q.enqueue(process_wav, filename, on_success=report_success, on_failure=report_failure)

        return make_response(jsonify({'message':'Upload Success!', 'path_url': '/static/uploads/'+filename, 'timestamp': timestamp}), 200)

    # upload via API (this can be ignored)
    elif request.data:
        print('Access through API!')
        path = app.config['UPLOADS']
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = timestamp+'.wav'
        newFile = open(os.path.join(path, filename), 'wb')
        newFile.write(request.data)
        print('Upload Success!')
        print('saved', filename)
        return make_response(jsonify({'message':'Upload Success via API!', 'path_url': '/static/uploads/'+filename}), 200)

    # invalid usage
    else:
        print('ERROR: No WAV recieved!')
        return make_response(jsonify({'message':'ERROR: No WAV recieved!'}), 400)


# configuring favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static', 'img'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')


# dummy process rename wav task:
def process_wav(file_name):
    path = app.config['UPLOADS']
    file_path = os.path.join(path, file_name)

    # input_file = open(file_path, 'rb')
    
    # dummy process
    # wav to mp3
    wav_to_mp3(file_name)
    # make fake midi
    midi_name = ''.join(file_name.split('.')[:-1]) + '.mid'
    midi_path = os.path.join(path, midi_name)
    shutil.copyfile(os.path.join(path, 'test.mid'), midi_path)

    return file_name
   


# report success
def report_success(job, connection, result, *args, **kwargs):
    print('success', job, connection, result, args, kwargs)
    

# report faliure
def report_failure(job, connection, type, value, traceback):
    print('faliure', job, connection, type, value, traceback)
    

# download midi & mp3
@app.route('/download_zip/<filename>')
def download_midi_and_mp3(filename):
    path = app.config['UPLOADS']
    midi_path = os.path.join(path, filename+'.mid')
    mp3_path = os.path.join(path, filename+'.mp3')
    zip_path = os.path.join(path, filename+'.zip')
    try:
        # create zip file
        with ZipFile(zip_path,'w') as zip_output:
            zip_output.write(midi_path, arcname=filename+'.mid')
            zip_output.write(mp3_path, arcname=filename+'.mp3')
            print(zip_output.filelist)
        # send
        return send_file(zip_path, as_attachment=True)
    except:
        return '<h1>Failed to download</h1>'


# download midi
@app.route('/download_midi/<filename>')
def download_midi(filename):
    path = app.config['UPLOADS']
    midi_path = os.path.join(path, filename+'.mid')
    try:
        return send_file(midi_path, as_attachment=True)
    except:
        return '<h1>Failed to download</h1>'


# download mp3
@app.route('/download_mp3/<filename>')
def download_mp3(filename):
    path = app.config['UPLOADS']
    mp3_path = os.path.join(path, filename+'.mp3')
    try:
        return send_file(mp3_path, as_attachment=True)
    except:
        return '<h1>Failed to download</h1>'



def wav_to_mp3(file_name):
    path = app.config['UPLOADS']
    wav_path = os.path.join(path, file_name)

    mp3_name = ''.join(file_name.split('.')[:-1]) + '.mp3'
    mp3_path = os.path.join(path, mp3_name)
    print('exporting', file_name)
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
    print('exported', mp3_name)


def mp3_to_wav(file_name):
    path = app.config['UPLOADS']
    mp3_path = os.path.join(path, file_name)

    wav_name = ''.join(file_name.split('.')[:-1]) + '.wav'
    wav_path = os.path.join(path, wav_name)
    print('exporting', file_name)
    AudioSegment.from_wav(mp3_path).export(wav_path, format="mp3")
    print('exported', wav_name)





    
    

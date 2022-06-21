from app import app

from flask import render_template, request, redirect, jsonify, make_response, url_for, flash, send_from_directory


from datetime import datetime

import os

import redis
from rq import Queue
import shutil
import time

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
    path = app.config['UPLOADS']
    file_path = os.path.join(path, file_name)

    # input_file = open(file_path, 'rb')
    
    # dummy process
    processed_name = file_name + 'processed'

    new_path = os.path.join(path, processed_name+'.wav')
    if os.path.exists(new_path):
        return render_template('public/display.html', file_name=processed_name)
    else:
        return render_template('public/queued.html', q_len=len(q), file_name=file_name)

# record's recieve post method
@app.route('/record/recieve', methods=['POST'])
def record_recieve():
    # upload via web front-end
    if request.files:
        file = request.files['file']
        if file.filename == '':
            print('ERROR: Image must have a filename')
            return make_response(jsonify({'message':'Image must have a filename'}), 400)

        else:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = timestamp+'.wav'
  
        
        # TODO: downsample wav to 8k Hz
        path = app.config['UPLOADS']
        file.save(os.path.join(path, filename))
        print(file)

        print('Upload Success!')
        print('saved', filename)

        # TODO: implement queing to call model 
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
    processed_name = ''.join(file_name.split('.')[:-1]) + 'processed'
    new_path = os.path.join(path, processed_name+'.wav')
    # output_file = open(new_path, 'wb')
    # dummy process, copy and rename



    shutil.copyfile(file_path, new_path)
    print('sleeping for 1 min')
    time.sleep(60) # sleep for 1 min
    
    return processed_name
   


# report success
def report_success(job, connection, result, *args, **kwargs):
    print('success', job, connection, result, args, kwargs)
    

# report faliure
def report_failure(job, connection, type, value, traceback):
    print('faliure', job, connection, type, value, traceback)
    
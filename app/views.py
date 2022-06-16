from app import app

from flask import render_template, request, redirect, jsonify, make_response, url_for, flash, send_from_directory

from datetime import datetime

import os

from werkzeug.utils import secure_filename

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
@app.route('/display/<timestamp>')
def display(timestamp):
    return render_template('public/display.html', timestamp=timestamp)

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
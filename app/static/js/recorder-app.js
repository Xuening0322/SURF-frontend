//webkitURL is deprecated but nevertheless
URL = window.URL || window.webkitURL;

var gumStream; //stream from getUserMedia()
var rec; //Recorder.js object
var input; //MediaStreamAudioSourceNode we'll be recording

// shim for AudioContext when it's not avb. 
var AudioContext = window.AudioContext || window.webkitAudioContext;
var audioContext //audio context to help us record

var recordButton = document.getElementById("recordButton");
var stopButton = document.getElementById("stopButton");
var pauseButton = document.getElementById("pauseButton");

//add events to those 2 buttons
recordButton.addEventListener("click", startRecording);
stopButton.addEventListener("click", stopRecording);
pauseButton.addEventListener("click", pauseRecording);


// timer dispatch function
function startTimer(seconds, container, oncomplete) {
    var startTime, timer, obj, ms = seconds * 1000,
        display = document.getElementById(container);
    obj = {};
    obj.resume = function() {
        startTime = new Date().getTime();
        timer = setInterval(obj.step, 250); // adjust this number to affect granularity
        // lower numbers are more accurate, but more CPU-expensive
    };
    obj.pause = function() {
        ms = obj.step();
        clearInterval(timer);
    };
    obj.end = function() {
        clearInterval(timer);
    };
    obj.step = function() {
        var now = Math.max(0, ms - (new Date().getTime() - startTime));
        display.innerHTML = parseInt((10000 - now) / 1000) + 's';
        if (now == 0) {
            clearInterval(timer);
            obj.resume = function() {};
            if (oncomplete) oncomplete();
        }
        return now;
    };
    obj.resume();
    return obj;
}
var timer;

function startRecording() {
    console.log("recordButton clicked");

    /*
    	Simple constraints object, for more advanced audio features see
    	https://addpipe.com/blog/audio-constraints-getusermedia/
    */
    var constraints = { audio: true, video: false }

    /*
    	We're using the standard promise based getUserMedia() 
    	https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia
	*/
    navigator.mediaDevices.getUserMedia(constraints).then(function(stream) {
        console.log("getUserMedia() success, stream created, initializing Recorder.js ...");

        /*
        	create an audio context after getUserMedia is called
        	sample rate is hardcoded to 44.1k
        */
        // audioContext = new AudioContext({ sampleRate: 441000 });
        audioContext = new AudioContext();


        //update the format 
        document.getElementById("formats").innerHTML = "Format: 1 channel pcm @ " + audioContext.sampleRate / 1000 + "kHz"

        /*  assign to gumStream for later use  */
        gumStream = stream;

        /* use the stream */
        input = audioContext.createMediaStreamSource(stream);

        /* 
        	Create the Recorder object and configure to record mono sound (1 channel)
        	Recording 2 channels  will double the file size
        */
        rec = new Recorder(input, { numChannels: 1 })

        //start the recording process
        rec.record()

        console.log("Recording started");


        /*
            Disable the record button until we get a success or fail from getUserMedia() 
        */

        recordButton.disabled = true;
        // allow stop and pause button only after 5 seconds of recording
        window.setTimeout(() => {
            stopButton.disabled = false;
            pauseButton.disabled = false;
        }, 5000);


        // automatically trigger stop recording when time is up!
        timer = startTimer(10, "timerLabel", stopRecording);

    }).catch(function(err) {
        //enable the record button if getUserMedia() fails
        recordButton.disabled = false;
        stopButton.disabled = true;
        pauseButton.disabled = true
        timer = null;
    });
}

function pauseRecording() {
    console.log("pauseButton clicked rec.recording=", rec.recording);
    if (rec.recording) {
        //pause
        rec.stop();
        timer.pause();
        pauseButton.innerHTML = "Resume";
    } else {
        //resume
        rec.record()
        timer.resume();
        pauseButton.innerHTML = "Pause";

    }
}

function stopRecording() {
    timer.end()
    timer = null;
    console.log("stopButton clicked");

    //disable the stop button, enable the record too allow for new recordings
    stopButton.disabled = true;
    recordButton.disabled = false;
    pauseButton.disabled = true;

    //reset button just in case the recording is stopped while paused
    pauseButton.innerHTML = "Pause";

    //tell the recorder to stop the recording
    rec.stop();

    //stop microphone access
    gumStream.getAudioTracks()[0].stop();

    //create the wav blob and pass it on to createDownloadLink
    rec.exportWAV(createDownloadLink);
}

function createDownloadLink(blob) {

    var url = URL.createObjectURL(blob);
    var au = document.createElement('audio');
    var li = document.createElement('li');
    var link = document.createElement('a');

    //name of .wav file to use during upload and download (without extendion)
    var filename = new Date().toISOString();

    //add controls to the <audio> element
    au.controls = true;
    au.src = url;

    //save to disk link
    link.href = url;
    link.download = filename + ".wav"; //download forces the browser to donwload the file using the  filename
    link.innerHTML = "Save to disk";

    //add the new audio element to li
    li.appendChild(au);

    //add the filename to the li
    li.appendChild(document.createTextNode(filename + ".wav "))

    //add the save to disk link to li
    li.appendChild(link);

    //upload link
    var upload = document.createElement('a');
    upload.href = "#";
    upload.innerHTML = "Upload";
    upload.addEventListener("click", function(event) {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);

        var data = new FormData();
        data.append('file', blob, 'file');
        fetch(window.origin + '/record/recieve_upload', {
                method: "POST",
                credentials: "include",
                body: data,
                cache: "no-cache"
            })
            .then(response => response.json())
            .then(json => {
                console.log(json);
                console.log(json['message']);
                // this redirects user to display page
                window.location.replace(window.origin + "/display/" + json['timestamp']);

            });
    })
    li.appendChild(document.createTextNode(" ")); //add a space in between
    li.appendChild(upload); //add the upload link to li

    // delete button
    var deleteButton = document.createElement('a')
    deleteButton.href = "#";
    deleteButton.innerHTML = " Delete";
    // removes current li from the recordingList
    deleteButton.addEventListener("click", function(event) {
        recordingsList.removeChild(li);
    });
    li.appendChild(deleteButton);

    //add the li element to the ol
    recordingsList.appendChild(li);



}
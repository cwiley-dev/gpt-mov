'''
Plan:
Test serving HTML, CSS, and JS
Test serving images
Test serving audio
Test serving images, text, and audio at once through JSON?
Test serving video
Lay out api endpoints

App functionalities:
    - Log in
    - Manage the API keys associated with your account
    - Manage projects on your account (create, delete, rename, edit)
    - Generate a "segment" from text
    - Generate a script from a specified subject (eg "rainbows")
    - Generate a "sequence" of segments from a script (user-defined or pre-generated)
    - Insert/append new segments in/to a sequence
    - Change the text of a segment
    - Save changed text as a "new version"
    - Regenerate the image, text, or audio in a segment, saving as a new "version" of that element
    - Switch between versions of re/generated images, text, or audio in a segment
    - Export a sequence as a video


Design for local usage, scale to server usage:
Local usage:
    - No log in, no users, still need to manage the one users API keys
    - Store and name things as if there are multiple users but the current user is called "local"
    - Database to make it easier to scale up later
    - Store images and audio as local files to scale up to cloud storage later
    - Server runs locally, additional py lib will launch browser window for local GUI
    - Encrypt database when not used so the API keys can't be snatched

Server usage:
    - Log in, users, manage API keys (how security? :/ )
    - Whitelisting for resources based on user ID
    
    

Schema:
    - User
        - ID
        - Username
        - Password
        - API Keys
        - Project IDs
    - Project
        - ID
        - Script
        - Sequence
    - Sequence
        - ID
        - Segments
    - Segment
        - ID
        - Index
        - Text list (text)
        - Image list (url to png)   # Store as URL because it makes serving easier
        - Audio list (url to mp3)   # Or, store in database because it makes selective serving easier?
 
 
Note: "Segment" object == {
        "index": int,
        "images": {
            "list": ["url"],
            "current_version": int
        },
        "text": {
            "list": ["text"],
            "current_version": int
        },
        "audio": {
            "list": ["url"],
            "current_version": int
        }
    }
    from Segment.jsonify()
    
GET /api/users/<user-id>
    Returns {"projects"}

# Project management
GET /api/projects/<project-id>
    Returns {"name": name, "id": id, "script": "script", "sequence": list[Segment]}
POST /api/projects/
    Body: {"name": name}
    Creates a new project/sequence
    Returns {"name": name, "id": id}
POST /api/projects/<project-id>
    Body: {"name": "name" | "", "delete": bool}
    Rename or delete the project
    Returns the new project name or None
GET /api/projects/<project-id>/segments/
    Returns {"":list[Segment]}
GET /api/projects/<project-id>/segments/<segment-index>
    Returns Segment object
GET /api/projects/<project-id>/segments/<segment-index>/images
    Returns {"list": ["url"], "current_version": int}
GET /api/projects/<project-id>/segments/<segment-index>/images/<image-index>
    Returns the image in .png format
GET /api/projects/<project-id>/segments/<segment-index>/text
    Returns {"list": ["text"], "current_version": int}
GET /api/projects/<project-id>/segments/<segment-index>/text/<text-index>
    Returns the text in plaintext format (utf-8?)
GET /api/projects/<project-id>/segments/<segment-index>/audio
    Returns {"list": ["url"], "current_version": int}
GET /api/projects/<project-id>/segments/<segment-index>/audio/<audio-index>
    Returns the audio in .mp3 format

# Script
GET /api/projects/<project-id>/script
    Returns the currently stored script
POST /api/projects/<project-id>/script
    Body: {"script": "script" | "", "subject": "subject" | ""}
    If the script is empty, generates a new script from the specified subject
    If the script and subject are empty, generates a new random script.
    Returns the new script, and sets it as the project script

# Version generation
POST /api/projects/<project-id>/segments
    Body: {"index": int, "text": "text"}
    Generates a new segment at the specified index with the specified text
    Consequently may likely change other segment indices
    Returns the new Segment object
POST /api/projects/<project-id>/segments/<segment-index>/images
    Body: {"image": "url" | ""}
    Replaces or generates a new image version for the specified segment
    Returns the new image .png
POST /api/projects/<project-id>/segments/<segment-index>/text
    Body: {"text": "text" | ""}
    Replaces or generates a new text version for the specified segment
    Returns the new text
POST /api/projects/<project-id>/segments/<segment-index>/audio
    Body: {"Audio": "url" | ""}
    Replaces or generates a new audio version for the specified segment
    Returns the new audio .mp3

# Version changes
# Should technically be PATCH but I'm unsure of the header considerations
POST /api/projects/<project-id>/segments/<segment-index>/
    Body: {"new-index": int}
    Changes the index of that segment. 
    new-index < 0 or new-index > len(sequence) will put the segment at the beginning or end of the sequence.
    Consequently may likely change other segment indices
    Returns the new Segment object
POST /api/projects/<project-id>/segments/<segment-index>/images/
    Body: {"new-version": int}
    Changes the current selected version of the segment's image
    version < 0 or version > len(images) will select the first or last version.
    Returns the new image .png
POST /api/projects/<project-id>/segments/<segment-index>/text/
    Body: {"new-version": int}
    Changes the current selected version of the segment's text
    version < 0 or version > len(text) will select the first or last version.
    Returns the new text
POST /api/projects/<project-id>/segments/<segment-index>/audio/
    Body: {"new-version": int}
    Changes the current selected version of the segment's audio
    version < 0 or version > len(audio) will select the first or last version.
    Returns the new audio .mp3
    
# Exporting
GET /api/projects/<project-id>/export
    Returns a URL to the current sequence exported as a video file .mp4
    # Note: store the exact sequence used to generate the video
        so that we don't get overloaded by pressing "generate" a lot
    
TODO later
    - link audio and text versions, since the text directly represents the audio
    - Let the image be generated by a custom prompt
    - Let the client upload custom images (? they can just edit it themselves if they want)
    - pay me  (¬‿¬)っ

'''

# Currently run via
# python -m flask --app server run
# http://127.0.0.1:5000 by default
from flask import Flask, request, send_file, render_template
from markupsafe import escape # for escaping user input

app = Flask(__name__, template_folder='www')

# Note: Don't include a leading slash on paths, that points to root C:\

# Test returning an image
# This works!
@app.route("/test/image")
def test_image():
    path = 'images/seq-test_12_0.png'
    return send_file(path, mimetype='image/png')

# Test returning audio
# This works!
@app.route("/test/audio")
def test_audio():
    path = 'audio/seq-test_12_0.mp3'
    return send_file(path, mimetype='audio/mpeg')

# Test POSTing with a body
# This works!
@app.route("/test/post", methods=['GET', 'POST'])
def test_post():
    if request.method == "GET":
        return render_template("test.html");
    data = request.data
    return f'Received POST request with data: {data}'


# @app.route("/api/projects/<int:project_id>", methods=['GET', 'POST'])
# def project_root(project_id):
#     if request.method == "POST":
#         # In the future, edit name or delete project
#         return "no"
#     if request.method == "GET":
#         return {
            
#         }


# def get_project(project_id):
#     pass
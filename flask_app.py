"""

 OMRChecker

 Author: Udayraj Deshmukh
 Github: https://github.com/Udayraj123

"""

import argparse
import os
import sys
from pathlib import Path
import platform
from src.entry import entry_point, process_image
from src.logger import logger
from flask import Flask, request, jsonify
import json
import firebase_admin
from firebase_admin import credentials, storage
from werkzeug.utils import secure_filename


cred = credentials.Certificate("opticalmarkrecognition-f7059-firebase-adminsdk-ytgau-c14ddee08f.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'opticalmarkrecognition-f7059.appspot.com'  # Replace with your Firebase storage bucket
})

def parse_args():
    # construct the argument parse and parse the arguments
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        "-i",
        "--inputDir",
        default=["inputs"],
        # https://docs.python.org/3/library/argparse.html#nargs
        nargs="*",
        required=False,
        type=str,
        dest="input_paths",
        help="Specify an input directory.",
    )

    argparser.add_argument(
        "-d",
        "--debug",
        required=False,
        dest="debug",
        action="store_false",
        help="Enables debugging mode for showing detailed errors",
    )

    argparser.add_argument(
        "-o",
        "--outputDir",
        default="outputs",
        required=False,
        dest="output_dir",
        help="Specify an output directory.",
    )

    argparser.add_argument(
        "-a",
        "--autoAlign",
        required=False,
        dest="autoAlign",
        action="store_true",
        help="(experimental) Enables automatic template alignment - \
        use if the scans show slight misalignments.",
    )

    argparser.add_argument(
        "-l",
        "--setLayout",
        required=False,
        dest="setLayout",
        action="store_true",
        help="Set up OMR template layout - modify your json file and \
        run again until the template is set.",
    )

    (
        args,
        unknown,
    ) = argparser.parse_known_args()

    args = vars(args)

    if len(unknown) > 0:
        logger.warning(f"\nError: Unknown arguments: {unknown}", unknown)
        argparser.print_help()
        exit(11)
    return args


def entry_point_for_args(args):
    if args["debug"] is True:
        # Disable tracebacks
        sys.tracebacklimit = 0
    for root in args["input_paths"]:
        entry_point(
            Path(root),
            args,
        )


app = Flask(__name__)

@app.route('/process_omr', methods=['POST'])
def process_omr():
        # Check if a file is part of the request
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    # Get data from request
    uploaded_file = request.files['file']  # Assuming OMR input is a file

    try:
        question_count = int(request.form.get('question_count', 0))
    except ValueError:
        question_count = 20

    args = parse_args()
    if platform.system() == 'Windows':
        input_dir = Path('inputs')  # Relative or absolute path for Windows
    else:
        input_dir = Path('/home/checkease/OMRChecker/inputs')
    if not os.path.exists(input_dir):
        raise Exception(f"Given input directory does not exist: '{input_dir}'")
    
    correct_answers_json = request.form.get('correct_answers', '[]')
    correct_answers = json.loads(correct_answers_json)
    logger.info(f'correct_answers: {correct_answers}')
    try:
        result = process_image(
            uploaded_file,
            input_dir,
            args,
            correct_answers,
            question_count
        )
        # result = your_omr_module.process_omr(uploaded_file)  # Replace with your OMR processing logic

        # Return the result as JSON
        return jsonify(result), 200
    except Exception as e:
        return str(e), 500



# Set the upload folder and allowed extensions
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to upload an image
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(local_path)

        # Upload the file to Firebase storage
        bucket = storage.bucket()
        blob = bucket.blob(filename)
        blob.upload_from_filename(local_path)

        # Get the download URL
        blob.make_public()
        download_url = blob.public_url

        # Optionally, remove the file from local storage after upload
        os.remove(local_path)

        return jsonify({'download_url': download_url}), 200

    return jsonify({'error': 'File type not allowed'}), 400



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


# if __name__ == "__main__":
#     args = parse_args()
#     entry_point_for_args(args)
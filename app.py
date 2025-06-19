from flask import Flask, request, jsonify, send_from_directory, render_template
import os
from werkzeug.utils import secure_filename

from cloud_ocr.recognizer import Recognize
from WorkFlow import Generate_Final_Report, report

app = Flask(__name__)

# Ensure required folders exist
for folder in [
    "Processos",
    "Processos/Processed",
    "Output/Processed",
    "Reports",
    "Reports/Processed",
]:
    os.makedirs(folder, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files[]')
    saved = []
    for file in files:
        if file and file.filename.lower().endswith('.pdf'):
            filename = secure_filename(file.filename)
            dest = os.path.join('Processos', filename)
            file.save(dest)
            saved.append(filename)
    return jsonify({'saved': saved})

@app.route('/start', methods=['POST'])
def start():
    # Run OCR and generate reports sequentially
    Recognize()
    Generate_Final_Report('gpt-4o-2024-08-06', report)
    return jsonify({'status': 'completed'})

@app.route('/reports')
def list_reports():
    files = [f for f in os.listdir('Reports') if f.endswith('.md')]
    return jsonify({'reports': files})

@app.route('/report/<path:filename>')
def get_report(filename):
    return send_from_directory('Reports', filename)

if __name__ == '__main__':
    app.run(debug=True)

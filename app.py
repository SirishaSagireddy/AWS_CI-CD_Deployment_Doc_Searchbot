# Standard libraries
import os
from pathlib import Path
# Third party libraries
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
# Custom libraries
from store_index import Store_to_db
from src.helper import read_yaml
import logging 

app = Flask(__name__)
UPLOAD_FOLDER = 'data/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
config_path = 'config/configuration.yaml'
config = read_yaml(config_path)
qa_connection = Store_to_db(config)

def allowed_file(filename):
    allowed_extensions = {'pdf', 'pptx', 'csv', 'docx', 'xlsx', 'doc'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() \
        in allowed_extensions

@app.route("/", methods=['POST', 'GET'])
def upload_file():
    if request.method == 'POST':
        url = request.form.get('url')
        if not url.strip():
            flash('URL field cannot be empty')
            return redirect(request.url)
        if url:
            print('url**')
            qa_connection.create_qa_instance(url)
            return redirect(url_for('chat_page'))
        
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            qa_connection.create_qa_instance()
            # Redirect to chat.html after successful upload
            # flash(message)
            # logger.info('Embeddings message%s'%message)
            Path(file_path).unlink()
            return redirect(url_for('chat_page'))
        elif url:
            qa_connection.create_qa_instance()
            return redirect(url_for('chat_page'))
        
        flash('Allowed file types are: PDF, PPTX, CSV, DOCX, XLSX, DOC')
        return redirect(request.url)
    return render_template('index.html')

@app.route("/get", methods=["GET", "POST"])
def chat_page():
    if request.method == 'POST':
        msg = request.form["msg"]
        input_msg = msg
        # print(input)
        result=qa_connection.qa({"query": input_msg})
        return str(result["result"])
    return render_template('chat.html')

if __name__ == "__main__":
    app.run(debug=False)

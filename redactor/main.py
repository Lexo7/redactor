from flask import Flask, render_template, request, redirect, url_for, send_from_directory, send_file
from utilities import convert_word_to_pdf, convert_text_to_pdf, most_searched, process_data, justification
from werkzeug.utils import secure_filename
from flaskwebgui import FlaskUI
import os
import random
from datetime import datetime
import time

from glob import glob
from io import BytesIO
from zipfile import ZipFile

app = Flask(__name__)
# ui = FlaskUI(app, server="flask") 

app.config['UPLOAD_FOLDER'] = './static/'

details = {
    "original file":"",
    "framed file":"",
    "redacted file":"",
    "search terms":"",
    "most searched":[],
    "redacted_terms":None,
    "all_locations": None,
    "redacted_locations":None,
    "text":'',
    "scanned": False
}

'''
pyinstaller -w -F --add-data "C:/Users/User/Desktop/JOURNEY/PROJECTS/REDACTION/redactor/redactor;templates" --add-data "C:/Users/User/Desktop/JOURNEY/PROJECTS/REDACTION/redactor/redactor;static" --add-data "C:/Users/User/Desktop/JOURNEY/PROJECTS/REDACTION/redactor/redactor;requirements.txt" --add-data "C:/Users/User/Desktop/JOURNEY/PROJECTS/REDACTION/redactor/redactor;utilities.py" main.py
'''

@app.route("/", methods=["GET", "POST"])
def index():
    #print(details)
    if request.method == "GET":
        for file in glob(os.path.join(app.config['UPLOAD_FOLDER'], '*.*')):
            os.remove(file)
        return render_template('index.html')
    
    if request.method == "POST":
        
        # Find out if the scanned box was checked
        scanned = request.form.getlist('scanned')
        print("Scanned: ", scanned)
        
        if scanned:
            print("Scanned box has been checked")
            details["scanned"] = True
        
        # List of accepted file extensions
        accepted_extensions = ['doc', 'pdf', 'docx', 'txt']
        
        # Get the text 
        text = request.form['text']
        details["text"] = text
        if not request.files['file']:
            message = 'Please Upload a file'
            print(message)
            return render_template("index.html", message = message)
        
        else:
            # Get the file
            file = request.files['file']
            
            # Sanitize the filename
            filename = secure_filename(file.filename)
            
            # Check for the extension of the uploaded file
            file_ext = filename.split('.')[-1].lower()
            
            print('File Name:', filename)
            # Check if file extension is acceptable
            if file_ext in accepted_extensions:
                
                print("Accepted File Name:", filename)
                # Move file to static folder
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print("Path to File: ", filepath)
                details["original file"] = filepath
                print(details)
                
                # Save file to the static folders
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
                #convert_word_to_pdf
                if file_ext.lower() in ['doc', 'docx']:
                    filename = convert_word_to_pdf(filepath)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    details["original file"] = filepath
                    print(filename)
                
                # Convert text to pdf
                if file_ext.lower() == 'txt':
                    filename = convert_text_to_pdf(filepath)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    details["original file"] = filepath
                    print(filename)
                
                return redirect(url_for("workspace", filename=filename))
            else:
                message = f'{filename} is not an acceptable file format'
                return render_template("index.html", message = message)    
        
        #render_template('index.html')
    render_template('index.html')

@app.route("/workspace/<filename>", methods=["GET", "POST"])
def workspace(filename):
    if request.method == "GET":
        print("Filename in workspace:",filename)
        # file = send_from_directory(app.config["UPLOAD_FOLDER"], filename)
        # print("Actual file: ", file)
        # print("Actual file: ", file.filename)
        return render_template('workspace.html', filename=filename)
    
    if request.method == "POST":
        terms = request.form['searchterms']
        print(terms)
        # Convert the terms into a list
        terms = list(terms.split(','))
        # Get the most searched terms
        most_searched_terms = most_searched(terms)
        print("New terms:", terms)
        print("Most searched terms:", most_searched_terms)
        
        # Add the search terms and the most searched terms to the details dictionary
        details["most searched"] = most_searched_terms
        details["search terms"] = terms
        
        print("How does the dictionary look like:",details)
        
        # Get original file name
        originalfilename = details["original file"].split('/')[-1]
        
        # Give name to text-framed file
        framedfile = 'framed_' + originalfilename
        framedfile = secure_filename(framedfile)
        print("Framed file name:", framedfile)
        
        # Get the original file
        input_file = details["original file"]
        print("Input filepath", input_file)
        
        # Get the output file
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], framedfile)
        print("Output filepath", output_file)
        
        # Check if the document is scanned and perform the following operations
        if details["scanned"] == True:
            # Pass the input file through the OCR Engine
            
            # Save the path to the output file
            details["framed file"] = output_file
            
            # Redirect the url
            return redirect(url_for("framed_text", framedfile=framedfile))
        
        all_locations = process_data(input_file, output_file, terms)
        print(all_locations)
        details["framed file"] = output_file
        # Add the locations to the details dictionary
        details['all_locations'] = all_locations
        return redirect(url_for("framed_text", framedfile=framedfile))
    

@app.route("/framedtext/<framedfile>", methods=["GET", "POST"])
def framed_text(framedfile):
    # args = request.args
    # framedfile = args.get("framedfile")
    # print("First framed file: ", framedfile)
    # framedfile = details["framed file"]   
    # print("Second framed file: ", framedfile) 
    print("Details:",details)
    if request.method == "GET":
        print("This is the name of the framed text file: ", framedfile)
        print(type(framedfile))
        return render_template("framed.html", filename=framedfile, searchterms=details["search terms"], locations=details["all_locations"])
    #print("This is the name of the framed text file", framedfile)
    
    if request.method == "POST":
        text_to_redact = request.form.getlist('forRedaction')
        print("Text to redact:", text_to_redact)
        
        details["redacted_terms"] = text_to_redact
        
        # Get original file name
        originalfilename = details["original file"].split('/')[-1]
        
        # Give name to redacted file
        redactedfile = 'redacted_' + originalfilename
        redactedfile = secure_filename(redactedfile)
        print("Redacted file name:", redactedfile)
        
        # Get the original filepath
        input_file = details["original file"]
        print("Input filepath", input_file)
        
        # Get the output filepath
        output_file = os.path.join(app.config['UPLOAD_FOLDER'], redactedfile)
        print("Output filepath", output_file)
        
        redacted_locations = process_data(input_file, output_file, text_to_redact, action="Redact")
        details["redacted file"] = output_file
        
        # Add locations of the redacted text
        details["redacted_locations"] = redacted_locations
        
        # Print redacted locations
        print(redacted_locations)
        
        return redirect(url_for("redaction", redactedfile=redactedfile))
        # return "coming through"
    # return render_template('framed.html', filename=framedfile)    

@app.route("/redaction/<redactedfile>", methods=["GET", "POST"])
def redaction(redactedfile):
    if request.method == "GET":
        # Get details to create the justification file
        outfile = os.path.join(app.config['UPLOAD_FOLDER'], 'Justification.txt')
        redacted_terms = details["redacted_terms"]
        redacted_terms_locations = details["redacted_locations"]
        text = details["text"]
        justification(redacted_terms, redacted_terms_locations, outfile, text)
        return render_template('redaction.html', filename=redactedfile, locations=details["redacted_locations"], terms=details["redacted_terms"])
    
    if request.method == "POST":
        target = app.config['UPLOAD_FOLDER']

        stream = BytesIO()
        with ZipFile(stream, 'w') as zf:
            for file in glob(os.path.join(target, '*.*')):
                zf.write(file, os.path.basename(file))
        stream.seek(0)
        
        details["original file"] = ""
        details["framed file"] = ""
        details["redacted file"] = ""
        details["search terms"] = ""
        details["most searched"] = []
        details["redacted_terms"] = None
        details["all_locations"] = None
        details["redacted_locations"] = None
        details["text"] = ''
        

        return send_file(
            stream,
            as_attachment=True,
            download_name='archive.zip'
        )    
    
if __name__ == "__main__":
    app.run(debug=True)
    #ui.run()
    #FlaskUI(app=app, server="flask").run()
# Import Libraries
import aspose.words as aw
from fpdf import FPDF
from typing import Tuple
from io import BytesIO
import os
import argparse
import re
import fitz

# Function to Convert Word file to pdf
def convert_word_to_pdf(filepath):
    filename = filepath.split('/')[-1].split('.')[0]
    print(filename)
    
    # Load word document
    doc = aw.Document(filepath)
    
    # Save as PDF
    doc.save(os.path.join('./static/', f'{filename}.pdf'))
    
    # Remove file to save space
    os.remove(filepath)
    
    newFilename = f'{filename}.pdf'
    
    print(newFilename)
    
    return newFilename

# Convert text file to pdf
def convert_text_to_pdf(filepath):
    filename = filepath.split('/')[-1].split('.')[0]
    print(filename)
    # save FPDF() class into
    # a variable pdf
    pdf = FPDF()  
    
    # Add a page
    pdf.add_page()
    
    # set style and size of font
    # that you want in the pdf
    pdf.set_font("Arial", size = 12)
    
    # open the text file in read mode
    f = open(filepath, "r")
    
    # insert the texts in pdf
    for x in f:
        pdf.cell(200, 10, txt = x, ln = 1, align = 'C')
    
    # save the pdf with name .pdf
    pdf.output(os.path.join('./static/', f'{filename}.pdf'))
    
    f.close()
    
    # Remove file to save space
    os.remove(filepath)
    
    # Get the file name
    newFilename = f'{filename}.pdf'
    
    print("New file name:",newFilename)
    
    return newFilename 

# Convert file to pdf
def convert_to_pdf(file):
    
    # Check for file extension
    extension = ''
    
    if extension in ['doc', 'docx']:
        convert_word_to_pdf(file)
    elif extension == 'txt':
        convert_text_to_pdf(file)
        
    return file    

# Function to return most searched terms
def most_searched(searchterms):
    data = []
    for term in searchterms:
        data.insert(0, term)
    if len(data) > 10:
        data.pop()
    
    return data

# This function extracts information from the pdf file
def extract_info(input_file: str):
    """
    Extracts file info
    """
    # Open the PDF
    pdfDoc = fitz.open(input_file)
    output = {
        "File": input_file, "Encrypted": ("True" if pdfDoc.isEncrypted else "False")
    }
    # If PDF is encrypted the file metadata cannot be extracted
    if not pdfDoc.isEncrypted:
        for key, value in pdfDoc.metadata.items():
            output[key] = value
    # To Display File Info
    print("## File Information ##################################################")
    print("\n".join("{}:{}".format(i, j) for i, j in output.items()))
    print("######################################################################")
    return True, output     

# This function searches for a string within the document lines
def search_for_text(lines, search_str):
    """
    Search for the search string within the document lines
    """
    for line in lines:
        # Find all matches within one line
        results = re.findall(search_str, line, re.IGNORECASE)
        # In case multiple matches within one line
        for result in results:
            yield result       
            
# This function redacts any matching values in the search term
def redact_matching_data(page, matched_values):
    """
    Redacts matching values
    """
    matches_found = 0
    # Loop throughout matching values
    for val in matched_values:
        matches_found += 1
        matching_val_area = page.searchFor(val)
        # Redact matching values
        [page.addRedactAnnot(area, text=" ", fill=(0, 0, 0))
         for area in matching_val_area]
    # Apply the redaction
    page.apply_redactions()
    return matches_found

# This function frames any matching text in the search terms
def frame_matching_data(page, matched_values):
    """
    frames matching values
    """
    #print("All values to frame: ", matched_values)
    matches_found = 0
    # Loop throughout matching values
    for val in matched_values:
        #print("Value to frame:", val)
        matches_found += 1
        matching_val_area = page.searchFor(val)
        for area in matching_val_area:
            if isinstance(area, fitz.fitz.Rect):
                # Draw a rectangle around matched values
                annot = page.addRectAnnot(area)
                # , fill = fitz.utils.getColor('black')
                annot.setColors(stroke=fitz.utils.getColor('red'))
                # If you want to remove matched data
                #page.addFreetextAnnot(area, ' ')
                annot.update()
    # print("Matches found from frame function: ", matches_found)
    return matches_found

def get_locations(lines, term, page_num):
    # Create an empty dictionary for the term
    locations = {}
    
    # Make the term the key of the dictionary
    locations[term] = {}
    
    # Create variables for the other features needed from the page
    locations[term]['pages'] = []
    locations[term]['line_number'] = []
    locations[term]['line_text'] = []
    
    for i in range(len(lines)):
        # Find all matches within one line
        results = re.findall(term, lines[i], re.IGNORECASE)
        if len(results) != 0:
            print("Found ",results," in ",lines[i])
            locations[term]['pages'].append(page_num+1)
            locations[term]['line_number'].append(i)
            locations[term]['line_text'].append(lines[i])
    
    return locations

# Function to assign reasons for redacting text in document
def funcreason(term):
    reasontext = ''
    if term[-1] == '*':
        reasontext = "name(s) of (a) natural person(s) other than those referred to in Article 39e(1) of Regulation (EC) No 178/2002"
        return reasontext
    elif term[-1] == '$':
        reasontext = "handwritten signature(s)"
        return reasontext
    elif term[-1] == '&':
        reasontext = "personal contact details (Telefonnummer/Durchwahl, Email und auch Strasse bzw. GPS Daten des Feldes wenn Privatbesitz bei Residue und Wirksamkeitsversuchen)"
        return reasontext
    elif term[-1] == '%':
        reasontext = "name(s) of (a) natural person(s ) involved in vertebrate testing. These are also being confidential as referred to Art. 63 (2)(g) of Regulation (EU) 1107/2009 and Art. 39e(2) of Reg. (EU) 178/2002 (nur bei Vertebratenstudien)"
        return reasontext
    elif term[-1] == '#':
        reasontext = "name(s) and address(es) of (a) natural person(s ) involved in vertebrate testing. These are also being confidential as referred to Art. 63 (2)(g) of Regulation (EU) 1107/2009 and Art. 39e(2) of Reg. (EU) 178/2002 (nur bei Vertebratenstudien)"
        return reasontext
    elif term[-1] == '!':
        reasontext = "label of the test facilicy (nur bei Vertebratenstudien)"
        return reasontext
    elif term[-1] == '?':
        reasontext = "abbreviation of the test facility"
        return reasontext
    else:
        reasontext = "No justification for the text"
        return reasontext


# Function to create and save justification file
def justification(redacted_terms, locations, outfile, text):
    identifier = ['*','$','&','%','#','!','?']

    for term in redacted_terms:
        reason = funcreason(term)
        for id in identifier:
            if term.endswith(id):
                term = term.replace(term[-1],'')
        for i in range(len(locations)):
            for key, value in locations[i].items():
                if key.lower() == term.lower():
                    if len(locations[i][term]['pages']) > 0:
                        with open(outfile, 'a') as file:
                            file.write(text)
                            for j in range(len(locations[i][term]['pages'])):
                                file.write(f"---{term} on page {locations[i][term]['pages'][j]}, line {locations[i][term]['line_number'][j]} has been redacted because it is {reason} \n")   

# This function puts all the methods above together
def process_data(input_file: str, output_file: str, searchterms: list, pages: Tuple = None, action: str = 'Frame'):
    """
    Process the pages of the PDF File
    """
    # Sanitize search term
    identifier = ['*','$','&','%','#','!','?']
    
    # Open the PDF
    pdfDoc = fitz.open(input_file)
    # Save the generated PDF to memory buffer
    output_buffer = BytesIO()
    total_matches = 0
    
    # Get the final set of locations
    all_locations = []
    
    # Iterate through pages
    for pg in range(pdfDoc.pageCount):
        # If required for specific pages
        if pages:
            if str(pg) not in pages:
                continue
        # Select the page
        page = pdfDoc[pg]
        # Get Matching Data
        for search_str in searchterms:
            # Sanitize search string
            for id in identifier:
                if search_str.endswith(id):
                    search_str = search_str.replace(search_str[-1],'')
            # Split page by lines
            page_lines = page.getText("text").split('\n')
            page_locations = get_locations(page_lines, search_str, pg)
            all_locations.append(page_locations)
            matched_values = search_for_text(page_lines, search_str)
            if matched_values:
                if action == 'Redact':
                    matches_found = redact_matching_data(page, matched_values)
                elif action == 'Frame':
                    matches_found = frame_matching_data(page, matched_values)
                else:
                    matches_found = frame_matching_data(page, matched_values)
                total_matches += matches_found
    print(f"{total_matches} Match(es) Found of Search terms {searchterms} In Input File: {input_file}")
    # Save to output
    pdfDoc.save(output_buffer)
    pdfDoc.close()
    # Save the output buffer to the output file
    with open(output_file, mode='wb') as f:
        f.write(output_buffer.getbuffer())
    
    return all_locations    
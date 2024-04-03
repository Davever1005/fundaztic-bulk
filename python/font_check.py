from pdfminer.layout import LTTextContainer, LTChar
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject
import os
import json

def text_extraction(element):
    # Extracting the text from the in-line text element
    line_text = element.get_text()
    
    # Find the formats of the text
    # Initialize the list with all the formats that appeared in the line of text
    line_bbox = []
    line_formats = []
    for text_line in element:
        if isinstance(text_line, LTTextContainer):
            # Iterating through each character in the line of text
            for character in text_line:
                if isinstance(character, LTChar):
                    # Append the font name of the character
                    line_formats.append(character.fontname)
                    # Append the font size of the character
                    # line_formats.append(character.size)
            line_bbox.append(text_line.bbox)
    # Find the unique font sizes and names in the line
    format_per_line = list(set(line_formats))
    
    # Return a tuple with the text in each line along with its format
    return (line_text, format_per_line, line_bbox)

def process_fonts(page_resource):
    fonts = {}
    for font_name, font_ref in page_resource.get('/Font', {}).items():
        font_obj = font_ref.get_object()
        fonts[font_name] = font_obj.get('/BaseFont', '')[1:]
    return fonts

def extract_fonts(pdf_file):
    with open(pdf_file, 'rb') as file:
        pdf_reader = PdfReader(file)
        font_data = []
        for page_num in range(len(pdf_reader.pages)): 
            page = pdf_reader.pages[page_num]
            page_resource = page.get('/Resources')
            if page_resource and '/Font' in page_resource: 
                font_data.append(process_fonts(page_resource))
        return font_data 
    
def draw_rectangles(pdf_path, results, unique_list, empty):
    # Open the original PDF
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    [writer.add_page(page) for page in reader.pages]
    fraud = []
    for result in results:
        line_text, line_formats, line_bbox = result[1]
        if empty:
            for idx, font in enumerate(line_formats):
                if  '+' in font:
                    line_formats[idx] = font.split('+')[1]

        if any(font not in unique_list for font in line_formats):
            fraud.append(result[0] + 1)
            # Draw a rectangle for each line of text
            for bbox in line_bbox:
                x0, y0, x1, y1 = bbox
                quad_points = [bbox[0], bbox[1], bbox[2], bbox[1], bbox[0], bbox[3], bbox[2], bbox[3]]
                width = x1 - x0
                height = y1 - y0
                annotation = Highlight(
                    rect=bbox,
                    quad_points=ArrayObject([FloatObject(quad_point) for quad_point in quad_points]),
                )
            writer.add_annotation(page_number=result[0], annotation=annotation)

    # Write the annotated file to disk
    annotated_path = os.path.join(os.getenv('TMP', '/tmp'), "annotated.pdf")
    with open(annotated_path, "wb") as fp:
        writer.write(fp)
    fraud = list(set(fraud))
    fraud.sort()
    if len(fraud) > 0:
        fraud_json = json.dumps({"page": ', '.join(map(str, sorted(fraud)))})
    else:
        fraud_json = json.dumps({"good": str("No different fonts found.")})
    return fraud_json
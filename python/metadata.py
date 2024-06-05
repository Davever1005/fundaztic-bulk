from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument

def metadata(file_path):
    fp = open(file_path, 'rb')
    parser = PDFParser(fp)
    doc = PDFDocument(parser)

    return doc.info
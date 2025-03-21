import pdfplumber

def getAllLinesFromPDF(file):
    """
    Extracts all lines of text from a PDF file, page by page, from top to bottom.

    Args:
        file (str): The path to the PDF file.

    Returns:
        list: A list of strings, where each string represents a line of text from the PDF.
              Lines are ordered from top to bottom across all pages.
    """
    with pdfplumber.open(file) as pdf:
        # Initialize an empty list to store all lines of text from the PDF
        allLines = []

        # Loop through each page in the PDF
        for page in pdf.pages:
            
            # Extract the full text content of the current page
            text = page.extract_text()

            # Split the page's text into individual lines using the newline character ('\n')
            # Each line represents a line of text as it appears in the PDF
            lines = text.split('\n')

            # Add the lines from the current page to the list of all lines
            allLines.extend(lines)

        # Return the combined list of lines from all pages
        return allLines

# args: lines - lines from pdf as each line is an element in a list i.e. [[line1],[line2],[line3]]
def extractPartsOfLines(lines):

    # loops through list of lines given - line becomes an element in the list i.e. a single list that is a line
    for line in lines:

        # splits lines into elements of a list - ie. ['itemnumber', 'brand', 'color']
        parts = line.split()

        # part of checking if a line is a shirt - item code is always the first element
        itemCode = parts[0]
        
        # checks if line is a shirt, by checking if item code is there (8 numerical digits)
        if len(itemCode) == 8 and itemCode.isdigit():

            # get brand from list of elements - brand will always start at index 1, end at index before the hyphen
            # Find the index of the first hyphen
            index_of_hyphen = parts.index('-')

            # Extract the brand (from index 1 to the index before the hyphen)
            brand = ' '.join(parts[1:index_of_hyphen])







# Example usage
lines = getAllLinesFromPDF('invoices/invoice.pdf')
extractPartsOfLines(lines)
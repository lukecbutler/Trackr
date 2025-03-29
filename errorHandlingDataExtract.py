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

""" GET BRAND """
def getBrand(partsOfLine):
    # get brand from list of elements - brand will always start at index 1, end at index before the hyphen
    # Find the index of the first hyphen

    indexOfFirstHyphen = partsOfLine.index('-')

    # Extract the brand (from index 1 to the index before the hyphen)
    brand = ' '.join(partsOfLine[1:indexOfFirstHyphen])

    return brand


""" GET DESCRIPTION """
def getDescription(partsOfLine):
    # Find the index of the first hyphen
    indexOfFirstHyphen = partsOfLine.index('-')

    # Find the index of the second hyphen
    indexOfSecondHyphen = partsOfLine.index('-', indexOfFirstHyphen + 1)

    # Extract the description (from the index after the first hyphen to the index before the second hyphen)
    description = ' '.join(partsOfLine[indexOfFirstHyphen + 1:indexOfSecondHyphen])

    return description

""" GET COLOR """
def getColor(partsOfLine):
    # check for parts[-7].isAlpha, parts[-6].isAlpha, and parts[-5].isAlpha
    # if not not parts[-7].isAlpha, parts[-6].isAlpha, and parts[-5].isAlpha, then check for parts[-6].isAlpha, and parts[-5].isAlpha
    # if not parts[-6].isAlpha, and parts[-5].isAlpha then parts[-5] is the color, and the color is only one word
    # Check if parts[-7], parts[-6], and parts[-5] are alphabetic
    if partsOfLine[-7].isalpha() and partsOfLine[-6].isalpha() and partsOfLine[-5].isalpha():
        # Color is multi-word (e.g., "Solid Black Blend")
        color = ' '.join(partsOfLine[-7:-4])  # Adjust indices as needed
        return color
    elif partsOfLine[-6].isalpha() and partsOfLine[-5].isalpha():
        # Color is two words (e.g., "Light Blue")
        color = ' '.join(partsOfLine[-6:-4])  # Adjust indices as needed
        return color
    elif partsOfLine[-5].isalpha(): 
        # Color is a single word (e.g., "Kelly")
        color = partsOfLine[-5]
        return color
    else:
        # Handle cases where no valid color is found
        color = "No Color Found"
        return color



def getSize(partsOfLine):
    """Size"""
    size = partsOfLine[-4]
    return size
     

def getQuantity(partsOfLine):
    """Quantity"""
    quantity = partsOfLine[-3]
    return quantity

# args: lines - lines from pdf as each line is an element in a list i.e. [[line1],[line2],[line3]]
# returns: list of lists, where each list is a row from the table, with just the brand, description, color, size, and quanity 
def extractTableContent(lines):

    pdfTable = []

    # loops through list of lines given - line becomes an element in the list i.e. a single list that is a line
    for line in lines:

        # splits lines into elements of a list - ie. ['itemnumber', 'brand', 'color']
        partsOfLine = line.split()

        # part of checking if a line is a shirt - item code is always the first element
        itemCode = partsOfLine[0]
        
        # checks if line is a shirt, by checking if item code is there (8 numerical digits)
        if len(itemCode) == 8 and itemCode.isdigit(): # this is now each individual line

            # returns brand of shirt
            brand = getBrand(partsOfLine)

            # returns description of shirt
            description = getDescription(partsOfLine)

            # returns color of shirt
            color = getColor(partsOfLine)

            # returns size of shirt
            size = getSize(partsOfLine)

            # returns quantity of shirt
            quantity = getQuantity(partsOfLine)



            listOfNewTableContent = [brand, description, color, size, quantity]
            pdfTable.append(listOfNewTableContent)

    return pdfTable

lines = getAllLinesFromPDF('invoices/invoice2.pdf')
extractTableContent(lines)
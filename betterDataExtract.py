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
# returns: list of lists, where each list is a row from the table, with just the brand, description, color, size, and quanity 
def extractTableContent(lines):
    pdfTable = []

    for line in lines:

        partsOfLine = line.split()
        if not partsOfLine:  # Skip empty lines
            continue
            
        try:
            itemCode = partsOfLine[0]

            # checks if line is a shirt, by checking if item code is there (8 numerical digits)
            if len(itemCode) == 8 and itemCode.isdigit():
                """BRAND"""
                # Find the index of the first hyphen
                try:
                    indexOfFirstHyphen = partsOfLine.index('-')
                except ValueError as e:
                    print(f"Could not find first hyphen in line: {line}")
                    continue
                
                # Extract the brand (from index 1 to the index before the hyphen)
                brand = ' '.join(partsOfLine[1:indexOfFirstHyphen])

                """DESCRIPTION"""
                # Find the index of the second hyphen
                try:
                    indexOfSecondHyphen = partsOfLine.index('-', indexOfFirstHyphen + 1)
                except ValueError as e:
                    print(f"Could not find second hyphen in line: {line}")
                    continue
                
                # Extract the description
                description = ' '.join(partsOfLine[indexOfFirstHyphen + 1:indexOfSecondHyphen])

                """COLOR"""
                color = "No Color Found"
                # Check different possible positions for color
                if len(partsOfLine) >= 7 and partsOfLine[-7].isalpha() and partsOfLine[-6].isalpha() and partsOfLine[-5].isalpha():
                    color = ' '.join(partsOfLine[-7:-4])
                elif len(partsOfLine) >= 6 and partsOfLine[-6].isalpha() and partsOfLine[-5].isalpha():
                    color = ' '.join(partsOfLine[-6:-4])
                elif len(partsOfLine) >= 5 and partsOfLine[-5].isalpha():
                    color = partsOfLine[-5]
                else:
                    print(f"Could not determine color in line: {line}")

                """Size"""
                size = partsOfLine[-4] if len(partsOfLine) >= 4 else "Unknown"

                """Quantity"""
                quantity = partsOfLine[-3] if len(partsOfLine) >= 3 else "Unknown"

                listOfNewTableContent = [brand, description, color, size, quantity]
                pdfTable.append(listOfNewTableContent)
       
        except Exception as e:
            print(f"Error processing line: {line}")
            print(f"Error details: {str(e)}")
            continue

    return pdfTable
import pdfplumber

def processPDF(filePath):
    """
    Processes a PDF file and extracts shirt information from it.

    Args:
        filePath (str): The path to the PDF file.

    Returns:
        list: A list of lists. Each sublist contains:
              [brand, description, color, size, quantity]
    """
    # This list will store all the extracted shirt entries
    extractedShirts = []

    # Open the PDF file using pdfplumber
    with pdfplumber.open(filePath) as pdf:

        # Loop through each page in the PDF
        for page in pdf.pages:

            # Extract text from the current page
            text = page.extract_text()

            # If the page is blank or extraction failed, skip it
            if not text:
                continue

            # Split the text into lines using newline character
            lines = text.split('\n')

            # Loop through each line of text
            for line in lines:

                # Split the line into individual words or parts
                parts = line.split()

                # Skip empty lines
                if not parts:
                    continue

                try:
                    # The first part should be the 8-digit item code
                    itemCode = parts[0]

                    # Check if this line is likely about a shirt (8-digit code)
                    if len(itemCode) == 8 and itemCode.isdigit():

                        # Try to find the positions of the two hyphens
                        try:
                            indexFirstHyphen = parts.index('-')
                            indexSecondHyphen = parts.index('-', indexFirstHyphen + 1)
                        except ValueError:
                            print(f"Skipping line with missing hyphens: {line}")
                            continue

                        # The BRAND is everything between the itemCode and the first hyphen
                        brand = ' '.join(parts[1:indexFirstHyphen])

                        # The DESCRIPTION is between the first and second hyphen
                        description = ' '.join(parts[indexFirstHyphen + 1:indexSecondHyphen])

                        # --- Determine COLOR ---
                        color = "Unknown"  # Default fallback if color isn't found

                        # Try checking for 3-word color
                        if len(parts) >= 7 and all(p.isalpha() for p in parts[-7:-4]):
                            color = ' '.join(parts[-7:-4])
                        # Try checking for 2-word color
                        elif len(parts) >= 6 and all(p.isalpha() for p in parts[-6:-4]):
                            color = ' '.join(parts[-6:-4])
                        # Try checking for 1-word color
                        elif len(parts) >= 5 and parts[-5].isalpha():
                            color = parts[-5]
                        else:
                            print(f"Could not determine color in line: {line}")

                        # SIZE
                        size = parts[-4] if len(parts) >= 4 else "Unknown"

                        # QUANTITY
                        quantity = parts[-3] if len(parts) >= 3 else "Unknown"

                        # Save the extracted data
                        extractedShirts.append([brand, description, color, size, quantity])

                except Exception as e:
                    # Catch unexpected issues and continue
                    print(f"Error processing line: {line}\nDetails: {str(e)}")

    # Return the full list of extracted shirts
    return extractedShirts


'''

PDF data extraction that for sure works






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

'''
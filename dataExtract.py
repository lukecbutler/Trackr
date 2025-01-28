import pdfplumber

# Path to your PDF file
file_path = "invoice.pdf"


# take in line of table - return values in list format
def pdfToListOfShirts():

        # take in entire text - create pg1 & p2 lines of shirt data
    with pdfplumber.open(file_path) as pdf:

        # show entire document raw
        # clean page 1 data
        page1 = pdf.pages[0]
        text1 = page1.extract_text()
        page1shirts = text1[451:-49]
        #print(page1shirts)
        # clean page 2 data
        page2 = pdf.pages[1]
        text2 = page2.extract_text()
        page2shirts = text2[47:-265]
        #print(page2shirts)

        pg1ShirtLines = page1shirts.split("\n")
        pg2ShirtLines = page2shirts.split("\n")
        allLines = pg1ShirtLines + pg2ShirtLines

    entireList = []
    for i in allLines:
        line = i

        parts = line.split()
        #The first element is always the ID, so skip it
        descriptionStart = 1

        # Incorporate when things get messy
        # Known color names to look for
        knownColors = {"Kelly", "Black", "Graphite", "Royal"}

        # Known size patterns to look for
        knownSizes = {"S", "M", "L", "XL", "One", "Adjustable", "5T"}

        # Find where description ends (the second hyphen)
        descriptionEnd = 0
        counter = 0
        for i in range(1, len(parts)):
            if parts[i] == "-":
                counter += 1
                if counter == 2:
                    descriptionEnd = i
                    break
                continue
        #extract the description
        description = " ".join(parts[descriptionStart:descriptionEnd])

        color = parts[-5]
        size = parts[-4]
        quantity = parts[-3]


        currentList = [description, color, size, quantity]
        entireList.append(currentList)

    return entireList

def createTable():
    # Header and data
    header = ["Description", "Color", "Size", "Quantity"]
    shirt_data = pdfToListOfShirts()

    # Calculate the maximum width of each column
    col_widths = [
        max(len(str(row[i])) for row in ([header] + shirt_data))
        for i in range(len(header))
    ]

    # Create a row format string based on column widths
    row_format = "  ".join(f"{{:<{width}}}" for width in col_widths)

    # Print the header
    print(row_format.format(*header))
    print("-" * (sum(col_widths) + 2 * (len(col_widths) - 1)))

    # Print each row of data
    for row in shirt_data:
        print(row_format.format(*row))

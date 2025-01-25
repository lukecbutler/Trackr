import pdfplumber
import re

# Path to your PDF file
file_path = "invoice.pdf"

with pdfplumber.open(file_path) as pdf:

    # show entire document raw
    # clean page 1 data
    page1 = pdf.pages[0]
    text1 = page1.extract_text()
    page1shirts = text1[451:-49]
    bill_to = re.search(r'Bill To(.+)',text1).group(1)
    #print(page1shirts)

    # clean page 2 data
    page2 = pdf.pages[1]
    text2 = page2.extract_text()
    page2shirts = text2[47:-265]
    #print(page2shirts)

pg1ShirtLines = page1shirts.split("\n")
pg2ShirtLines = page2shirts.split("\n")



def parse_line(line):

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

    return f"Description: {description}\nColor: {color}\nSize: {size}\nQuantity: {quantity}\n\n"


for i in pg1ShirtLines:
    print(parse_line(i))

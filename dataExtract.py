import pdfplumber

# take in file - return description, color, size and quantity values in list format
def pdfToListOfShirts(filename):

    # TODO: instead of speicifying page1, page2, etc. create for loop that loops through each page no matter the page amount

    # take in entire text - create pg1 & pg2 lines of shirt data
    with pdfplumber.open(filename) as pdf:

        # clean page 1 data
        page1 = pdf.pages[0]
        text1 = page1.extract_text()
        # This is only the shirt data from page 1
        page1shirts = text1[451:-49]

        # clean page 2 data
        page2 = pdf.pages[1]
        text2 = page2.extract_text()
        # This is only the shirt data from page 2
        page2shirts = text2[47:-265]

        #split the shirt data into lines, and combie to form variable allLines
        pg1ShirtLines = page1shirts.split("\n")
        pg2ShirtLines = page2shirts.split("\n")
        allLines = pg1ShirtLines + pg2ShirtLines
        return allLines


lines = pdfToListOfShirts('invoices/invoice2.pdf')
for line in lines:
    print(line)
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


    # create list that will hold the rows of information once cleaned
    entireList = []

##################################################################################################################################################
    for i in allLines:
        line = i

        # each line is split into the different string of characters
        parts = line.split()

        #The first element is always the ID, so skip it
        descriptionStart = 1
        print(parts)

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



        # check for parts[-7].isAlpha, parts[-6].isAlpha, and parts[-5].isAlpha
        # if not not parts[-7].isAlpha, parts[-6].isAlpha, and parts[-5].isAlpha, then check for parts[-6].isAlpha, and parts[-5].isAlpha
        # if not parts[-6].isAlpha, and parts[-5].isAlpha then parts[-5] is the color, and the color is only one word
        color = parts[-5]
        size = parts[-4]
        quantity = parts[-3]
        


        currentList = [description, color, size, quantity]
        entireList.append(currentList)

        #print(currentList)

    return entireList

pdfToListOfShirts('invoice.pdf')
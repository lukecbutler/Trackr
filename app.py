from flask import Flask, request, jsonify, render_template
import pdfplumber

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("tester.html")

@app.route('/extract-pdf', methods=['POST'])
def extract_pdf():
    file = request.files['file']
    if not file:
        return jsonify({"error": "No file uploaded"}), 400
    
    with pdfplumber.open(file) as pdf:
        page1 = pdf.pages[0]
        text1 = page1.extract_text()
        page1shirts = text1[451:-49]
        pg1ShirtLines = page1shirts.split("\n")
        
        data = []
        for line in pg1ShirtLines:
            data.append(parse_line(line))
        
        return jsonify(data)

def parse_line(line):
    parts = line.split()
    descriptionStart = 1

    knownColors = {"Kelly", "Black", "Graphite", "Royal"}
    knownSizes = {"S", "M", "L", "XL", "One", "Adjustable", "5T"}

    descriptionEnd = 0
    counter = 0
    for i in range(1, len(parts)):
        if parts[i] == "-":
            counter += 1
            if counter == 2:
                descriptionEnd = i
                break
            continue
    description = " ".join(parts[descriptionStart:descriptionEnd])
    color = parts[-5]
    size = parts[-4]
    quantity = parts[-3]

    return {"description": description, "color": color, "size": size, "quantity": quantity}

if __name__ == "__main__":
    app.run(debug=True, port=80, host='0.0.0.0')

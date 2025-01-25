let inventory = JSON.parse(localStorage.getItem('inventory')) || [];

document.getElementById('addForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const description = document.getElementById('description').value;
    const color = document.getElementById('color').value;
    const size = document.getElementById('size').value;
    const pieces = document.getElementById('pieces').value;

    const newItem = { id: Date.now(), description, color, size, pieces };
    inventory.push(newItem);
    localStorage.setItem('inventory', JSON.stringify(inventory));
    renderInventory();
    e.target.reset();
});

function renderInventory() {
    const table = document.getElementById('inventoryTable');
    table.innerHTML = '';
    inventory.forEach(item => {
        const row = `<tr>
            <td>${item.description}</td>
            <td>${item.color}</td>
            <td>${item.size}</td>
            <td>${item.pieces}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="editItem(${item.id})">Edit</button>
                <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">Delete</button>
            </td>
        </tr>`;
        table.innerHTML += row;
    });
}

function deleteItem(id) {
    inventory = inventory.filter(item => item.id !== id);
    localStorage.setItem('inventory', JSON.stringify(inventory));
    renderInventory();
}

function editItem(id) {
    const item = inventory.find(i => i.id === id);
    if (item) {
        document.getElementById('description').value = item.description;
        document.getElementById('color').value = item.color;
        document.getElementById('size').value = item.size;
        document.getElementById('pieces').value = item.pieces;
        deleteItem(id);
    }
}

async function uploadPdf() {
    // Get the file from the input field
    const fileInput = document.getElementById('pdfInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a PDF file'); // If no file is selected, show an alert and stop
        return;
    }

    // Prepare the file to be sent to the server
    const formData = new FormData();
    formData.append('file', file); // Attach the file with the name 'file'

    try {
        // Send the file to the Flask backend
        const response = await fetch('http://localhost:5000/extract-pdf', {
            method: 'POST', // Send a POST request
            body: formData, // Send the file data
        });

        // Check if the response from the server is successful
        if (!response.ok) {
            throw new Error('Failed to extract PDF data'); // If there's an error, stop and show it
        }

        // Convert the server's response (JSON) into a JavaScript object
        const data = await response.json();

        // Add the extracted data to your inventory
        data.forEach(item => {
            const newItem = {
                id: Date.now(), // Generate a unique ID based on the current time
                description: item.description, // Use the description from the extracted data
                color: item.color, // Use the color from the extracted data
                size: item.size, // Use the size from the extracted data
                pieces: item.quantity, // Use the quantity from the extracted data
            };
            inventory.push(newItem); // Add the new item to the inventory list
        });

        // Save the updated inventory to local storage
        localStorage.setItem('inventory', JSON.stringify(inventory));

        // Refresh the table to show the updated inventory
        renderInventory();

    } catch (error) {
        console.error('Error:', error); // Log any errors that occurred
    }
}

// Get the inventory from localStorage or start with an empty array if there is none
let inventory = JSON.parse(localStorage.getItem('inventory')) || [];

// Add an event listener to the form for adding new items
document.getElementById('addForm').addEventListener('submit', function (e) {
    // Prevent the form from submitting in the traditional way (reloading the page)
    e.preventDefault();

    // Get values from the input fields
    const description = document.getElementById('description').value;
    const color = document.getElementById('color').value;
    const size = document.getElementById('size').value;
    const pieces = document.getElementById('pieces').value;

    // Create a new item object with a unique ID
    const newItem = {
        id: Date.now(), // Use the current time as a unique identifier
        description: description,
        color: color,
        size: size,
        pieces: pieces
    };

    // Add the new item to the inventory array
    inventory.push(newItem);

    // Save the updated inventory to localStorage
    localStorage.setItem('inventory', JSON.stringify(inventory));

    // Update the table to show the new item
    renderInventory();

    // Clear the form fields after adding the item
    e.target.reset();
});

// Function to display the inventory in the table
function renderInventory() {
    // Get the table body element where the inventory will be displayed
    const table = document.getElementById('inventoryTable');
    table.innerHTML = ''; // Clear any existing rows

    // Loop through each item in the inventory array
    for (let i = 0; i < inventory.length; i++) {
        const item = inventory[i];

        // Create a table row for the item
        const row = `
            <tr>
                <td>${item.description}</td>
                <td>${item.color}</td>
                <td>${item.size}</td>
                <td>${item.pieces}</td>
                <td>
                    <button class="btn btn-warning btn-sm" onclick="editItem(${item.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})">Delete</button>
                </td>
            </tr>
        `;

        // Add the row to the table
        table.innerHTML += row;
    }
}

// Function to delete an item from the inventory
function deleteItem(id) {
    // Create a new array that includes all items except the one with the matching ID
    const updatedInventory = [];
    for (let i = 0; i < inventory.length; i++) {
        if (inventory[i].id !== id) {
            updatedInventory.push(inventory[i]);
        }
    }

    // Update the inventory array and save it to localStorage
    inventory = updatedInventory;
    localStorage.setItem('inventory', JSON.stringify(inventory));

    // Refresh the table to reflect the changes
    renderInventory();
}

// Function to edit an item in the inventory
function editItem(id) {
    // Find the item in the inventory by its ID
    let itemToEdit = null;
    for (let i = 0; i < inventory.length; i++) {
        if (inventory[i].id === id) {
            itemToEdit = inventory[i];
            break;
        }
    }

    // If the item was found, populate the form fields with its values
    if (itemToEdit) {
        document.getElementById('description').value = itemToEdit.description;
        document.getElementById('color').value = itemToEdit.color;
        document.getElementById('size').value = itemToEdit.size;
        document.getElementById('pieces').value = itemToEdit.pieces;

        // Delete the item so it can be replaced when the user submits the form
        deleteItem(id);
    }
}

// Display the inventory when the page loads
renderInventory();

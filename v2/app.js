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

renderInventory();

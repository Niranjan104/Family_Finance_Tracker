const API_URL = window.location.origin;

// Fetch categories and populate dropdown
async function fetchCategories() {
    let response = await fetch(`${API_URL}/get_categories`);
    let categories = await response.json();
    let select = document.getElementById("category");
    select.innerHTML = '<option value="">Select</option>';
    categories.forEach(cat => {
        let option = document.createElement("option");
        option.value = cat.name;
        option.textContent = cat.name;
        select.appendChild(option);
    });
    let othersOption = document.createElement("option");
    othersOption.value = "Others";
    othersOption.textContent = "Others";
    select.appendChild(othersOption);
}

// Show/hide custom category input
document.getElementById("category").addEventListener("change", function() {
    let customCategoryLabel = document.getElementById("custom-category-label");
    let customCategoryDescLabel = document.getElementById("custom-category-desc-label");
    let customCategoryInput = document.getElementById("custom-category");
    let customCategoryDescInput = document.getElementById("custom-category-desc");
    if (this.value === "Others") {
        customCategoryLabel.style.display = "block";
        customCategoryDescLabel.style.display = "block";
        customCategoryInput.required = true;
        customCategoryDescInput.required = true;
    } else {
        customCategoryLabel.style.display = "none";
        customCategoryDescLabel.style.display = "none";
        customCategoryInput.required = false;
        customCategoryDescInput.required = false;
    }
});

// Fetch and display expenses
async function fetchExpenses() {
    let response = await fetch(`${API_URL}/get_expenses`);
    let expenses = await response.json();
    let tableBody = document.getElementById("expense-table-body");
    tableBody.innerHTML = "";

    expenses.forEach(exp => {
        let row = document.createElement("tr");
        row.setAttribute("data-id", exp.id);
        row.innerHTML = `
            <td>${exp.name}</td>
            <td>${exp.date}</td>
            <td>${exp.category}</td>
            <td>${exp.description || ""}</td>
            <td>₹${exp.amount}</td>
            <td>
                <button class="edit-btn" onclick="editExpense(${exp.id})">✏️</button>
                <button class="delete-btn" onclick="deleteExpense(${exp.id})">❌</button>
            </td>
            <td>
                ${exp.image ? `<a href="/uploads/${exp.image}" target="_blank">View</a>` : "No file"}
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Generate category dropdown options
function generateCategoryOptions(selectedCategory) {
    let categories = JSON.parse(localStorage.getItem("categories") || "[]");
    return categories.map(cat => 
        `<option value="${cat.name}" ${cat.name === selectedCategory ? "selected" : ""}>${cat.name}</option>`
    ).join("");
}

// Add new expense
document.getElementById("expense-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    let formData = new FormData(event.target);

    // Handle custom category
    let categorySelect = document.getElementById("category");
    if (categorySelect.value === "Others") {
        let customCategory = document.getElementById("custom-category").value;
        let customCategoryDesc = document.getElementById("custom-category-desc").value;
        formData.set("category", customCategory);
        formData.set("custom-category-desc", customCategoryDesc);
    }

    await fetch(`${API_URL}/add_expense`, {
        method: "POST",
        body: formData
    });

    fetchExpenses();
    event.target.reset();
    document.getElementById("custom-category-label").style.display = "none";
    document.getElementById("custom-category-desc-label").style.display = "none";
});

// Update expense field inline
async function updateExpense(id, field, value) {
    let formData = new FormData();
    formData.append(field, value);

    await fetch(`${API_URL}/edit_expense/${id}`, {
        method: "PUT",
        body: formData
    });

    fetchExpenses();
}

// Upload image
async function uploadImage(id, file) {
    let formData = new FormData();
    formData.append("file-upload", file);

    await fetch(`${API_URL}/edit_expense/${id}`, {
        method: "PUT",
        body: formData
    });

    fetchExpenses();
}

// Delete expense
async function deleteExpense(id) {
    await fetch(`${API_URL}/delete_expense/${id}`, { method: "DELETE" });
    fetchExpenses();
}

// Fetch and display expense details for editing
async function fetchExpenseDetails(id) {
    let response = await fetch(`${API_URL}/get_expense/${id}`);
    let expense = await response.json();

    document.getElementById("name").value = expense.name;
    document.getElementById("category").value = expense.category;
    document.getElementById("category-desc").value = expense.category_desc;
    document.getElementById("date").value = expense.date;
    document.getElementById("amount").value = expense.amount;
    document.getElementById("description").value = expense.description;
    document.getElementById("file-upload").value = ""; // Clear the file input
}

// Initialize
fetchCategories().then(() => {
    fetchExpenses();
});

const API_URL = window.location.origin;

const DEFAULT_CATEGORIES = ["Food🍕", "Transport🚂 ", "Bills💸", "Entertainment🤡","Shopping🛍️","Therapy 🩺", "Others"];

// Fetch categories and populate dropdown
async function fetchCategories() {
    let select = document.getElementById("category");
    select.innerHTML = '<option value="">Select</option>';
    // Add default categories
    DEFAULT_CATEGORIES.forEach(cat => {
        let option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        select.appendChild(option);
    });
}

// Show/hide custom category input
document.getElementById("category").addEventListener("change", function() {
    let customCategoryLabel = document.getElementById("custom-category-label");
    let customCategoryInput = document.getElementById("custom-category");
    if (this.value === "Others") {
        customCategoryLabel.style.display = "block";
        customCategoryInput.required = true;
    } else {
        customCategoryLabel.style.display = "none";
        customCategoryInput.required = false;
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
                ${exp.image_url ? `<img src="${exp.image_url}" class="thumbnail" onclick="showImagePopup('${exp.image_url}')" />` : "No file"}
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Show image in a popup
function showImagePopup(imageUrl) {
    let popup = document.createElement("div");
    popup.classList.add("image-popup");
    popup.innerHTML = `
        <div class="popup-content">
            <span class="close-btn" onclick="closeImagePopup()">&times;</span>
            <img src="${imageUrl}" />
        </div>
    `;
    document.body.appendChild(popup);
}

// Close image popup
function closeImagePopup() {
    let popup = document.querySelector(".image-popup");
    if (popup) {
        popup.remove();
    }
}

// Add new expense
document.getElementById("expense-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    let formData = new FormData(event.target);

    // Handle custom category
    let categorySelect = document.getElementById("category");
    if (categorySelect.value === "Others") {
        let customCategory = document.getElementById("custom-category").value;
        formData.set("category", customCategory);
    }

    let expenseId = document.getElementById("expense-id").value;
    let url = `${API_URL}/add_expense`;
    let method = "POST";

    if (expenseId) {
        url = `${API_URL}/edit_expense/${expenseId}`;
        method = "PUT";
    }

    let response = await fetch(url, {
        method: method,
        body: formData
    });

    let result = await response.json();
    fetchExpenses();
    event.target.reset();
    document.getElementById("custom-category-label").style.display = "none";
    document.getElementById("expense-id").value = ""; // Clear the hidden input field
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
    if (response.status === 404) {
        alert("Expense not found");
        return;
    }
    let expense = await response.json();

    document.getElementById("expense-id").value = expense.id; // Set the hidden input field with the expense ID
    document.getElementById("name").value = expense.name;
    document.getElementById("category").value = expense.category;
    document.getElementById("category-desc").value = expense.category_desc;
    document.getElementById("date").value = expense.date;
    document.getElementById("amount").value = expense.amount;
    document.getElementById("description").value = expense.description;
    document.getElementById("file-upload").value = ""; // Clear the file input

    // Show custom category input if the category is "Others" or a custom category
    if (expense.category === "Others" || !DEFAULT_CATEGORIES.includes(expense.category)) {
        document.getElementById("custom-category-label").style.display = "block";
        document.getElementById("custom-category").value = expense.category;
        document.getElementById("category").value = "Others";
    } else {
        document.getElementById("custom-category-label").style.display = "none";
    }
}

// Edit expense
async function editExpense(id) {
    await fetchExpenseDetails(id);
    document.getElementById("expense-form").scrollIntoView({ behavior: "smooth" });
}

// Initialize
fetchCategories().then(() => {
    fetchExpenses();
});

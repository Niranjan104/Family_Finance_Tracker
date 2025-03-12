const API_URL = window.location.origin;

const messages = [
    "💸 Counting your regrets… I mean, transactions… 💸",
    "🏦 Asking your bank if it’s okay to proceed… 📞",
];

function displayRandomMessage() {
    const messageContainer = document.getElementById("message");
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    messageContainer.textContent = randomMessage;
    messageContainer.style.textAlign = "center"; // Center the message
}

// Function to strip emojis from a string
function stripEmojis(text) {
    return text.replace(/[\u{1F600}-\u{1F64F}]/gu, '')
               .replace(/[\u{1F300}-\u{1F5FF}]/gu, '')
               .replace(/[\u{1F680}-\u{1F6FF}]/gu, '')
               .replace(/[\u{1F700}-\u{1F77F}]/gu, '')
               .replace(/[\u{1F780}-\u{1F7FF}]/gu, '')
               .replace(/[\u{1F800}-\u{1F8FF}]/gu, '')
               .replace(/[\u{1F900}-\u{1F9FF}]/gu, '')
               .replace(/[\u{1FA00}-\u{1FA6F}]/gu, '')
               .replace(/[\u{1FA70}-\u{1FAFF}]/gu, '')
               .replace(/[\u{2600}-\u{26FF}]/gu, '')
               .replace(/[\u{2700}-\u{27BF}]/gu, '');
}

// Update file upload label with file name
document.getElementById("file-upload").addEventListener("change", function() {
    const fileName = this.files[0] ? this.files[0].name : "Upload File";
    document.getElementById("file-upload-label").textContent = fileName;
});

// Fetch and display expenses
async function fetchExpenses(fromDate = "", toDate = "") {
    let url = `${API_URL}/get_expenses`;
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    let response = await fetch(url);
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
                <button class="edit-btn edit" onclick="editExpense(${exp.id})">✏️</button>
                <button class="delete-btn delete" onclick="deleteExpense(${exp.id})">❌</button>
            </td>
            <td>
                ${exp.image_url ? getFileLink(exp.image_url, exp.file_type) : "No file"}
            </td>
        `;
        tableBody.appendChild(row);
    });
    updateStats(fromDate, toDate);
}

function getFileLink(url, fileType) {
    const imageTypes = ["image/jpeg", "image/png"];
    if (imageTypes.includes(fileType)) {
        return `<img src="${url}" class="thumbnail" onclick="showImagePopup('${url}')" />`;
    } else if (fileType === "application/pdf") {
        return `<a href="${url}" target="_blank">👀📄</a>`;
    } else if (fileType === "application/msword" || fileType === "application/vnd.openxmlformats-officedocument.wordprocessingml.document") {
        return `<a href="${url}" target="_blank">📥📄</a>`;
    } else {
        return `<a href="${url}" target="_blank">View File</a>`;
    }
}

function openPdfInNewTab(url) {
    fetch(url)
        .then(response => response.blob())
        .then(blob => {
            const blobUrl = URL.createObjectURL(blob);
            window.open(blobUrl, '_blank');
        })
        .catch(error => console.error('Error opening PDF:', error));
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

// Show the add expense popup
document.getElementById("add-expense-btn").addEventListener("click", function() {
    document.getElementById("add-expense-popup").style.display = "flex";
    document.body.style.overflow = "hidden"; // Disable background scrolling
});

// Close the add expense popup
document.getElementById("close-popup-btn").addEventListener("click", function() {
    document.getElementById("add-expense-popup").style.display = "none";
    document.body.style.overflow = "auto"; // Enable background scrolling
});

// Add new expense
document.getElementById("expense-form").addEventListener("submit", async function(event) {
    event.preventDefault();
    let formData = new FormData(event.target);

    // Handle category
    let categorySelect = document.getElementById("category");
    formData.set("category", stripEmojis(categorySelect.value));

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
    fetchStats();
    event.target.reset();
    document.getElementById("expense-id").value = "";
    document.getElementById("file-upload-label").textContent = "Upload File";
    document.getElementById("add-expense-popup").style.display = "none"; // Close popup after submission
    document.body.style.overflow = "auto"; // Enable background scrolling
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
    if (!confirm("😃Sure you want to Delete?")) return;
    await fetch(`${API_URL}/delete_expense/${id}`, { method: "DELETE" });
    fetchExpenses();
    setTimeout(fetchStats, 500);
}

// Fetch expense details for editing
async function fetchExpenseDetails(id) {
    let response = await fetch(`${API_URL}/get_expense/${id}`);
    if (response.status === 404) {
        alert("Expense not found");
        return;
    }
    let expense = await response.json();
    document.getElementById("expense-id").value = expense.id;
    document.getElementById("name").value = expense.name;
    document.getElementById("category").value = expense.category;
    document.getElementById("category-desc").value = expense.category_desc;
    document.getElementById("date").value = expense.date;
    document.getElementById("amount").value = expense.amount;
    document.getElementById("description").value = expense.description;
    document.getElementById("file-upload").value = "";
}

// Edit expense
async function editExpense(id) {
    await fetchExpenseDetails(id);
    document.getElementById("add-expense-popup").style.display = "flex"; // Open the popup
    document.body.style.overflow = "hidden"; // Disable background scrolling
    document.getElementById("expense-form").scrollIntoView({ behavior: "smooth" });
}

// Filter expenses by date
document.getElementById("filter-btn").addEventListener("click", function() {
    const fromDate = document.getElementById("from-date").value;
    const toDate = document.getElementById("to-date").value;
    if (!fromDate || !toDate) {
        const alertBox = document.createElement("div");
        alertBox.textContent = "😯Please fill out both date fields😅 ";
        alertBox.style.position = "fixed";
        alertBox.style.top = "5px";
        alertBox.style.left = "50%";
        alertBox.style.transform = "translateX(-50%)";
        alertBox.style.backgroundColor = "#f44336";
        alertBox.style.color = "#fff";
        alertBox.style.padding = "20px";
        alertBox.style.borderRadius = "20px";
        alertBox.style.boxShadow = "3px 3px 10px rgba(0, 0, 0, 0.1)";
        document.body.appendChild(alertBox);
        setTimeout(() => { document.body.removeChild(alertBox); }, 2000);
        return;
    }
    fetchExpenses(fromDate, toDate);
});

// Refresh expense list
document.getElementById("refresh-btn").addEventListener("click", function() {
    document.getElementById("from-date").value = "";
    document.getElementById("to-date").value = "";
    fetchExpenses();
    fetchStats();
});

// Fetch and update stats
async function fetchStats() {
    let response = await fetch(`${API_URL}/get_stats`);
    let stats = await response.json();
    document.getElementById("total-spent-value").textContent = stats.total_spent.toFixed(2);
    document.getElementById("expense-count-value").textContent = stats.expense_count;
    document.getElementById("last-7days-spent-value").textContent = stats.last_7days_spent.toFixed(2);
    document.getElementById("highest-category-value").textContent = stats.highest_category;
    document.getElementById("highest-amount-value").textContent = stats.highest_amount.toFixed(2);
}

// Update stats based on filtered expenses
async function updateStats(fromDate, toDate) {
    let url = `${API_URL}/get_stats`;
    if (fromDate && toDate) {
        url += `?from_date=${fromDate}&to_date=${toDate}`;
    }
    let response = await fetch(url);
    let stats = await response.json();
    document.getElementById("total-spent-value").textContent = stats.total_spent.toFixed(2);
    document.getElementById("expense-count-value").textContent = stats.expense_count;
    document.getElementById("last-7days-spent-value").textContent = stats.last_7days_spent.toFixed(2);
    document.getElementById("highest-category-value").textContent = stats.highest_category;
    document.getElementById("highest-amount-value").textContent = stats.highest_amount.toFixed(2);
}

// Populate year select dropdown
function populateYearSelect() {
    const yearSelect = document.getElementById("year-select");
    const currentYear = new Date().getFullYear();
    for (let i = currentYear; i <= currentYear + 10; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        yearSelect.appendChild(option);
    }
}

// Toggle recurring status
async function toggleRecurring(id, isRecurring) {
    const confirmation = confirm(`Set as ${isRecurring ? "recurring" : "non-recurring"}?`);
    if (!confirmation) return;

    await fetch(`${API_URL}/toggle_recurring/${id}`, {
        method: "PUT",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ recurring: isRecurring })
    });
    fetchBudgets();
}

// Initialization
fetchExpenses();
fetchStats();
fetchBudgets(); // Fetch budgets on page load
populateYearSelect();
displayRandomMessage(); // Display message immediately on page load

// Helper function to show temporary alerts
function showTemporaryAlert(message, type = 'info') {
    const alertBox = document.createElement('div');
    alertBox.className = `alert ${type}`;
    alertBox.textContent = message;
    document.body.appendChild(alertBox);
    setTimeout(() => {
        alertBox.classList.add('fade-out');
        setTimeout(() => document.body.removeChild(alertBox), 300);
    }, 3000);
}

// Toggle dark mode
document.getElementById("dark-mode-toggle").addEventListener("click", function() {
    document.body.classList.toggle("dark-mode");
    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled");
});

// Set dark mode preference on load
window.addEventListener("load", function() {
    const darkMode = localStorage.getItem("darkMode");
    if (darkMode === "enabled") {
        document.body.classList.add("dark-mode");
    }
});

setInterval(displayRandomMessage, 3000);

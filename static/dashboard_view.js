document.addEventListener('DOMContentLoaded', function() {
    loadExpenseData();
    loadBudgetData();
});

function loadExpenseData(page = 1) {
    const fromDate = document.getElementById('from-date').value;
    const toDate = document.getElementById('to-date').value;
    
    fetch(`${API_URL}/get_expenses?from_date=${fromDate}&to_date=${toDate}&page=${page}`, { 
        credentials: 'include' 
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayExpenses(data.expenses);
            updateExpensePagination(data.current_page, data.total_pages);
        })
        .catch(error => {
            console.error('Error fetching expense data:', error);
            const tableBody = document.getElementById('expense-table-body');
            tableBody.innerHTML = `<tr><td colspan="6" class="empty-table-message">Failed to load expenses. Please try again later.</td></tr>`;
        });
}

function loadBudgetData(page = 1) {
    fetch(`${API_URL}/get_budgets?page=${page}`, { 
        credentials: 'include',
        headers: {'Cache-Control': 'no-cache'}
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        displayBudgets(data.budgets);
        updateBudgetPagination(data.current_page, data.total_pages);
    })
    .catch(error => {
        console.error('Error fetching budget data:', error);
        const tableBody = document.getElementById('budget-table-body');
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-table-message">No budgets configured</td></tr>`;
    });
}

function updateExpensePagination(currentPage, totalPages) {
    const paginationControls = document.getElementById("expense-pagination-controls");
    paginationControls.innerHTML = `
        <button onclick="loadExpenseData(1)">First</button>
        <button onclick="loadExpenseData(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button onclick="loadExpenseData(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
        <button onclick="loadExpenseData(${totalPages})">Last</button>
    `;
}

function updateBudgetPagination(currentPage, totalPages) {
    const paginationControls = document.getElementById("budget-pagination-controls");
    paginationControls.innerHTML = `
        <button onclick="loadBudgetData(1)">First</button>
        <button onclick="loadBudgetData(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button onclick="loadBudgetData(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
        <button onclick="loadBudgetData(${totalPages})">Last</button>
    `;
}

function displayExpenses(expenses) {
    const tableBody = document.getElementById('expense-table-body');
    tableBody.innerHTML = '';
    
    if (expenses.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="6" class="empty-table-message">No expenses found</td>`;
        tableBody.appendChild(row);
        return;
    }
    
    expenses.forEach(expense => {
        const row = document.createElement('tr');
        
        // Format the date
        const expenseDate = new Date(expense.date);
        const formattedDate = expenseDate.toLocaleDateString();
        
        // Create file link if available
        let fileLink = 'No file';
        if (expense.image_url) {
            fileLink = getFileLink(expense.image_url, expense.file_type);
        }
        
        row.innerHTML = `
            <td>${expense.name}</td>
            <td>${formattedDate}</td>
            <td>${expense.category}</td>
            <td>${expense.description || 'N/A'}</td>
            <td>₹${parseFloat(expense.amount).toFixed(2)}</td>
            <td>${fileLink}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Add this function to handle file links
function getFileLink(url, fileType) {
    const imageTypes = ["image/jpeg", "image/png"];
    if (imageTypes.includes(fileType)) {
        return `<a href="#" onclick="showImagePopup('${url}'); return false;">🖼️</a>`;
    } else {
        return `<a href="${url}" target="_blank">📄</a>`;
    }
}

// Fetch and display budgets

const API_URL = window.location.origin;

// Update budget loading to match script.js pattern
function loadBudgetData() {
    fetch(`${API_URL}/get_budgets`, { 
        credentials: 'include',
        headers: {'Cache-Control': 'no-cache'} // Match script.js cache handling
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        // Handle empty state first like script.js does
        if (data && data.length > 0) {
            displayBudgets(data);
        } else {
            displayBudgets([]); // Explicit empty array handling
        }
    })
    .catch(error => {
        console.error('Error fetching budget data:', error);
        const tableBody = document.getElementById('budget-table-body');
        tableBody.innerHTML = `<tr><td colspan="5" class="empty-table-message">No budgets configured</td></tr>`;
    });
}

function displayBudgets(budgets) {
    const tableBody = document.getElementById('budget-table-body');
    tableBody.innerHTML = '';
    
    if (!budgets || budgets.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-table-message">
                    No budgets found. <a href="/dashboard_edit" class="link">Create one?</a>
                </td>
            </tr>
        `;
        return;
    }

    const monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"];

    budgets.forEach(budget => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${budget.year}</td>
            <td>${monthNames[budget.month - 1]}</td>
            <td>${budget.category}</td> <!-- Must match backend response field name -->
            <td>₹${parseFloat(budget.amount).toFixed(2)}</td>
            <td>${budget.recurring ? 'Yes' : 'No'}</td>
        `;
        tableBody.appendChild(row);
    });
}

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

fetchStats();

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
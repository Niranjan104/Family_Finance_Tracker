document.addEventListener('DOMContentLoaded', function() {
    // Initialize date filters with current month
    initializeDateFilters();
    
    // Load initial data
    loadExpenseData();
    loadBudgetData();
    loadDashboardStats();
    
    // Set up event listeners
    document.getElementById('filter-btn').addEventListener('click', function() {
        loadExpenseData();
        loadBudgetData();  // Add budget reload
        loadDashboardStats();
    });
    
    document.getElementById('refresh-btn').addEventListener('click', function() {
        document.getElementById('from-date').value = '';
        document.getElementById('to-date').value = '';
        loadExpenseData();
        loadBudgetData();  // Add budget reload
        loadDashboardStats();
    });
});

function initializeDateFilters() {
    // Set default date range to last 7 days
    const today = new Date();
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(today.getDate() - 7);
    
    const fromDateInput = document.getElementById('from-date');
    const toDateInput = document.getElementById('to-date');
    
    fromDateInput.valueAsDate = sevenDaysAgo;
    toDateInput.valueAsDate = today;
}

// Add this function to handle dashboard stats
function loadDashboardStats() {
    fetch(`${API_URL}/get_stats`, { credentials: 'include' })
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            // Update your stats DOM elements here
            console.log('Dashboard stats loaded:', data);
        })
        .catch(error => console.error('Error loading stats:', error));
}

// Update all fetch calls to include credentials
function loadExpenseData() {
    const fromDate = document.getElementById('from-date').value;
    const toDate = document.getElementById('to-date').value;
    
    fetch(`${API_URL}/get_expenses?from_date=${fromDate}&to_date=${toDate}`, { 
        credentials: 'include' 
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            displayExpenses(data);
        })
        .catch(error => {
            console.error('Error fetching expense data:', error);
            // Show error message in the table
            const tableBody = document.getElementById('expense-table-body');
            tableBody.innerHTML = `<tr><td colspan="6" class="empty-table-message">Failed to load expenses. Please try again later.</td></tr>`;
        });
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
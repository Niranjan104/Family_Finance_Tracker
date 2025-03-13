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
    // Set default date range to current month
    const today = new Date();
    const firstDay = new Date(today.getFullYear(), today.getMonth(), 1);
    
    const fromDateInput = document.getElementById('from-date');
    const toDateInput = document.getElementById('to-date');
    
    fromDateInput.valueAsDate = firstDay;
    toDateInput.valueAsDate = today;
}

function loadExpenseData() {
    const fromDate = document.getElementById('from-date').value;
    const toDate = document.getElementById('to-date').value;
    
    // Use the existing get_expenses endpoint
    fetch(`/get_expenses?from_date=${fromDate}&to_date=${toDate}`)
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
            fileLink = `<a href="${expense.image_url}" target="_blank">View File</a>`;
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

// Fetch and display budgets

function loadBudgetData() {
    fetch('/get_budgets')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => displayBudgets(data))
        .catch(error => {
            console.error('Error fetching budget data:', error);
            const tableBody = document.getElementById('budget-table-body');
            tableBody.innerHTML = `<tr><td colspan="5" class="empty-table-message">Failed to load budgets. Please try again later.</td></tr>`;
        });
}

function displayBudgets(budgets) {
    const tableBody = document.getElementById('budget-table-body');
    tableBody.innerHTML = '';
    
    if (budgets.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="5" class="empty-table-message">No budgets found</td>`;
        tableBody.appendChild(row);
        return;
    }
    
    const monthNames = ["January", "February", "March", "April", "May", "June",
                      "July", "August", "September", "October", "November", "December"];

    budgets.forEach(budget => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${budget.year}</td>
            <td>${monthNames[budget.month - 1]}</td>
            <td>${budget.category}</td>
            <td>₹${parseFloat(budget.amount).toFixed(2)}</td>
            <td>${budget.recurring ? 'Yes' : 'No'}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Update event listeners to include budget reloading

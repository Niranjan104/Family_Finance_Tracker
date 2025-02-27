const API_URL = window.location.origin;

// Default categories
const DEFAULT_CATEGORIES = [
  "Food🍕",
  "Transport🚂 ",
  "Bills💸",
  "Entertainment🤡",
  "Shopping🛍️",
  "Therapy 🩺",
  "Others"
];

// Random messages
const messages = [
  "💸 Counting your regrets… I mean, transactions… 💸",
  "🏦 Asking your bank if it’s okay to proceed… 📞",
  "🎢 Analyzing your financial rollercoaster… 📊",
  "🛍️ Rethinking that last online shopping spree… 🤔",
  "🛒 Compiling all your 'just one more' purchases… 💳",
  "💳 Checking if your card is still breathing… 🚑",
  "🍕 Calculating how much of your salary went to food… 😋",
  "🎰 Spinning the wheel of 'Do I have enough money?' 🤞",
  "🏖️ Searching for your retirement fund… Found: 404 🔎",
  "🏃‍♂️ Watching your money run faster than you… 💨",
  "📅 Estimating how long until payday saves you… ⏳",
  "🔎 Looking for savings… Please wait… 🧐",
  "💰 Your money was here… and now it’s gone! 💨",
  "🚀 Sending a rescue mission for your budget… 🆘",
  "🤷‍♂️ Trying to explain your expenses to your future self… 😬"
];

// Show a random message in #message every 3 seconds
function displayRandomMessage() {
  const messageContainer = document.getElementById("message");
  const randomMessage = messages[Math.floor(Math.random() * messages.length)];
  messageContainer.textContent = randomMessage;
}
setInterval(displayRandomMessage, 3000);

// Strip emojis from category text
function stripEmojis(text) {
  return text
    .replace(/[\u{1F600}-\u{1F64F}]/gu, '')
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

// Fetch categories and populate dropdown
async function fetchCategories() {
  let select = document.getElementById("category");
  select.innerHTML = '<option value="">Select</option>';
  // Add default categories
  DEFAULT_CATEGORIES.forEach(cat => {
    let option = document.createElement("option");
    option.value = cat; // Keep emojis for display
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

// Update file upload label with file name
document.getElementById("file-upload").addEventListener("change", function() {
  const fileName = this.files[0] ? this.files[0].name : "Upload File";
  document.getElementById("file-upload-label").textContent = fileName;
});

// Fetch expenses
async function fetchExpenses(fromDate = "", toDate = "") {
  let url = `${API_URL}/get_expenses`;
  if (fromDate && toDate) {
    url += `?from_date=${fromDate}&to_date=${toDate}`;
  }
  // Example: you would fetch from your real backend
  // let response = await fetch(url);
  // let expenses = await response.json();

  // For demonstration, let's mock some data:
  let expenses = [
    {
      id: 1,
      name: "Pizza",
      date: "2025-02-01",
      category: "Food🍕",
      description: "Dinner with friends",
      amount: 500,
      image_url: "",
      file_type: ""
    },
    {
      id: 2,
      name: "Bus Fare",
      date: "2025-02-02",
      category: "Transport🚂 ",
      description: "Daily commute",
      amount: 100,
      image_url: "",
      file_type: ""
    }
  ];

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
      <td>${exp.image_url ? getFileLink(exp.image_url, exp.file_type) : "No file"}</td>
    `;
    tableBody.appendChild(row);
  });

  // Update stats based on filtered data
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

// Add / Edit expense
document.getElementById("expense-form").addEventListener("submit", async function(event) {
  event.preventDefault();
  let formData = new FormData(event.target);

  // Handle custom category
  let categorySelect = document.getElementById("category");
  if (categorySelect.value === "Others") {
    let customCategory = document.getElementById("custom-category").value;
    formData.set("category", stripEmojis(customCategory));
  } else {
    formData.set("category", stripEmojis(categorySelect.value));
  }

  let expenseId = document.getElementById("expense-id").value;
  let url = `${API_URL}/add_expense`;
  let method = "POST";

  if (expenseId) {
    url = `${API_URL}/edit_expense/${expenseId}`;
    method = "PUT";
  }

  // Example: you'd send this to your real backend
  // let response = await fetch(url, { method, body: formData });
  // let result = await response.json();

  // Refresh expense list & stats
  fetchExpenses();
  fetchStats();

  // Reset form
  event.target.reset();
  document.getElementById("custom-category-label").style.display = "none";
  document.getElementById("expense-id").value = "";
  document.getElementById("file-upload-label").textContent = "Upload File📤";
});

// Edit expense (prefill form)
async function editExpense(id) {
  // Example fetch from backend
  // let response = await fetch(`${API_URL}/get_expense/${id}`);
  // let expense = await response.json();

  // Mock data
  let expense = {
    id: id,
    name: "Mocked Expense",
    category: "Others",
    category_desc: "Some description",
    date: "2025-02-05",
    amount: 999,
    description: "Mocked details"
  };

  document.getElementById("expense-id").value = expense.id;
  document.getElementById("name").value = expense.name;
  document.getElementById("category").value = expense.category;
  document.getElementById("category-desc").value = expense.category_desc;
  document.getElementById("date").value = expense.date;
  document.getElementById("amount").value = expense.amount;
  document.getElementById("description").value = expense.description;
  document.getElementById("file-upload").value = "";

  // Show custom category input if "Others" or custom
  if (expense.category === "Others" || !DEFAULT_CATEGORIES.includes(expense.category)) {
    document.getElementById("custom-category-label").style.display = "block";
    document.getElementById("custom-category").value = expense.category;
    document.getElementById("category").value = "Others";
  } else {
    document.getElementById("custom-category-label").style.display = "none";
  }

  document.getElementById("expense-form").scrollIntoView({ behavior: "smooth" });
}

// Delete expense
async function deleteExpense(id) {
  if (!confirm("😃Sure you want to Delete?")) return;

  // Example: you'd call your real backend
  // await fetch(`${API_URL}/delete_expense/${id}`, { method: "DELETE" });

  // Refresh
  fetchExpenses();
  setTimeout(fetchStats, 500);
}

// Filter by date
document.getElementById("filter-btn").addEventListener("click", function() {
  const fromDate = document.getElementById("from-date").value;
  const toDate = document.getElementById("to-date").value;
  if (!fromDate || !toDate) {
    const alertBox = document.createElement("div");
    alertBox.textContent = "😯Please fill out both date fields😅";
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

    setTimeout(() => {
      document.body.removeChild(alertBox);
    }, 2000);
    return;
  }
  fetchExpenses(fromDate, toDate);
});

// Refresh the filter
document.getElementById("refresh-btn").addEventListener("click", function() {
  document.getElementById("from-date").value = "";
  document.getElementById("to-date").value = "";
  fetchExpenses();
  fetchStats();
});

// Fetch stats
async function fetchStats() {
  // Example: you'd fetch real stats from your backend
  // let response = await fetch(`${API_URL}/get_stats`);
  // let stats = await response.json();

  // Mock stats
  let stats = {
    total_spent: 600,
    expense_count: 2,
    last_7days_spent: 200,
    highest_category: "Food",
    highest_amount: 500
  };

  document.getElementById("total-spent-value").textContent = stats.total_spent.toFixed(2);
  document.getElementById("expense-count-value").textContent = stats.expense_count;
  document.getElementById("last-7days-spent-value").textContent = stats.last_7days_spent.toFixed(2);
  document.getElementById("highest-category-value").textContent = stats.highest_category;
  document.getElementById("highest-amount-value").textContent = stats.highest_amount.toFixed(2);
}

// Update stats (with optional date range)
async function updateStats(fromDate, toDate) {
  // If you need filtered stats, pass fromDate/toDate to your backend
  fetchStats(); // Using the mock approach for demonstration
}

// Initialize
async function init() {
  await fetchCategories();
  fetchExpenses();
  fetchStats();

  // Check for saved dark mode preference
  const darkMode = localStorage.getItem("darkMode");
  if (darkMode === "enabled") {
    document.body.classList.add("dark-mode");
  }
}
init();

// Toggle dark mode
document.getElementById("dark-mode-toggle").addEventListener("click", function() {
  document.body.classList.toggle("dark-mode");
  const isDarkMode = document.body.classList.contains("dark-mode");
  localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled");
});

// -------------------------------------------
//      MONTH-YEAR + BUDGET FORM LOGIC
// -------------------------------------------

// Populate the year dropdown (example: currentYear to currentYear+10)
function populateYears() {
  const yearSelect = document.getElementById('year-select');
  const currentYear = new Date().getFullYear();
  for (let i = currentYear; i <= currentYear + 10; i++) {
    const option = document.createElement('option');
    option.value = i;
    option.textContent = i;
    yearSelect.appendChild(option);
  }
}

// Initialize the Month/Year form
document.addEventListener('DOMContentLoaded', function () {
  populateYears();

  // Load previous selection (if any)
  const storedYear = localStorage.getItem('selectedYear');
  const storedMonth = localStorage.getItem('selectedMonth');
  if (storedYear && storedMonth) {
    document.getElementById('year-select').value = storedYear;
    document.getElementById('month-select').value = storedMonth;
  }
});

document.getElementById('month-year-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const year = document.getElementById('year-select').value;
  const month = document.getElementById('month-select').value;
  const prompt = document.getElementById('month-year-prompt');

  if (!year || !month) {
    alert('Please select both year and month');
    return;
  }

  // Check if same as previous selection
  const lastSelected = localStorage.getItem('selectedPeriod');
  if (lastSelected === `${year}-${month}`) {
    prompt.style.display = 'block';
    setTimeout(() => {
      prompt.style.display = 'none';
    }, 3000);
    return;
  }

  // Store selection
  localStorage.setItem('selectedPeriod', `${year}-${month}`);
  localStorage.setItem('selectedYear', year);
  localStorage.setItem('selectedMonth', month);

  // Show the new Category & Amount form on the right side
  document.getElementById('budget-form-container').style.display = 'block';
});

// Handle the new Budget Category form submission
document.getElementById('budget-category-form').addEventListener('submit', function(e) {
  e.preventDefault();
  const category = document.getElementById('budget-category').value;
  const amount = document.getElementById('budget-amount').value;

  // Example: Save to localStorage or send to your backend
  console.log('Budget category:', category);
  console.log('Budget amount:', amount);

  alert(`Budget saved for ${category}: ₹${amount}`);
  // Optionally reset form
  // e.target.reset();
});
const savingsCategories = ["Education", "Health", "Travel", "Food", "Entertainment", "Others"];
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

document.addEventListener("DOMContentLoaded", function() {
    const categorySelect = document.getElementById("saving_category_name");
    savingsCategories.forEach(category => {
        const option = document.createElement("option");
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });
    displayRandomMessage(); // Display a random message when the page loads
    setInterval(displayRandomMessage, 2000); // Change the message every 2 seconds
    loadDarkModePreference(); // Load dark mode preference on page load
});

document.getElementById("savingTargetForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const id = document.getElementById("savingTargetForm").dataset.id;
    const category = document.getElementById("saving_category_name").value;
    const data = {
        saving_category_name: category,
        saving_category_description: document.getElementById("saving_category_description").value,
        savings_goal_name: document.getElementById("savings_goal_name").value,
        savings_target_amount: document.getElementById("savings_target_amount").value,
        savings_target_date: document.getElementById("savings_target_date").value
    };
    const url = id ? `/update_saving_target/${id}` : '/add_saving_target';
    const method = id ? "PUT" : "POST";
    fetch(url, { method: method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(response => response.json())
        .then(response => {
            loadData();
            closeForm('savingTargetForm');
            showMessage(response.message);
        });
});

document.getElementById("savingsForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const data = {
        savings_target_id: document.getElementById("savings_target_id").value,
        savings_goal_name: document.getElementById("savings_goal_name").value,
        savings_amount_saved: document.getElementById("savings_amount_saved").value,
        savings_payment_mode: document.getElementById("savings_payment_mode").value,
        savings_date_saved: document.getElementById("savings_date_saved").value
    };
    fetch('/add_savings', { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(response => response.json())
        .then(response => {
            loadData();
            closeForm('savingsForm');
            showMessage(response.message);
        });
});

function loadData() {
    fetch('/get_all_data')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("savingsTable").querySelector("tbody");
            tbody.innerHTML = "";
            data.forEach(item => {
                let remainingAmount;
                if (item.savings_amount_saved >= item.savings_target_amount) {
                    remainingAmount = item.savings_amount_saved == item.savings_target_amount ? "Reached" : "Exceeded";
                } else {
                    remainingAmount = item.savings_target_amount - item.savings_amount_saved;
                }
                const row = document.createElement("tr");
                row.setAttribute("data-id", item.savings_target_id);
                row.innerHTML = `
                    <td>${item.saving_category_name || ''}</td>
                    <td>${item.savings_goal_name || ''}</td>
                    <td>${item.savings_target_amount || ''}</td>
                    <td>${item.savings_target_date || ''}</td>
                    <td>${item.savings_amount_saved || ''}</td>
                    <td>${remainingAmount}</td>
                    <td>${item.savings_payment_mode || ''}</td>
                    <td>
                        <button class="edit" onclick="editTarget(${item.savings_target_id})">✏️</button>
                        <button class="delete" onclick="deleteTarget(${item.savings_target_id})">❌</button>
                    </td>
                    <td>
                        <button class="update" onclick="updateSavings(${item.savings_target_id})">Update</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        });
}

function editTarget(id) {
    fetch(`/get_savings/${id}`)
        .then(response => response.json())
        .then(data => {
            const target = data.savings;
            document.getElementById("saving_category_name").value = target.saving_category_name;
            document.getElementById("saving_category_description").value = target.saving_category_description;
            document.getElementById("savings_goal_name").value = target.savings_goal_name;
            document.getElementById("savings_target_amount").value = target.savings_target_amount;
            document.getElementById("savings_target_date").value = target.savings_target_date;
            document.getElementById("savingTargetForm").dataset.id = id;
            showForm('savingTargetForm');
        });
}

function deleteTarget(id) {
    if (confirm("Are you sure you want to delete this saving target?")) {
        fetch(`/delete_saving_target/${id}`, { method: "DELETE" })
            .then(response => response.json())
            .then(response => {
                loadData();
                showMessage(response.message);
            });
    }
}

function deleteSavings(id) {
    fetch(`/delete_savings/${id}`, { method: "DELETE" })
        .then(response => response.json())
        .then(() => loadData());
}

function updateSavings(id) {
    const target = document.querySelector(`tr[data-id='${id}']`);
    fetch(`/get_savings/${id}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("savings_target_id").value = id;
            if (data.savings) {
                document.getElementById("savings_amount_saved").value = data.savings.savings_amount_saved;
                document.getElementById("savings_payment_mode").value = data.savings.savings_payment_mode;
                document.getElementById("savings_date_saved").value = data.savings.savings_date_saved;
            } else {
                document.getElementById("savings_amount_saved").value = '';
                document.getElementById("savings_payment_mode").value = '';
                document.getElementById("savings_date_saved").value = '';
            }
            showForm('savingsForm');
        });
}

function showForm(formId) {
    // Hide all forms and reset them
    document.querySelectorAll('.form-popup').forEach(form => {
        form.style.display = 'none';
    });
    // Show the selected form
    document.getElementById(formId).style.display = 'block';
    // Show the backdrop
    document.getElementById('backdrop').style.display = 'block';
}

function closeForm(formId) {
    document.getElementById(formId).style.display = 'none';
    // Hide the backdrop
    document.getElementById('backdrop').style.display = 'none';
    // Clear form data
    const form = document.getElementById(formId).querySelector('.form-container');
    form.reset();
    if (formId === 'savingTargetForm') {
        document.getElementById("savingTargetForm").dataset.id = '';
    }
}

function showMessage(message) {
    alert(message);
}

function displayRandomMessage() {
    const messageContainer = document.getElementById("message");
    const randomMessage = messages[Math.floor(Math.random() * messages.length)];
    messageContainer.textContent = randomMessage;
    messageContainer.style.textAlign = "center"; // Ensure the message is displayed in the center
}

function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");
    document.querySelector("header").classList.toggle("dark-mode");
    document.querySelectorAll("nav button").forEach(button => button.classList.toggle("dark-mode"));
    document.querySelector(".table-list").classList.toggle("dark-mode");
    document.querySelectorAll("table").forEach(table => table.classList.toggle("dark-mode"));
    document.querySelectorAll(".form-popup").forEach(form => form.classList.toggle("dark-mode"));
    document.querySelectorAll(".close-btn").forEach(button => button.classList.toggle("dark-mode"));
    document.querySelectorAll("form button").forEach(button => button.classList.toggle("dark-mode"));
    saveDarkModePreference();
}

function saveDarkModePreference() {
    const isDarkMode = document.body.classList.contains("dark-mode");
    localStorage.setItem("darkMode", isDarkMode ? "enabled" : "disabled");
}

function loadDarkModePreference() {
    const darkMode = localStorage.getItem("darkMode");
    if (darkMode === "enabled") {
        toggleDarkMode();
    }
}

loadData();

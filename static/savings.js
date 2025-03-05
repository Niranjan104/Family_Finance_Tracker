document.getElementById("savingTargetForm").addEventListener("submit", function(e) {
    e.preventDefault();
    const data = {
        saving_category_name: document.getElementById("saving_category_name").value,
        saving_category_description: document.getElementById("saving_category_description").value,
        savings_goal_name: document.getElementById("savings_goal_name").value,
        savings_target_amount: document.getElementById("savings_target_amount").value,
        savings_target_date: document.getElementById("savings_target_date").value
    };
    fetch('/add_saving_target', { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) })
        .then(response => response.json())
        .then(() => location.reload());
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
        .then(() => location.reload());
});

function loadData() {
    fetch('/get_all_data')
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById("savingsTable").querySelector("tbody");
            tbody.innerHTML = "";
            data.forEach(item => {
                const row = document.createElement("tr");
                row.setAttribute("data-id", item.savings_target_id);
                row.innerHTML = `
                    <td>${item.saving_category_name || ''}</td>
                    <td>${item.saving_category_description || ''}</td>
                    <td>${item.savings_goal_name || ''}</td>
                    <td>${item.savings_target_amount || ''}</td>
                    <td>${item.savings_target_date || ''}</td>
                    <td>${item.savings_amount_saved || ''}</td>
                    <td>${item.savings_payment_mode || ''}</td>
                    <td>${item.savings_date_saved || ''}</td>
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
    const target = document.querySelector(`tr[data-id='${id}']`);
    document.getElementById("saving_category_name").value = target.querySelector("td:nth-child(1)").innerText;
    document.getElementById("saving_category_description").value = target.querySelector("td:nth-child(2)").innerText;
    document.getElementById("savings_goal_name").value = target.querySelector("td:nth-child(3)").innerText;
    document.getElementById("savings_target_amount").value = target.querySelector("td:nth-child(4)").innerText;
    document.getElementById("savings_target_date").value = target.querySelector("td:nth-child(5)").innerText;
    document.getElementById("savingTargetForm").dataset.id = id;
    showForm('savingTargetForm');
}

function deleteTarget(id) {
    fetch(`/delete_saving_target/${id}`, { method: "DELETE" })
        .then(response => response.json())
        .then(() => location.reload());
}

function deleteSavings(id) {
    fetch(`/delete_savings/${id}`, { method: "DELETE" })
        .then(response => response.json())
        .then(() => location.reload());
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
    document.getElementById(formId).style.display = 'block';
}

function closeForm(formId) {
    document.getElementById(formId).style.display = 'none';
}


loadData();

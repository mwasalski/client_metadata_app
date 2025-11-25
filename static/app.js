const apiBase = "/api/clients";

const form = document.getElementById("clientForm");
const submitBtn = document.getElementById("submitBtn");
const cancelBtn = document.getElementById("cancelBtn");
const listEl = document.getElementById("clientsList");
const emptyState = document.getElementById("emptyState");
const searchInput = document.getElementById("search");
const statusFilter = document.getElementById("statusFilter");
const resetBtn = document.getElementById("resetDbBtn");
const exportBtn = document.getElementById("exportBtn");

let clients = [];
let editingId = null;

const statusLabels = {
  prospect: "Prospect",
  active: "Active Discussion",
  closed: "Closed Won",
  churn_risk: "At Risk",
};

function escapeHtml(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function fetchClients() {
  const res = await fetch(apiBase);
  clients = await res.json();
  renderClients();
}

function renderClients() {
  const term = searchInput.value.trim().toLowerCase();
  const status = statusFilter.value;

  const filtered = clients.filter((c) => {
    const matchesStatus = !status || c.status === status;
    const matchesTerm =
      !term ||
      c.full_name.toLowerCase().includes(term) ||
      (c.company || "").toLowerCase().includes(term);
    return matchesStatus && matchesTerm;
  });

  emptyState.style.display = filtered.length ? "none" : "block";

  listEl.innerHTML = filtered
    .map((client) => {
      const metaParts = [
        client.company || null,
        client.email || null,
        client.phone || null,
      ].filter(Boolean);

      const go = client.go_factors
        ? `<div class="badge go"><strong>Green Lights</strong>${escapeHtml(client.go_factors)}</div>`
        : `<div class="badge go" style="opacity:0.5"><strong>Green Lights</strong>—</div>`;

      const noGo = client.no_go_factors
        ? `<div class="badge no-go"><strong>Red Flags</strong>${escapeHtml(client.no_go_factors)}</div>`
        : `<div class="badge no-go" style="opacity:0.5"><strong>Red Flags</strong>—</div>`;

      const notes = client.notes
        ? `<div class="notes">${escapeHtml(client.notes)}</div>`
        : ``;

      return `
        <article class="card" data-id="${client.id}">
          <div class="card-header">
            <div>
              <div class="client-name">${escapeHtml(client.full_name)}</div>
              <div class="meta">${metaParts.length ? escapeHtml(metaParts.join(" · ")) : ""}</div>
            </div>
            <div class="status ${client.status}">${statusLabels[client.status] || client.status}</div>
          </div>
          <div class="badges">
            ${go}
            ${noGo}
          </div>
          ${notes}
          <div class="card-actions">
            <button class="ghost" data-action="edit">Edit Details</button>
            <button class="ghost" data-action="delete" style="color: var(--danger);">Delete</button>
          </div>
        </article>
      `;
    })
    .join("");
}

function setFormMode(mode) {
  if (mode === "edit") {
    submitBtn.textContent = "Update Client";
    cancelBtn.style.display = "inline-flex";
  } else {
    submitBtn.textContent = "Save Client";
    cancelBtn.style.display = "none";
    editingId = null;
  }
}

function clearForm() {
  form.reset();
  document.getElementById("status").value = "prospect";
}

function fillForm(client) {
  form.full_name.value = client.full_name || "";
  form.company.value = client.company || "";
  form.email.value = client.email || "";
  form.phone.value = client.phone || "";
  form.status.value = client.status || "prospect";
  form.go_factors.value = client.go_factors || "";
  form.no_go_factors.value = client.no_go_factors || "";
  form.notes.value = client.notes || "";
}

async function saveClient(e) {
  e.preventDefault();
  const payload = {
    full_name: form.full_name.value,
    company: form.company.value,
    email: form.email.value,
    phone: form.phone.value,
    status: form.status.value,
    go_factors: form.go_factors.value,
    no_go_factors: form.no_go_factors.value,
    notes: form.notes.value,
  };

  try {
    const res = await fetch(
      editingId ? `${apiBase}/${editingId}` : apiBase,
      {
        method: editingId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );

    if (!res.ok) {
      const data = await res.json();
      alert(data.errors ? data.errors.join("\n") : "Something went wrong.");
      return;
    }

    clearForm();
    setFormMode("create");
    await fetchClients();
  } catch (err) {
    console.error(err);
    alert("Could not save client. Check your connection and try again.");
  }
}

function handleListClick(e) {
  const card = e.target.closest(".card");
  if (!card) return;
  const id = Number(card.dataset.id);
  if (Number.isNaN(id)) return;

  if (e.target.dataset.action === "edit") {
    const client = clients.find((c) => c.id === id);
    if (!client) return;
    editingId = id;
    fillForm(client);
    setFormMode("edit");
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else if (e.target.dataset.action === "delete") {
    deleteClient(id);
  }
}

async function deleteClient(id) {
  const confirmed = confirm("Delete this client? This cannot be undone.");
  if (!confirmed) return;
  try {
    const res = await fetch(`${apiBase}/${id}`, { method: "DELETE" });
    if (!res.ok) {
      alert("Could not delete client.");
      return;
    }
    if (editingId === id) {
      clearForm();
      setFormMode("create");
    }
    await fetchClients();
  } catch (err) {
    console.error(err);
    alert("Could not delete client. Try again.");
  }
}

async function resetDatabase() {
  const confirmed = confirm(
    "Are you sure you want to reset all data? This will delete every client record permanently."
  );
  if (!confirmed) return;
  try {
    const res = await fetch("/api/reset-db", { method: "POST" });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      alert(data.error || "Could not reset database.");
      return;
    }
    clearForm();
    setFormMode("create");
    await fetchClients();
    alert("All data has been reset. You can start fresh.");
  } catch (err) {
    console.error(err);
    alert("Could not reset database. Try again.");
  }
}

cancelBtn.addEventListener("click", () => {
  clearForm();
  setFormMode("create");
});

form.addEventListener("submit", saveClient);
listEl.addEventListener("click", handleListClick);
searchInput.addEventListener("input", renderClients);
statusFilter.addEventListener("change", renderClients);
resetBtn.addEventListener("click", resetDatabase);
exportBtn.addEventListener("click", () => {
  window.location.href = "/api/export-csv";
});

fetchClients();

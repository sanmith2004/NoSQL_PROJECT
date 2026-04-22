/**
 * admin.js — Admin panel: create events, analytics, queue, attendance
 */

const API = "http://localhost:5000";

document.addEventListener("DOMContentLoaded", () => {
  initNotifications();
  loadDashboard();
  loadAnalytics();
  loadAllEvents();
  setupCreateEventForm();
  setupAttributeBuilder();
});

// ── Dashboard Stats ───────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const res = await fetch(`${API}/dashboard`);
    const d = await res.json();
    document.getElementById("stat-events").textContent       = d.total_events;
    document.getElementById("stat-registrations").textContent = d.total_registrations;
    document.getElementById("stat-students").textContent     = d.total_students;

    const typeEl = document.getElementById("stat-types");
    typeEl.innerHTML = Object.entries(d.events_by_type)
      .map(([t, c]) => `<span class="event-type-badge badge-${t}">${t.replace("_"," ")}: ${c}</span>`)
      .join(" ");
  } catch (e) {
    console.error("Dashboard load failed", e);
  }
}

// ── Analytics ─────────────────────────────────────────────────────────────
async function loadAnalytics() {
  try {
    const res = await fetch(`${API}/admin/analytics`);
    const d = await res.json();

    renderTable("tbl-top-events", d.highest_registrations,
      ["title", "type", "registered_count", "max_seats"],
      ["Event", "Type", "Registered", "Max Seats"]);

    renderTable("tbl-dept", d.dept_participation,
      ["department", "total_registrations", "unique_students"],
      ["Department", "Total Registrations", "Unique Students"]);

    renderTable("tbl-active", d.most_active_students,
      ["name", "department", "events_registered", "events_attended"],
      ["Student", "Dept", "Registered", "Attended"]);

    renderTable("tbl-attendance", d.attendance_rate_by_type,
      ["event_type", "total_registrations", "total_attended", "attendance_rate"],
      ["Event Type", "Total", "Attended", "Rate (%)"]);
  } catch (e) {
    console.error("Analytics load failed", e);
  }
}

function renderTable(id, rows, keys, headers) {
  const el = document.getElementById(id);
  if (!el || !rows) return;
  if (!rows.length) { el.innerHTML = "<p style='color:var(--muted)'>No data yet.</p>"; return; }

  const thead = `<tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr>`;
  const tbody = rows.map(r =>
    `<tr>${keys.map(k => `<td>${r[k] ?? "-"}</td>`).join("")}</tr>`
  ).join("");

  el.innerHTML = `<div class="table-wrap"><table><thead>${thead}</thead><tbody>${tbody}</tbody></table></div>`;
}

// ── Event List (admin) ────────────────────────────────────────────────────
async function loadAllEvents() {
  try {
    const res = await fetch(`${API}/events`);
    const events = await res.json();
    const el = document.getElementById("admin-events-list");
    if (!el) return;

    el.innerHTML = events.map(e => `
      <tr>
        <td>${e.title}</td>
        <td><span class="event-type-badge badge-${e.type}">${e.type.replace("_"," ")}</span></td>
        <td>${new Date(e.date).toLocaleDateString("en-IN")}</td>
        <td>${e.registered_count} / ${e.max_seats}</td>
        <td id="seats-admin-${e._id}">Loading...</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="viewQueue('${e._id}','${e.title}')">Queue</button>
        </td>
      </tr>
    `).join("");

    // Load live seats
    for (const e of events) {
      fetch(`${API}/events/${e._id}/seats`)
        .then(r => r.json())
        .then(d => {
          const el2 = document.getElementById(`seats-admin-${e._id}`);
          if (el2) el2.textContent = `${d.available_seats} (${d.source})`;
        }).catch(() => {});
    }
  } catch (e) {
    console.error("Events load failed", e);
  }
}

// ── Queue Viewer ──────────────────────────────────────────────────────────
async function viewQueue(eventId, title) {
  const res = await fetch(`${API}/admin/queue/${eventId}`);
  const d = await res.json();
  const modal = document.getElementById("queue-modal");
  document.getElementById("queue-modal-title").textContent = `Queue: ${title}`;
  document.getElementById("queue-content").innerHTML = `
    <p><strong>Queue length:</strong> ${d.queue_length}</p>
    ${d.queue.length
      ? `<ul style="margin-top:.75rem;padding-left:1.25rem">${d.queue.map(s => `<li>${s}</li>`).join("")}</ul>`
      : "<p style='color:var(--muted)'>Queue is empty.</p>"
    }
    <div style="margin-top:1rem">
      <button class="btn btn-primary btn-sm" onclick="processQueue('${eventId}')">Process Next (LPOP)</button>
    </div>
  `;
  modal.classList.add("open");
}

async function processQueue(eventId) {
  const res = await fetch(`${API}/admin/queue/${eventId}/process`, { method: "POST" });
  const d = await res.json();
  alert(d.processed_student_id
    ? `Processed student: ${d.processed_student_id}`
    : "Queue is empty.");
  closeModal("queue-modal");
}

// ── Create Event Form ─────────────────────────────────────────────────────
let attributeCount = 0;

function setupAttributeBuilder() {
  document.getElementById("add-attr-btn").addEventListener("click", () => {
    attributeCount++;
    const wrap = document.getElementById("attributes-wrap");
    const row = document.createElement("div");
    row.className = "attr-row";
    row.id = `attr-${attributeCount}`;
    row.innerHTML = `
      <input type="text" placeholder="key (e.g. prerequisites)" class="attr-key">
      <input type="text" placeholder="value" class="attr-val">
      <button type="button" class="btn btn-danger btn-sm" onclick="document.getElementById('attr-${attributeCount}').remove()">✕</button>
    `;
    wrap.appendChild(row);
  });
}

function setupCreateEventForm() {
  document.getElementById("create-event-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("create-event-btn");
    btn.disabled = true;
    btn.textContent = "Creating...";

    // Collect attributes
    const attrs = [];
    document.querySelectorAll(".attr-row").forEach(row => {
      const key = row.querySelector(".attr-key").value.trim();
      const val = row.querySelector(".attr-val").value.trim();
      if (key && val) attrs.push({ key, value: val });
    });

    const body = {
      title:      document.getElementById("ev-title").value.trim(),
      type:       document.getElementById("ev-type").value,
      date:       document.getElementById("ev-date").value,
      venue:      document.getElementById("ev-venue").value.trim(),
      max_seats:  parseInt(document.getElementById("ev-seats").value),
      attributes: attrs
    };

    try {
      const res = await fetch(`${API}/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (res.ok) {
        showAdminAlert("success", `✅ Event "${data.title}" created! ID: ${data._id}`);
        document.getElementById("create-event-form").reset();
        document.getElementById("attributes-wrap").innerHTML = "";
        loadDashboard();
        loadAllEvents();
      } else {
        showAdminAlert("error", `❌ ${data.error}`);
      }
    } catch (err) {
      showAdminAlert("error", "Network error.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Create Event";
    }
  });
}

function showAdminAlert(type, msg) {
  const el = document.getElementById("create-alert");
  if (el) {
    el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
    setTimeout(() => el.innerHTML = "", 5000);
  }
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

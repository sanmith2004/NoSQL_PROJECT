/**
 * main.js — Student-facing event listing & registration
 */

const API = "http://localhost:5000";
let allEvents = [];
let activeFilter = "all";
let selectedEventId = null;
let countdownTimers = {};

// ── Boot ──────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initNotifications();
  loadEvents();
  setupFilterButtons();
  setupModal();
  setupCancelModal();
  startSeatRefresh();
});

// ── Load Events ───────────────────────────────────────────────────────────
async function loadEvents() {
  const grid = document.getElementById("events-grid");
  grid.innerHTML = '<div class="spinner"></div>';
  try {
    const res = await fetch(`${API}/events`);
    allEvents = await res.json();
    renderEvents(allEvents);
  } catch (e) {
    grid.innerHTML = '<div class="alert alert-error">Failed to load events. Is the server running?</div>';
  }
}

function renderEvents(events) {
  const grid = document.getElementById("events-grid");
  const filtered = activeFilter === "all" ? events : events.filter(e => e.type === activeFilter);

  if (!filtered.length) {
    grid.innerHTML = '<p style="color:var(--muted)">No events found.</p>';
    return;
  }

  grid.innerHTML = filtered.map(e => eventCardHTML(e)).join("");

  // Start countdown timers
  filtered.forEach(e => {
    if (e.countdown_seconds > 0) startCountdown(e._id, e.countdown_seconds);
  });
}

function eventCardHTML(e) {
  const pct = Math.round((e.available_seats / e.max_seats) * 100);
  const fillClass = pct > 40 ? "fill-ok" : pct > 10 ? "fill-warning" : "fill-danger";
  const isFull = e.available_seats <= 0;
  const dateStr = new Date(e.date).toLocaleDateString("en-IN", { day:"numeric", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" });

  const attrs = (e.attributes || []).slice(0, 3).map(a =>
    `<li><strong>${a.key}:</strong> ${a.value}</li>`
  ).join("");

  return `
  <div class="event-card" id="card-${e._id}" data-type="${e.type}">
    <div class="event-card-header">
      <span class="event-type-badge badge-${e.type}">${e.type.replace("_"," ")}</span>
      <div class="event-title">${e.title}</div>
      <div class="event-meta">
        <span>📅 ${dateStr}</span>
        <span>📍 ${e.venue}</span>
      </div>
    </div>
    <div class="event-card-body">
      <div class="seats-bar-wrap">
        <div class="seats-label">
          <span>Seats Available</span>
          <span class="seats-count" id="seats-${e._id}">${e.available_seats} / ${e.max_seats}</span>
        </div>
        <div class="seats-bar">
          <div class="seats-bar-fill ${fillClass}" id="bar-${e._id}" style="width:${pct}%"></div>
        </div>
      </div>
      <div class="countdown" id="cd-${e._id}">
        ${e.countdown_seconds > 0 ? "⏳ " + formatCountdown(e.countdown_seconds) : "🔴 Event started"}
      </div>
      <ul class="attributes-list">${attrs}</ul>
    </div>
    <div class="event-card-footer">
      <button class="btn btn-primary btn-sm" onclick="openRegModal('${e._id}','${e.title}')"
        ${isFull ? "disabled" : ""}>
        ${isFull ? "Full" : "Register"}
      </button>
      <button class="btn btn-outline btn-sm" onclick="openCancelModal('${e._id}','${e.title}')">Cancel</button>
      <a href="/event/${e._id}" class="btn btn-ghost btn-sm">Details →</a>
    </div>
  </div>`;
}

// ── Filter Buttons ────────────────────────────────────────────────────────
function setupFilterButtons() {
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      activeFilter = btn.dataset.type;
      renderEvents(allEvents);
    });
  });
}

// ── Registration Modal ────────────────────────────────────────────────────
function setupModal() {
  document.getElementById("reg-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("reg-submit-btn");
    btn.disabled = true;
    btn.textContent = "Registering...";

    const body = {
      name:       document.getElementById("reg-name").value.trim(),
      email:      document.getElementById("reg-email").value.trim(),
      department: document.getElementById("reg-dept").value.trim()
    };

    try {
      const res = await fetch(`${API}/events/${selectedEventId}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (res.ok) {
        showAlert("reg-alert", "success", `✅ Registered successfully! Seats left: ${data.available_seats ?? "N/A"}`);
        updateSeatsUI(selectedEventId, data.available_seats);
        setTimeout(() => closeModal("reg-modal"), 2000);
      } else {
        showAlert("reg-alert", "error", `❌ ${data.error}`);
      }
    } catch (err) {
      showAlert("reg-alert", "error", "Network error. Please try again.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Register";
    }
  });
}

function openRegModal(eventId, title) {
  selectedEventId = eventId;
  document.getElementById("reg-modal-title").textContent = `Register: ${title}`;
  document.getElementById("reg-alert").innerHTML = "";
  document.getElementById("reg-form").reset();
  document.getElementById("reg-modal").classList.add("open");
}

// ── Cancel Modal ──────────────────────────────────────────────────────────
function setupCancelModal() {
  document.getElementById("cancel-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("cancel-submit-btn");
    btn.disabled = true;
    btn.textContent = "Cancelling...";

    const email = document.getElementById("cancel-email").value.trim();
    try {
      const res = await fetch(`${API}/events/${selectedEventId}/register`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok) {
        showAlert("cancel-alert", "success", `✅ Cancelled. Seats now: ${data.available_seats ?? "N/A"}`);
        updateSeatsUI(selectedEventId, data.available_seats);
        setTimeout(() => closeModal("cancel-modal"), 2000);
      } else {
        showAlert("cancel-alert", "error", `❌ ${data.error}`);
      }
    } catch (err) {
      showAlert("cancel-alert", "error", "Network error.");
    } finally {
      btn.disabled = false;
      btn.textContent = "Cancel Registration";
    }
  });
}

function openCancelModal(eventId, title) {
  selectedEventId = eventId;
  document.getElementById("cancel-modal-title").textContent = `Cancel: ${title}`;
  document.getElementById("cancel-alert").innerHTML = "";
  document.getElementById("cancel-form").reset();
  document.getElementById("cancel-modal").classList.add("open");
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

// ── Live Seat Refresh ─────────────────────────────────────────────────────
function startSeatRefresh() {
  setInterval(async () => {
    for (const e of allEvents) {
      try {
        const res = await fetch(`${API}/events/${e._id}/seats`);
        if (res.ok) {
          const d = await res.json();
          updateSeatsUI(e._id, d.available_seats, e.max_seats);
        }
      } catch (_) {}
    }
  }, 10000); // every 10 seconds
}

function updateSeatsUI(eventId, available, maxSeats) {
  const seatsEl = document.getElementById(`seats-${eventId}`);
  const barEl   = document.getElementById(`bar-${eventId}`);
  const cardEl  = document.getElementById(`card-${eventId}`);
  if (!seatsEl) return;

  const event = allEvents.find(e => e._id === eventId);
  const max = maxSeats || (event ? event.max_seats : 1);
  const avail = available ?? 0;

  seatsEl.textContent = `${avail} / ${max}`;

  if (barEl) {
    const pct = Math.round((avail / max) * 100);
    barEl.style.width = pct + "%";
    barEl.className = `seats-bar-fill ${pct > 40 ? "fill-ok" : pct > 10 ? "fill-warning" : "fill-danger"}`;
  }

  // Disable register button if full
  if (cardEl) {
    const regBtn = cardEl.querySelector(".btn-primary");
    if (regBtn) {
      regBtn.disabled = avail <= 0;
      regBtn.textContent = avail <= 0 ? "Full" : "Register";
    }
  }
}

// ── Countdown Timers ──────────────────────────────────────────────────────
function startCountdown(eventId, seconds) {
  if (countdownTimers[eventId]) clearInterval(countdownTimers[eventId]);
  let remaining = seconds;
  const el = document.getElementById(`cd-${eventId}`);
  if (!el) return;

  countdownTimers[eventId] = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      el.textContent = "🔴 Event started";
      clearInterval(countdownTimers[eventId]);
    } else {
      el.textContent = "⏳ " + formatCountdown(remaining);
    }
  }, 1000);
}

function formatCountdown(s) {
  const d = Math.floor(s / 86400);
  const h = Math.floor((s % 86400) / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  const parts = [];
  if (d) parts.push(`${d}d`);
  if (h) parts.push(`${h}h`);
  if (m) parts.push(`${m}m`);
  parts.push(`${sec}s`);
  return parts.join(" ");
}

// ── Helpers ───────────────────────────────────────────────────────────────
function showAlert(id, type, msg) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
}

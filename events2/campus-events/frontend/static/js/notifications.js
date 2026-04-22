/**
 * notifications.js — SSE-based real-time notification panel
 */

const API_BASE = "http://localhost:5000";

let notifPanel = null;

function initNotifications() {
  notifPanel = document.getElementById("notif-panel");
  if (!notifPanel) {
    notifPanel = document.createElement("div");
    notifPanel.id = "notif-panel";
    notifPanel.className = "notif-panel";
    document.body.appendChild(notifPanel);
  }

  const evtSource = new EventSource(`${API_BASE}/notifications/stream`);

  evtSource.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data);
      if (data.type === "connected") return;
      showToast(data);
    } catch (_) {}
  };

  evtSource.onerror = () => {
    console.warn("[Notifications] SSE connection lost. Retrying...");
  };
}

function showToast(data) {
  const toast = document.createElement("div");
  toast.className = `notif-toast ${data.type || ""}`;

  let title = "", body = "";
  switch (data.type) {
    case "new_event":
      title = "🎉 New Event";
      body  = `<strong>${data.title}</strong> has been added!`;
      break;
    case "almost_full":
      title = "⚠️ Almost Full";
      body  = `<strong>${data.title}</strong> — only ${data.remaining_seats} seat(s) left!`;
      break;
    case "seat_open":
      title = "✅ Seat Available";
      body  = `A seat just opened in <strong>${data.title}</strong>!`;
      break;
    default:
      title = "📢 Notification";
      body  = JSON.stringify(data);
  }

  toast.innerHTML = `
    <span class="notif-close" onclick="this.parentElement.remove()" title="Dismiss">✕</span>
    <div class="notif-title">${title}</div>
    <div class="notif-body">${body}</div>
  `;

  notifPanel.prepend(toast);

  // Auto-dismiss after 6 seconds
  setTimeout(() => toast.remove(), 6000);
}

// Expose for manual use
window.showToast = showToast;
window.initNotifications = initNotifications;

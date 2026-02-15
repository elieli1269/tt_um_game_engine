const sender = document.getElementById("sender");
const kind = document.getElementById("kind");
const target = document.getElementById("target");
const message = document.getElementById("message");
const external = document.getElementById("external");
const sendForm = document.getElementById("send-form");
const sendStatus = document.getElementById("send-status");
const inboxUser = document.getElementById("inbox-user");
const refreshBtn = document.getElementById("refresh-btn");
const enableNotifBtn = document.getElementById("enable-notif");
const list = document.getElementById("messages");
const roomInput = document.getElementById("room");

let appUsers = [];
let appGroups = {};
let lastSeen = 0;

async function fetchUsers() {
  const res = await fetch("api.php?action=users");
  const data = await res.json();
  appUsers = data.users || [];
  appGroups = data.groups || {};

  [sender, inboxUser].forEach((el) => {
    el.innerHTML = appUsers.map((u) => `<option value="${u}">${u}</option>`).join("");
  });

  updateTargets();
}

function updateTargets() {
  if (kind.value === "group") {
    target.innerHTML = Object.keys(appGroups).map((g) => `<option value="${g}">${g}</option>`).join("");
  } else {
    target.innerHTML = appUsers.map((u) => `<option value="${u}">${u}</option>`).join("");
  }
}

function pushNotification(title, text) {
  if (!("Notification" in window) || Notification.permission !== "granted") return;
  new Notification(title, { body: text });
}

async function refreshInbox() {
  const user = inboxUser.value;
  if (!user) return;

  const res = await fetch(`api.php?action=inbox&user=${encodeURIComponent(user)}&after_id=${lastSeen}`);
  const data = await res.json();
  const messages = data.messages || [];

  if (messages.length === 0 && list.children.length === 0) {
    list.innerHTML = "<li>Aucun message.</li>";
    return;
  }

  if (list.children.length === 1 && list.children[0].textContent === "Aucun message.") {
    list.innerHTML = "";
  }

  messages.forEach((msg) => {
    lastSeen = Math.max(lastSeen, Number(msg.id));
    const li = document.createElement("li");
    const ext = msg.external ? "[EXT]" : "";
    li.textContent = `#${msg.id} ${ext} ${msg.sender} -> ${msg.kind}:${msg.target} | ${msg.message}`;
    list.prepend(li);
    pushNotification(`Nouveau message de ${msg.sender}`, msg.message);
  });
}

sendForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    sender: sender.value,
    kind: kind.value,
    target: target.value,
    message: message.value,
    external: external.checked,
  };

  const res = await fetch("api.php?action=send", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  if (!res.ok) {
    sendStatus.textContent = data.error || "Erreur";
    return;
  }

  sendStatus.textContent = `Message envoyé (#${data.id})`;
  message.value = "";
});

kind.addEventListener("change", updateTargets);
refreshBtn.addEventListener("click", refreshInbox);
enableNotifBtn.addEventListener("click", async () => {
  if ("Notification" in window) {
    await Notification.requestPermission();
  }
});

document.getElementById("audio-call").addEventListener("click", async () => {
  const room = encodeURIComponent(roomInput.value || "audio-room");
  const res = await fetch(`api.php?action=call_link&room=${room}&video=0`);
  const data = await res.json();
  window.open(data.url, "_blank");
});

document.getElementById("video-call").addEventListener("click", async () => {
  const room = encodeURIComponent(roomInput.value || "video-room");
  const res = await fetch(`api.php?action=call_link&room=${room}&video=1`);
  const data = await res.json();
  window.open(data.url, "_blank");
});

fetchUsers().then(() => {
  refreshInbox();
  setInterval(refreshInbox, 1000);
});

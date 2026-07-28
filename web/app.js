const form = document.querySelector("#chat-form");
const input = document.querySelector("#query-input");
const sendButton = document.querySelector("#send-button");
const clearButton = document.querySelector("#clear-button");
const messages = document.querySelector("#messages");
const status = document.querySelector("#status");

function addMessage(role, text, tools = []) {
  const article = document.createElement("article");
  article.className = `message ${role === "user" ? "user-message" : "assistant-message"}`;

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "YOU" : "D3 / ASSISTANT";
  article.append(label);

  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  article.append(paragraph);

  if (tools.length > 0) {
    const meta = document.createElement("div");
    meta.className = "message-label";
    meta.textContent = `TOOLS · ${tools.join(" → ")}`;
    meta.style.color = "var(--accent)";
    meta.style.marginTop = "12px";
    article.append(meta);
  }

  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
}

function setBusy(isBusy) {
  input.disabled = isBusy;
  sendButton.disabled = isBusy;
  sendButton.querySelector("span").textContent = isBusy ? "Đang xử lý" : "Gửi";
}

async function sendMessage(query) {
  addMessage("user", query);
  setBusy(true);
  status.className = "composer-status";
  status.textContent = "Đang kiểm tra phạm vi và suy luận...";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Không thể xử lý câu hỏi.");
    addMessage("assistant", payload.answer, payload.tool_calls || []);
    status.textContent = payload.in_scope ? "Đã trả lời trong phạm vi trợ lý." : "Câu hỏi ngoài phạm vi đã được bỏ qua.";
  } catch (error) {
    status.className = "composer-status error";
    status.textContent = error.message || "Không thể kết nối tới server.";
    addMessage("assistant", "Mình chưa thể xử lý yêu cầu này. Hãy kiểm tra server và thử lại.");
  } finally {
    setBusy(false);
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const query = input.value.trim();
  if (!query || sendButton.disabled) return;
  input.value = "";
  input.style.height = "auto";
  sendMessage(query);
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 140)}px`;
});

document.querySelectorAll(".example-chip").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent;
    input.dispatchEvent(new Event("input"));
    input.focus();
  });
});

clearButton.addEventListener("click", () => {
  messages.replaceChildren();
  addMessage("assistant", "Đã xóa hội thoại. Bạn muốn tìm khóa học hoặc hỏi về lộ trình nào?");
  status.className = "composer-status";
  status.textContent = "Enter để gửi · Shift + Enter để xuống dòng";
  input.focus();
});

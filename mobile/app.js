const pairing = document.getElementById("pairing");
const command = document.getElementById("command");
const sendButton = document.getElementById("send");
const result = document.getElementById("result");
const state = document.getElementById("state");

pairing.value = sessionStorage.getItem("ameba-pairing-code") || "";

async function sendText(text) {
  if (!/^\d{6}$/.test(pairing.value)) {
    result.textContent = "請先輸入電腦橋接程式顯示的 6 位數配對碼";
    pairing.focus();
    return;
  }
  sessionStorage.setItem("ameba-pairing-code", pairing.value);
  if (!text.trim()) {
    result.textContent = "請先用手機鍵盤的麥克風輸入指令";
    command.focus();
    return;
  }
  sendButton.disabled = true;
  result.textContent = `已送出「${text}」，等待板卡回覆…`;
  try {
    const response = await fetch("/api/command", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Pairing-Code": pairing.value },
      body: JSON.stringify({ text }),
      signal: AbortSignal.timeout(8000)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "傳送失敗");
    state.textContent = `藍燈${data.blue ? "開" : "關"}、綠燈${data.green ? "開" : "關"}`;
    result.textContent = data.action === "BLINK3"
      ? "板卡回覆：已閃爍三次，原狀態已恢復"
      : data.action === "OFF"
        ? "異常指令：板卡已回覆，兩燈設定為熄滅"
        : `板卡回覆：${state.textContent}`;
  } catch (error) {
    if (error.message.includes("通訊失敗") || error.name === "TimeoutError") state.textContent = "未知";
    result.textContent = `操作失敗：${error.message}`;
  } finally {
    sendButton.disabled = false;
  }
}

sendButton.addEventListener("click", () => { void sendText(command.value); });
command.addEventListener("keydown", (event) => {
  if (event.key === "Enter") void sendText(command.value);
});
document.querySelectorAll("[data-command]").forEach((button) => {
  button.addEventListener("click", () => { void sendText(button.dataset.command); });
});

import { parseVoiceCommand, parseBoardReply } from "./commands.mjs";

const $ = (id) => document.getElementById(id);
const ui = {
  connect: $("connect-button"), disconnect: $("disconnect-button"), listen: $("listen-button"),
  test: $("test-button"), testInput: $("test-input"), connection: $("connection-state"),
  micTest: $("mic-test-button"), micResult: $("mic-test-result"), micLevel: $("mic-level"),
  transcript: $("transcript"), interpretation: $("interpretation"), execution: $("execution"),
  blueLamp: $("blue-lamp"), greenLamp: $("green-lamp"), blueState: $("blue-state"), greenState: $("green-state")
};

const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let port = null;
let reader = null;
let pending = null;
let sequence = 0;
let listening = false;
let micTesting = false;
let connecting = false;

function updateButtons() {
  ui.connect.disabled = !!port || connecting;
  ui.disconnect.disabled = !port || connecting;
  ui.listen.disabled = !port || !Recognition || listening || micTesting || !!pending;
  ui.test.disabled = !port || !!pending;
  ui.micTest.disabled = listening || micTesting;
}

function showBoardState(blue, green) {
  ui.blueLamp.classList.toggle("on", blue);
  ui.greenLamp.classList.toggle("on", green);
  ui.blueState.textContent = blue ? "開" : "關";
  ui.greenState.textContent = green ? "開" : "關";
}

function unknownBoardState() {
  ui.blueLamp.classList.remove("on");
  ui.greenLamp.classList.remove("on");
  ui.blueState.textContent = "未知";
  ui.greenState.textContent = "未知";
}

function resolvePending(reply) {
  if (!pending || reply.id !== pending.id) return;
  clearTimeout(pending.timer);
  const current = pending;
  pending = null;
  updateButtons();
  if (reply.type === "ACK") {
    showBoardState(reply.blue, reply.green);
    current.resolve(reply);
  } else {
    if (typeof reply.blue === "boolean" && typeof reply.green === "boolean") showBoardState(reply.blue, reply.green);
    current.reject(new Error(`板卡拒絕指令：${reply.message}`));
  }
}

async function readLoop(activePort) {
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (activePort.readable && port === activePort) {
      reader = activePort.readable.getReader();
      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          if (buffer.length > 256) buffer = "";
          let end;
          while ((end = buffer.indexOf("\n")) >= 0) {
            const line = buffer.slice(0, end).trim();
            buffer = buffer.slice(end + 1);
            const reply = parseBoardReply(line);
            if (reply) resolvePending(reply);
          }
        }
      } finally {
        reader.releaseLock();
        reader = null;
      }
      break;
    }
  } catch (error) {
    if (port === activePort) ui.execution.textContent = `通訊中斷：${error.message}`;
  } finally {
    if (port === activePort) await disconnect("裝置已斷線");
  }
}

async function send(action) {
  if (!port?.writable) throw new Error("尚未連接開發板");
  if (pending) throw new Error("前一個指令尚未完成");
  sequence = (sequence % 999999) + 1;
  const id = sequence;
  const response = new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      if (pending?.id === id) {
        pending = null;
        unknownBoardState();
        updateButtons();
        reject(new Error("等待板卡回覆逾時；LED 狀態未確認"));
      }
    }, 5000);
    pending = { id, timer, resolve, reject };
  });
  updateButtons();
  const writer = port.writable.getWriter();
  try {
    await writer.write(new TextEncoder().encode(`CMD ${id} ${action}\n`));
  } catch (error) {
    if (pending?.id === id) {
      clearTimeout(pending.timer);
      pending.reject(new Error(`傳送失敗：${error.message}`));
      pending = null;
    }
  } finally {
    writer.releaseLock();
    updateButtons();
  }
  return response;
}

async function disconnect(message = "已中斷連線") {
  const oldPort = port;
  port = null;
  if (pending) {
    clearTimeout(pending.timer);
    pending.reject(new Error("通訊中斷，LED 狀態未確認"));
    pending = null;
  }
  try { await reader?.cancel(); } catch { /* 裝置拔除時可能已關閉 */ }
  try { await oldPort?.close(); } catch { /* 裝置拔除時可能已關閉 */ }
  ui.connection.textContent = message;
  unknownBoardState();
  updateButtons();
}

ui.connect.addEventListener("click", async () => {
  if (!navigator.serial) {
    ui.connection.textContent = "此瀏覽器不支援 Web Serial，請使用桌面版 Chrome 或 Edge 的 localhost 網頁";
    return;
  }
  connecting = true;
  updateButtons();
  try {
    const selected = await navigator.serial.requestPort();
    await selected.open({ baudRate: 115200 });
    port = selected;
    ui.connection.textContent = "已連線，正在讀取板卡設定…";
    void readLoop(selected);
    await send("STATUS");
    ui.connection.textContent = "已連接 Ameba Mini";
    ui.execution.textContent = "板卡已回覆，可開始操作";
  } catch (error) {
    if (port) await disconnect("連線失敗");
    ui.connection.textContent = error.name === "NotFoundError" ? "已取消選擇序列埠" : `連線失敗：${error.message}`;
  } finally {
    connecting = false;
    updateButtons();
  }
});

ui.disconnect.addEventListener("click", () => { void disconnect(); });

async function handleText(text) {
  ui.transcript.textContent = text || "未辨識到語音";
  const action = parseVoiceCommand(text);
  if (!action) {
    ui.interpretation.textContent = "未收到語音或文字";
    ui.execution.textContent = "未傳送指令，LED 設定保持不變";
    return;
  }
  const descriptions = {
    LEFT: "左邊開燈 → 藍燈",
    RIGHT: "右邊開燈 → 綠燈",
    BLINK3: "閃爍三次 → 藍燈與綠燈一起閃，然後恢復原狀態",
    OFF: "異常指令 → 藍燈與綠燈全部熄滅"
  };
  ui.interpretation.textContent = descriptions[action];
  ui.execution.textContent = action === "BLINK3" ? "已送出，等待板卡完成三次閃爍…" : "已送出，等待板卡回覆…";
  try {
    await send(action);
    ui.execution.textContent = action === "BLINK3"
      ? "板卡已回覆：三次閃爍完成，原狀態已恢復"
      : action === "OFF"
        ? "板卡已回覆：兩燈已設定為熄滅"
        : "板卡已回覆，請觀察 LED 實際亮滅";
  } catch (error) {
    ui.execution.textContent = error.message;
  }
}

ui.test.addEventListener("click", () => { void handleText(ui.testInput.value); });
ui.testInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !ui.test.disabled) void handleText(ui.testInput.value);
});

ui.micTest.addEventListener("click", async () => {
  if (!navigator.mediaDevices?.getUserMedia) {
    ui.micResult.textContent = "此瀏覽器無法讀取麥克風，請改用桌面版 Chrome 或 Edge";
    return;
  }
  micTesting = true;
  updateButtons();
  let stream;
  let context;
  let frame;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const analyser = context.createAnalyser();
    analyser.fftSize = 2048;
    source.connect(analyser);
    const samples = new Uint8Array(analyser.fftSize);
    let highest = 0;
    const deviceName = stream.getAudioTracks()[0]?.label || "預設麥克風";
    ui.micResult.textContent = `正在測試「${deviceName}」，請說話…`;
    const measure = () => {
      analyser.getByteTimeDomainData(samples);
      let sum = 0;
      for (const sample of samples) sum += ((sample - 128) / 128) ** 2;
      const level = Math.sqrt(sum / samples.length);
      highest = Math.max(highest, level);
      ui.micLevel.style.width = `${Math.min(100, level * 450)}%`;
      frame = requestAnimationFrame(measure);
    };
    measure();
    await new Promise((resolve) => setTimeout(resolve, 5000));
    ui.micResult.textContent = highest < 0.008
      ? `「${deviceName}」幾乎沒有收到聲音；請檢查靜音與瀏覽器預設麥克風`
      : `「${deviceName}」有收到聲音；現在按「開始聆聽」並在提示後說話`;
  } catch (error) {
    ui.micResult.textContent = `麥克風檢查失敗（${error.name}）：${error.message}`;
  } finally {
    cancelAnimationFrame(frame);
    ui.micLevel.style.width = "0";
    stream?.getTracks().forEach((track) => track.stop());
    await context?.close();
    micTesting = false;
    updateButtons();
  }
});

if (Recognition) {
  const recognition = new Recognition();
  recognition.lang = "zh-TW";
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;
  recognition.onaudiostart = () => { ui.execution.textContent = "麥克風已啟動，請現在說話"; };
  recognition.onresult = (event) => { void handleText(event.results[0][0].transcript); };
  recognition.onerror = (event) => {
    ui.transcript.textContent = "未辨識到語音";
    ui.interpretation.textContent = "未產生控制指令";
    const explanations = {
      "not-allowed": "麥克風權限被拒絕；請在瀏覽器網址列左側允許此網站使用麥克風",
      "service-not-allowed": "瀏覽器未允許語音辨識服務；請改用桌面版 Chrome 或 Edge",
      "audio-capture": "無法取得麥克風；請檢查 Windows 與瀏覽器的輸入裝置設定",
      "no-speech": "沒有偵測到聲音；請確認選對麥克風、沒有靜音，並靠近麥克風再說一次",
      "network": "語音辨識服務連線失敗；請檢查網路，並用桌面版 Chrome 或 Edge 重試",
      "language-not-supported": "此瀏覽器不支援繁體中文語音辨識（zh-TW）"
    };
    ui.execution.textContent = `語音辨識失敗（${event.error}）：${explanations[event.error] || event.message || "請檢查瀏覽器與麥克風設定"}`;
  };
  recognition.onend = () => {
    listening = false;
    ui.listen.textContent = "開始聆聽";
    updateButtons();
  };
  ui.listen.addEventListener("click", () => {
    try {
      recognition.start();
      listening = true;
      ui.listen.textContent = "聆聽中…";
      ui.execution.textContent = "正在辨識語音";
      updateButtons();
    } catch (error) {
      ui.execution.textContent = `無法啟動麥克風：${error.message}`;
    }
  });
} else {
  ui.execution.textContent = "此瀏覽器不支援語音辨識，請使用支援的桌面瀏覽器";
}

updateButtons();

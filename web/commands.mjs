export function parseVoiceCommand(text) {
  const cleaned = String(text).replace(/[\s\p{P}\p{S}]/gu, "");
  if (cleaned === "左邊開燈") return "LEFT";
  if (cleaned === "右邊開燈") return "RIGHT";
  if (cleaned === "閃爍三次" || cleaned === "閃爍3次") return "BLINK3";
  return String(text).trim() ? "OFF" : null;
}

export function parseBoardReply(line) {
  const match = /^(ACK|ERR) ([1-9]\d{0,5}) (.+)$/.exec(line.trim());
  if (!match) return null;
  if (match[1] === "ERR") {
    const errorState = /^(.*?) BLUE=([01]) GREEN=([01])$/.exec(match[3]);
    return errorState
      ? { type: "ERR", id: Number(match[2]), message: errorState[1], blue: errorState[2] === "1", green: errorState[3] === "1" }
      : { type: "ERR", id: Number(match[2]), message: match[3] };
  }
  const state = /^BLUE=([01]) GREEN=([01])$/.exec(match[3]);
  if (!state) return null;
  return { type: "ACK", id: Number(match[2]), blue: state[1] === "1", green: state[2] === "1" };
}

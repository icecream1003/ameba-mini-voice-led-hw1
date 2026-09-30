import assert from "node:assert/strict";
import { test } from "node:test";
import { parseVoiceCommand, parseBoardReply } from "../web/commands.mjs";

test("只接受指定控制指令並容許標點與空白", () => {
  assert.equal(parseVoiceCommand("左邊開燈。"), "LEFT");
  assert.equal(parseVoiceCommand("右 邊 開 燈"), "RIGHT");
  assert.equal(parseVoiceCommand("閃爍三次！"), "BLINK3");
  assert.equal(parseVoiceCommand("閃爍3次"), "BLINK3");
  assert.equal(parseVoiceCommand("左邊開燈，右邊開燈"), "OFF");
  assert.equal(parseVoiceCommand("請把左邊開燈"), "OFF");
  assert.equal(parseVoiceCommand("今天天氣很好"), "OFF");
  assert.equal(parseVoiceCommand(""), null);
  assert.equal(parseVoiceCommand("   "), null);
});

test("只接受有編號且格式完整的板卡回覆", () => {
  assert.deepEqual(parseBoardReply("ACK 12 BLUE=1 GREEN=0\r"), {
    type: "ACK", id: 12, blue: true, green: false
  });
  assert.deepEqual(parseBoardReply("ERR 2 UNKNOWN"), {
    type: "ERR", id: 2, message: "UNKNOWN"
  });
  assert.deepEqual(parseBoardReply("ERR 3 UNKNOWN BLUE=0 GREEN=0"), {
    type: "ERR", id: 3, message: "UNKNOWN", blue: false, green: false
  });
  assert.equal(parseBoardReply("ACK 4 BLUE=maybe GREEN=0"), null);
  assert.equal(parseBoardReply("boot message"), null);
});

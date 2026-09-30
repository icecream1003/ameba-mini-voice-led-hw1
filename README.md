# Ameba Mini 語音控制 LED

此專案以 **AMB82-MINI／RTL8735B** 為目標：電腦瀏覽器辨識「左邊開燈」、「右邊開燈」與「閃爍三次」，透過 USB 序列埠送到板卡。左邊使藍燈亮、綠燈滅；右邊使綠燈亮、藍燈滅；閃爍三次讓兩燈同步閃三次，再恢復原本亮滅狀態。辨識到其他非空白語句時，系統送出 `OFF`，使兩燈都熄滅；完全沒有辨識文字時不送指令。

**作業規格差異：**題目原文要求非控制語句不改變 LED 狀態。本版本依後續需求改為異常語句關閉兩燈，因此該驗收項目與原題目不同；繳交前請確認教師是否接受此安全關燈策略。

Arduino IDE 畫面顯示 AMB82-MINI 與 COM3。開發時使用過 AmebaPro2 板卡套件 `4.0.9-build20250805`，目前電腦安裝 `4.1.1-build20260922`；目前版本的 `variant.h` 將 `LED_B` 定義為 D23、`LED_G` 定義為 D24。LED 亮滅邏輯仍須燒錄後目視確認實體板卡反應。

## 執行環境

| 項目 | 本機環境或需求 |
| --- | --- |
| 開發板 | Realtek AMB82-MINI（RTL8735B），AmebaPro2 Arduino 板卡套件；目前安裝 `4.1.1-build20260922` |
| 電腦 | Windows；USB 資料線；Arduino IDE；COM 埠以本機裝置管理員顯示為準 |
| 桌面網頁 | Chrome 或 Edge、麥克風、Python 3（本機 `3.11.9`）；不需額外 Python 套件 |
| iPhone 模式 | iPhone Safari、同一 Wi-Fi、電腦端 Python 3 與 `pyserial>=3.5,<4`（本機 `3.5`） |
| 自動測試 | Node.js（本機 `v22.23.2`）與 Python 3；執行方式見下方「驗收與證據」 |

原始程式位於 `ameba_voice_led/`、`web/`、`mobile/`、`mobile_bridge.py`；`requirements-mobile.txt` 列出手機橋接程式的 Python 套件。`tests/` 是測試程式，`docs/` 有架構報告產生程式、協作紀錄與驗收表範本。若要執行 `docs/build_report.py`，須另裝 `requirements-report.txt` 的套件及 Windows 微軟正黑體；**此腳本會覆寫同名 Word 文件，請先備份自己寫過的內容。**

## 上傳 GitHub

這個資料夾已可作為 Git 專案使用。`.gitignore` 排除測試快取、產生的預覽圖與 `docs/` 中的 Word/PDF 文件；報告 PDF 請依作業要求另外繳交，不會隨原始碼自動上傳。

1. 在 GitHub 建立一個空的 repository，例如 `ameba-mini-voice-led`；不要勾選建立 README、`.gitignore` 或 License。
2. 在本資料夾開啟 PowerShell，設定這個專案的提交姓名與 GitHub 電子郵件，然後提交檔案：

   ```powershell
   git config user.name "你的名字"
   git config user.email "你的 GitHub 電子郵件"
   git add .
   git status --short
   git commit -m "Add Ameba Mini voice LED project"
   ```

3. 將 `你的帳號` 改成自己的 GitHub 帳號，再連接並上傳：

   ```powershell
   git remote add origin https://github.com/你的帳號/ameba-mini-voice-led.git
   git push -u origin main
   ```

4. 開啟 `https://github.com/你的帳號/ameba-mini-voice-led`，確認能看到 `README.md`、`ameba_voice_led/`、`web/`、`mobile/`、`requirements-mobile.txt`；將此網址放入繳交 PDF。之後修改程式，可執行 `git add .`、`git commit -m "說明修改"`、`git push` 更新。

## 系統流程

```text
電腦麥克風 → Web Speech API (zh-TW) → 指令比對
                                      ↓
                              Web Serial (115200)
                                      ↓
                  AMB82-MINI LED_B / LED_G → ACK 回覆
                                      ↓
                       網頁顯示板卡回報的輸出設定
```

網頁顯示的是**板卡程式回報的輸出設定**，不是用光感測器量到的實際發光情形。實際 LED 反應需以目視觀察記錄。

## 準備與執行

1. 在 Arduino IDE 選 **AmebaPro2 ARM (32-bits) Boards → AMB82-MINI**，序列埠選 **COM3**。參照[瑞昱 AMB82-MINI 入門文件](https://github.com/Ameba-AIoT/ameba-arduino-doc/blob/main/source/ameba_pro2/amb82-mini/Getting_Started/Getting%20Started%20with%20Ameba.rst)。COM 編號可能在重新插拔後改變，以 Windows 裝置管理員顯示為準。
2. 可先用 `Blink/Blink.ino` 分別替換成 `LED_B`、`LED_G` 並燒錄，目視記錄兩燈與 `HIGH`／`LOW` 控制結果。若實物亮滅相反，修改 `ameba_voice_led/ameba_voice_led.ino` 的 `LED_ON`、`LED_OFF`。
3. 用 Arduino IDE 開啟 `ameba_voice_led/ameba_voice_led.ino`，編譯並上傳。依瑞昱文件，若未啟用 Auto Flash Mode，進入燒錄模式的順序是：按住 UART_DOWNLOAD、按放 RESET、放開 UART_DOWNLOAD；上傳後按 RESET 執行。
4. 關閉 Arduino Serial Monitor，避免佔用 COM 埠。連接板卡 USB。
5. 在專案根目錄執行 `python -m http.server 8000`，用桌面版 Chrome 或 Edge 開啟 `http://localhost:8000/web/`。允許網站使用麥克風和序列埠。
6. 按「連接開發板」選擇板卡 COM 埠，接著展開「測試與除錯」先用文字測試三句指令與異常語句關燈。確認無誤後按「開始聆聽」測語音。

Web Speech API 與 Web Serial API 的支援依瀏覽器而異；語音辨識可能需要網路。若網頁顯示不支援，先檢查所用桌面瀏覽器與麥克風權限。`localhost` 可供 Web Serial 所需的安全內容環境使用。

若語音顯示 `no-speech`，請在「測試與除錯」按「檢查麥克風（5 秒）」並對著麥克風說話。若顯示幾乎沒有聲音，確認瀏覽器預設輸入裝置選的是實體 USB 麥克風、沒有靜音，並檢查 Windows 與網站的麥克風權限。若音量測試正常，按「開始聆聽」，等畫面顯示「麥克風已啟動，請現在說話」後再說指令。

## 序列通訊格式

網頁傳送 `CMD <id> LEFT\n`、`CMD <id> RIGHT\n`、`CMD <id> BLINK3\n`、`CMD <id> OFF\n` 或 `CMD <id> STATUS\n`。板卡回覆 `ACK <id> BLUE=1 GREEN=0\n` 等狀態。板卡若收到未知的有效格式指令，會先關閉兩燈，再回覆 `ERR <id> UNKNOWN BLUE=0 GREEN=0\n`。`BLINK3` 約需 1.8 秒，板卡完成並恢復原狀態後才回覆。每個指令有流水號，網頁只採信對應編號的回覆；逾時和斷線時狀態改為「未知」。

## iPhone 手機模式

手機模式保留電腦到板卡的 USB 線，由電腦橋接 COM3。手機和電腦需在同一個 Wi-Fi。由於手機連到電腦區網 IP 的一般 HTTP 網頁時，網頁麥克風 API 受安全環境限制，這個模式使用 **iPhone 鍵盤的「聽寫」**將語音轉成文字，再按「送出」。手機網頁也有手動按鈕供測試。

1. 在電腦瀏覽器的控制頁按「中斷連線」，並關閉 Arduino Serial Monitor。同一個 COM 埠同時只能由一個程式使用。
2. 在專案根目錄執行 `python -m pip install -r requirements-mobile.txt`（本機已有 pyserial 3.5 時可略過）。
3. 執行 `python mobile_bridge.py --port COM3`，保持這個視窗開啟。程式會印出手機網址和本次 6 位數配對碼。若 Windows 防火牆詢問，允許此程式在私人網路上連線。
4. 在 iPhone 的 Safari 開啟電腦顯示的網址，例如 `http://192.168.50.98:8765/`。這是目前電腦的 Wi-Fi IP，若網路改變請使用啟動時印出的新網址。輸入配對碼。
5. 點「語音或文字指令」輸入框，再點 iPhone 鍵盤上的麥克風，說「左邊開燈」、「右邊開燈」或「閃爍三次」。確認辨識文字後按「送出指令」，觀察板卡回覆及 LED。

若 iPhone 鍵盤沒有麥克風，前往「設定 → 一般 → 鍵盤」開啟「啟用聽寫」。若手機網址無法打開，確認兩端在同一 Wi-Fi，且不是隔離用的訪客網路；核對電腦防火牆的私人網路允許設定。手機模式使用區網 HTTP，請只在信任的 Wi-Fi 上使用。橋接程式的配對碼會在每次啟動時更換。

參考：[Apple iPhone 聽寫說明](https://support.apple.com/zh-tw/guide/iphone/-iph2c0651d2/ios)、[MDN 安全內容說明](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Secure_Contexts)。

## 驗收與證據

請使用 `docs/acceptance-template.csv` 記錄左、右指令各五次的辨識文字、板卡回覆和實際 LED 觀察，再記錄一項異常語句、一次通訊中斷與加分指令「閃爍三次」。錄影時同框呈現網頁與板卡 LED。PDF 需要另附系統架構圖、操作說明、AI 協作紀錄、實際問題與修正、學習心得，以及 YouTube 和 GitHub 連結。

本機邏輯測試：`node --test tests/commands.test.mjs`。此測試只涵蓋文字判斷及回覆解析；不代替板卡、麥克風與通訊實測。

手機橋接測試：`python -m unittest discover -s tests -p test_mobile_bridge.py -v`。此測試使用假的序列裝置，不代替 iPhone 與實體板卡驗證。

## 參考資料

- [瑞昱 AMB82-MINI Arduino 入門文件](https://github.com/Ameba-AIoT/ameba-arduino-doc/blob/main/source/ameba_pro2/amb82-mini/Getting_Started/Getting%20Started%20with%20Ameba.rst)
- [瑞昱 AMB82-MINI Arduino 範例相容清單](https://github.com/Ameba-AIoT/ameba-arduino-doc/blob/main/source/ameba_pro2/amb82-mini/Example_Guides/Basic/Arduino-build-in%20example.rst)
- [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
- [MDN Web Serial API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Serial_API)

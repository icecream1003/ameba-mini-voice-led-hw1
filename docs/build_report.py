from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


BASE = Path(__file__).resolve().parent
BUILD = BASE / ".build"
BUILD.mkdir(exist_ok=True)
FIGURE = BUILD / "system_architecture.png"
OUTPUT = BASE / "Ameba_Mini_語音控制_LED_系統說明.docx"
FONT_PATH = "C:/Windows/Fonts/msjh.ttc"


def font(size, bold=False):
    return ImageFont.truetype(FONT_PATH, size=size, index=1 if bold else 0)


def rounded_box(draw, xy, fill, outline, title, subtitle):
    draw.rounded_rectangle(xy, radius=24, fill=fill, outline=outline, width=3)
    x0, y0, x1, y1 = xy
    draw.text(((x0 + x1) / 2, y0 + 28), title, font=font(32, True), fill="#14263a", anchor="ma")
    draw.text(((x0 + x1) / 2, y0 + 73), subtitle, font=font(24), fill="#48576a", anchor="ma")


def arrow(draw, start, end, color="#4b6b88"):
    import math
    draw.line([start, end], fill=color, width=6)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    wing = 16
    back = 24
    a = (end[0] - back * math.cos(angle) + wing * math.sin(angle), end[1] - back * math.sin(angle) - wing * math.cos(angle))
    b = (end[0] - back * math.cos(angle) - wing * math.sin(angle), end[1] - back * math.sin(angle) + wing * math.cos(angle))
    draw.polygon([end, a, b], fill=color)


image = Image.new("RGB", (1900, 780), "#ffffff")
draw = ImageDraw.Draw(image)
draw.text((90, 30), "電腦直接控制", font=font(31, True), fill="#203854")
draw.text((90, 370), "iPhone 區網控制", font=font(31, True), fill="#203854")
rounded_box(draw, (80, 90, 430, 270), "#edf6fa", "#80b8cc", "電腦麥克風", "Web Speech 辨識")
rounded_box(draw, (520, 90, 900, 270), "#edf6fa", "#80b8cc", "電腦網頁", "文字比對與 Web Serial")
rounded_box(draw, (980, 90, 1320, 270), "#eaf5ef", "#8abb9c", "USB 序列埠", "COM3  115200")
rounded_box(draw, (1410, 250, 1820, 530), "#edf2fa", "#8ca9cd", "AMB82-MINI", "LED_B 藍燈  LED_G 綠燈")
rounded_box(draw, (80, 440, 430, 620), "#fff6e8", "#d4b486", "iPhone 聽寫", "語音轉成文字")
rounded_box(draw, (520, 440, 900, 620), "#fff6e8", "#d4b486", "Safari 手機頁面", "送出辨識文字")
rounded_box(draw, (980, 440, 1320, 620), "#f3edf9", "#b9a0d0", "電腦 Python", "區網接收並橋接 COM3")
for a, b in [((430, 180), (520, 180)), ((900, 180), (980, 180)), ((1320, 180), (1430, 315)),
             ((430, 530), (520, 530)), ((900, 530), (980, 530)), ((1320, 530), (1410, 470))]:
    arrow(draw, a, b)
draw.text((1410, 610), "板卡回傳 ACK 及輸出設定", font=font(26), fill="#415772")
draw.text((1410, 653), "實際發光需目視確認", font=font(25), fill="#7b5660")
image.save(FIGURE)


def set_run_font(run, size=None, bold=None, color=None):
    run.font.name = "Microsoft JhengHei"
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def set_cell_shading(cell, color):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), color)
    tc_pr.append(shading)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    if widths:
        for i, width in enumerate(widths):
            table.columns[i].width = Cm(width)
    for i, head in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = head
        set_cell_shading(cell, "DCE9F1")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for para in cell.paragraphs:
            for run in para.runs:
                set_run_font(run, 9, True)
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = value
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for para in cells[i].paragraphs:
                para.paragraph_format.space_after = Pt(0)
                for run in para.runs:
                    set_run_font(run, 9)
    return table


def add_step(doc, number, title, body):
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.left_indent = Cm(0.3)
    p.paragraph_format.first_line_indent = Cm(-0.3)
    set_run_font(p.add_run(f"{number}. {title}　"), 10.5, True)
    set_run_font(p.add_run(body), 10.5)


doc = Document()
section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.top_margin = Cm(1.7)
section.bottom_margin = Cm(1.6)
section.left_margin = Cm(2.1)
section.right_margin = Cm(2.1)

styles = doc.styles
for name in ("Normal", "Title", "Heading 1", "Heading 2"):
    style = styles[name]
    style.font.name = "Microsoft JhengHei"
    style._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")
    style.font.color.rgb = RGBColor(0, 0, 0)
styles["Normal"].font.size = Pt(10.5)
styles["Normal"].paragraph_format.space_after = Pt(4)
styles["Normal"].paragraph_format.line_spacing = 1.25
styles["Title"].font.size = Pt(22)
styles["Title"].font.bold = True
styles["Heading 1"].font.size = Pt(15)
styles["Heading 1"].font.bold = True
styles["Heading 1"].paragraph_format.space_before = Pt(11)
styles["Heading 1"].paragraph_format.space_after = Pt(7)
styles["Heading 2"].font.size = Pt(11.5)
styles["Heading 2"].font.bold = True
styles["Heading 2"].paragraph_format.space_before = Pt(8)
styles["Heading 2"].paragraph_format.space_after = Pt(5)

title = doc.add_paragraph("Ameba Mini 語音控制 LED 系統", style="Title")
for properties in (styles["Title"]._element.get_or_add_pPr(), title._p.get_or_add_pPr()):
    for border in properties.findall(qn("w:pBdr")):
        properties.remove(border)
p = doc.add_paragraph()
set_run_font(p.add_run("系統架構 操作說明 AI 協作紀錄"), 11)
p = doc.add_paragraph()
set_run_font(p.add_run("本專題以電腦或 iPhone 辨識中文語音，將指定指令送至 AMB82-MINI 開發板，控制板上藍燈與綠燈。本文說明資料如何傳遞、如何操作與驗證，以及開發時實際使用 AI 修正問題的過程。"), 10.5)

doc.add_heading("一 系統架構", level=1)
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run().add_picture(str(FIGURE), width=Cm(15.3))
p = doc.add_paragraph("圖 1　電腦與 iPhone 控制 AMB82-MINI 的資料流程")
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
for run in p.runs:
    set_run_font(run, 9)

doc.add_heading("硬體與通訊設定", level=2)
add_table(doc, ["項目", "設定"], [
    ("開發板", "AMB82-MINI，晶片 RTL8735B"),
    ("板上 LED", "藍燈 LED_B 對應 D23；綠燈 LED_G 對應 D24。HIGH 點亮、LOW 熄滅。"),
    ("電腦與板卡", "USB 序列通訊，測試電腦顯示 COM3，鮑率 115200。COM 編號可能變動。"),
    ("手機與電腦", "同一 Wi-Fi 的區網 HTTP；iPhone Safari 傳送文字，電腦 Python 程式橋接 COM 埠。"),
], [3.3, 13.5])

doc.add_heading("指令與狀態回饋", level=2)
add_table(doc, ["辨識文字", "板卡指令", "LED 行為"], [
    ("左邊開燈", "LEFT", "藍燈亮、綠燈滅"),
    ("右邊開燈", "RIGHT", "藍燈滅、綠燈亮"),
    ("閃爍三次／閃爍3次", "BLINK3", "兩燈同步閃三次，再恢復原本設定"),
    ("其他非空白語句", "OFF", "藍燈與綠燈都熄滅"),
    ("沒有辨識文字", "不傳送", "保持原設定"),
], [5.0, 3.0, 8.8])
heading = doc.add_heading("二 操作說明", level=1)
heading.paragraph_format.page_break_before = True
doc.add_heading("電腦版操作", level=2)
computer_steps = [
    ("上傳板卡程式", "Arduino IDE 選擇 AMB82-MINI 與對應 COM 埠，開啟 ameba_voice_led.ino，編譯上傳後按板上的 RESET。"),
    ("釋放 COM 埠", "關閉 Arduino 序列監控視窗；若手機橋接程式正在使用 COM3，先停止它。"),
    ("啟動網頁", "在專案資料夾執行 python -m http.server 8000，使用桌面版 Chrome 或 Edge 開啟 http://127.0.0.1:8000/web/。"),
    ("連接與測試", "按「連接開發板」選擇 COM3。先在「測試與除錯」輸入三種指令，觀察板卡回覆和 LED。"),
    ("語音操作", "允許網站使用麥克風，按「開始聆聽」，等畫面提示麥克風已啟動後說出一個指令。介面會顯示辨識文字和執行結果。"),
]
for i, (title, body) in enumerate(computer_steps, 1):
    add_step(doc, i, title, body)

doc.add_heading("iPhone 版操作", level=2)
mobile_steps = [
    ("保留 USB 連線", "電腦繼續以 USB 連接開發板，並和 iPhone 連接同一個 Wi-Fi。"),
    ("釋放 COM 埠", "在電腦網頁按「中斷連線」，關閉 Arduino 序列監控視窗。"),
    ("啟動橋接程式", "在專案資料夾執行 python mobile_bridge.py --port COM3，保持程式執行；記下畫面印出的手機網址及本次六位數配對碼。"),
    ("開啟手機頁面", "用 iPhone Safari 開啟該網址並輸入配對碼。電腦 Wi-Fi IP 可能隨網路改變，請以程式當次顯示為準。"),
    ("使用聽寫", "點指令輸入框，再點 iPhone 鍵盤上的麥克風，說出指令；確認辨識文字後按「送出指令」。若沒有麥克風按鈕，於「設定 > 一般 > 鍵盤」開啟「啟用聽寫」。"),
]
for i, (title, body) in enumerate(mobile_steps, 1):
    add_step(doc, i, title, body)

doc.add_heading("異常處理與驗證方式", level=2)
add_table(doc, ["情況", "系統處理與驗證"], [
    ("非控制語句", "送出 OFF 並將兩燈關閉；介面顯示安全關燈結果。"),
    ("完全沒有辨識文字", "不傳送指令；LED 保持原設定。"),
    ("語音顯示 no-speech", "使用麥克風五秒音量檢查，確認輸入裝置、靜音與網站權限，再重新辨識。"),
    ("通訊中斷或逾時", "介面提示失敗，板卡狀態標為未知；重新連線後用 STATUS 取得板卡回報。"),
    ("現場驗收", "左、右指令各測五次，逐次記錄辨識結果、板卡回覆與目視 LED 反應；另測異常語句關燈及一次通訊中斷。"),
], [4.3, 12.5])
heading = doc.add_heading("三 AI 協作紀錄", level=1)
heading.paragraph_format.page_break_before = True
p = doc.add_paragraph()
set_run_font(p.add_run("開發過程以自然語言提出需求，再根據程式測試、板卡截圖及操作結果修正。下表保留關鍵提示詞與可確認的結果；未取得的五次現場驗收數據不在此表中臆填。"), 10.5)
add_table(doc, ["階段與提示詞", "AI 產出與修正", "驗證依據"], [
    ("規畫：運用 Vibe Coding 實作 Ameba Mini 語音控制 LED 系統", "將語音辨識、指令傳送、板卡控制、回饋和異常處理拆成可測試的流程。", "作業需求與原有 Blink 範例。"),
    ("實作：想要請你實做看看", "產生電腦網頁、Arduino 程式、序列指令格式及驗收表。", "文字判斷和回覆解析的本機測試通過。"),
    ("硬體修正：板卡型號是這個；提供 AMB82-MINI 截圖", "初版曾誤以為 AMB23。依截圖改為 AMB82-MINI，核對 LED_B=D23、LED_G=D24 及 HIGH 點亮邏輯。", "本機 AmebaPro2 板卡套件定義；使用者提供的板卡設定截圖。"),
    ("燒錄確認：這樣有嗎；提供 Arduino IDE 截圖", "辨識上傳結果，指示按 RESET、釋放 COM3 後連接控制頁。", "截圖顯示 upload success 與 AMB82-MINI on COM3。"),
    ("語音問題：語音辨識一直失敗；截圖顯示 no-speech", "辨別板卡通訊與語音輸入問題，新增五秒麥克風音量檢查和更清楚的錯誤提示。", "文字測試可控制 LED；畫面顯示 no-speech。"),
    ("加分與手機：可以加入閃爍三次嗎；我要怎麼在手機上也可以操作", "加入 BLINK3，完成後恢復原狀態；另加入 iPhone 聽寫頁、區網橋接及六位數配對碼。", "本機指令、序列模擬與 HTTP 測試通過；使用者回覆「完成了」。"),
    ("異常指令：收到異常指令的時候會兩邊都黑掉", "非空白的異常語句送出 OFF；板卡收到 OFF 或未知有效格式指令時關閉兩燈。", "本機測試通過，新韌體待實測。與原題目不改變 LED 的要求不同，繳交前需確認。"),
], [4.5, 7.7, 4.6])

doc.add_heading("實際問題與修正", level=2)
p = doc.add_paragraph()
set_run_font(p.add_run("最明確的硬體問題是初版板卡型號判斷錯誤。初版依 AMB23 文件規畫，但使用者提供的 Arduino IDE 畫面顯示 AMB82-MINI、COM3。AI 重新檢查已安裝的 AmebaPro2 套件，確認 LED_B 為 D23、LED_G 為 D24，並更新程式註解、操作文件與燒錄步驟。之後使用者提供的畫面顯示 upload success，證明更新程式可成功燒錄。這個過程顯示 AI 產生的硬體程式必須用實際板卡型號、套件定義和燒錄結果驗證。"), 10.5)

heading = doc.add_heading("四 學習心得與繳交資訊", level=1)
heading.paragraph_format.page_break_before = True
p = doc.add_paragraph()
set_run_font(p.add_run("學習心得由學生自行撰寫。可在下方直接輸入，再將完成的 Word 匯出為 PDF。"), 10.5)
reflection = doc.add_table(rows=1, cols=1)
reflection.style = "Table Grid"
reflection.rows[0].height = Cm(10)
reflection.rows[0].cells[0].text = "請在此撰寫學習心得"
for run in reflection.rows[0].cells[0].paragraphs[0].runs:
    set_run_font(run, 10, color=(110, 110, 110))
doc.add_heading("繳交連結與驗收結果", level=2)
for label in ["GitHub 專案連結：", "YouTube 示範影片連結：", "左邊開燈五次成功次數：", "右邊開燈五次成功次數：", "異常語句關燈與通訊中斷測試結果："]:
    p = doc.add_paragraph(style="Normal")
    set_run_font(p.add_run(label), 10.5)
    set_run_font(p.add_run("________________________________"), 10.5, color=(130, 130, 130))
p = doc.add_paragraph()
set_run_font(p.add_run("參考資料：瑞昱 AMB82-MINI Arduino 文件；Apple iPhone 聽寫說明；專案 README 與原始程式。"), 9)

doc.save(OUTPUT)
print(OUTPUT)

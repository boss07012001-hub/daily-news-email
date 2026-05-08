import feedparser
import smtplib
import os
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── 設定區 ──────────────────────────────────────────
SENDER_EMAIL    = os.environ["SENDER_EMAIL"]     # 寄件人 Gmail
SENDER_PASSWORD = os.environ["SENDER_PASSWORD"]  # Gmail 應用程式密碼
RECEIVER_EMAIL  = os.environ["RECEIVER_EMAIL"]   # 收件人（可填同一個）

# 搜尋關鍵字（每個關鍵字會獨立查詢 Google News RSS）
KEYWORDS = [
    "客訴",
    "客戶抱怨",
    "顧客抱怨",
    "消費者投訴",
    "客服糾紛",
]

MAX_PER_KEYWORD = 5  # 每個關鍵字最多顯示幾則
# ────────────────────────────────────────────────────


def fetch_google_news(keyword: str, max_results: int = 5) -> list[dict]:
    """從 Google News RSS 抓取指定關鍵字的新聞"""
    url = f"https://news.google.com/rss/search?q={keyword}&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:max_results]:
        pub = entry.get("published", "")
        try:
            pub_dt = datetime.datetime(*entry.published_parsed[:6])
            pub_str = pub_dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pub_str = pub
        results.append({
            "title":  entry.get("title", "（無標題）"),
            "link":   entry.get("link",  "#"),
            "source": entry.get("source", {}).get("title", "未知來源"),
            "pub":    pub_str,
            "summary": entry.get("summary", "")[:120] + "...",
        })
    return results


def build_html(all_news: dict[str, list]) -> str:
    today = datetime.date.today().strftime("%Y 年 %m 月 %d 日")
    
    # 產生各關鍵字區塊
    sections_html = ""
    total = 0
    for keyword, items in all_news.items():
        if not items:
            continue
        total += len(items)
        rows = ""
        for i, n in enumerate(items):
            bg = "#ffffff" if i % 2 == 0 else "#fdf6ee"
            rows += f"""
            <tr style="background:{bg};">
              <td style="padding:12px 16px; border-bottom:1px solid #f0e0c8;">
                <a href="{n['link']}" style="color:#d4621a; font-weight:600; text-decoration:none; font-size:14px;">
                  {n['title']}
                </a>
                <div style="color:#888; font-size:12px; margin-top:4px;">
                  📰 {n['source']} &nbsp;|&nbsp; 🕐 {n['pub']}
                </div>
              </td>
            </tr>"""

        sections_html += f"""
        <div style="margin-bottom:32px;">
          <div style="background:#d4621a; color:#fff; padding:10px 18px; border-radius:6px 6px 0 0;
                      font-size:15px; font-weight:700; letter-spacing:1px;">
            🔍 關鍵字：{keyword}（共 {len(items)} 則）
          </div>
          <table width="100%" cellpadding="0" cellspacing="0"
                 style="border:1px solid #f0e0c8; border-top:none; border-radius:0 0 6px 6px; overflow:hidden;">
            {rows}
          </table>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="UTF-8"></head>
<body style="margin:0; padding:0; background:#f5f5f5; font-family:'Helvetica Neue',Arial,sans-serif;">
  <div style="max-width:680px; margin:30px auto; background:#fff; border-radius:10px;
              box-shadow:0 2px 12px rgba(0,0,0,0.08); overflow:hidden;">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#d4621a,#f0a060); padding:28px 32px;">
      <div style="color:#fff; font-size:22px; font-weight:700;">📋 客訴相關新聞日報</div>
      <div style="color:rgba(255,255,255,0.85); font-size:13px; margin-top:6px;">
        {today} &nbsp;|&nbsp; 共收錄 {total} 則新聞
      </div>
    </div>

    <!-- Body -->
    <div style="padding:28px 32px;">
      {sections_html}
    </div>

    <!-- Footer -->
    <div style="background:#f9f9f9; border-top:1px solid #eee; padding:16px 32px;
                text-align:center; color:#aaa; font-size:11px;">
      此郵件由 GitHub Actions 自動產生 · 每日早上 8:00 發送<br>
      關鍵字來源：Google News Taiwan
    </div>

  </div>
</body>
</html>"""
    return html


def send_email(html_body: str):
    today = datetime.date.today().strftime("%Y/%m/%d")
    subject = f"【客訴新聞日報】{today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SENDER_EMAIL
    msg["To"]      = RECEIVER_EMAIL
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
    print(f"✅ 信件已寄出至 {RECEIVER_EMAIL}")


def main():
    print("🔍 開始抓取新聞...")
    all_news = {}
    for kw in KEYWORDS:
        print(f"  → 搜尋：{kw}")
        all_news[kw] = fetch_google_news(kw, MAX_PER_KEYWORD)

    print("📝 產生 HTML 信件...")
    html = build_html(all_news)

    print("📧 寄送郵件...")
    send_email(html)


if __name__ == "__main__":
    main()

import os
import json
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(CURRENT_DIR, "sources.json")

def load_email_config():
    if os.path.exists(SOURCES_FILE):
        try:
            with open(SOURCES_FILE, "r", encoding="utf-8") as f:
                sdata = json.load(f)
                return sdata.get("distribution_settings", {}).get("email", {
                    "enabled": False,
                    "smtp_host": "smtp.qq.com",
                    "smtp_port": 465,
                    "use_ssl": True,
                    "sender_email": "",
                    "sender_password": "",
                    "recipient_emails": ""
                })
        except Exception:
            pass
    return {
        "enabled": False,
        "smtp_host": "smtp.qq.com",
        "smtp_port": 465,
        "use_ssl": True,
        "sender_email": "",
        "sender_password": "",
        "recipient_emails": ""
    }

def send_email_brief(rendered_html, custom_cfg=None):
    cfg = custom_cfg or load_email_config()
    
    smtp_host = cfg.get("smtp_host", "").strip()
    smtp_port = int(cfg.get("smtp_port", 465))
    use_ssl = cfg.get("use_ssl", True)
    sender = cfg.get("sender_email", "").strip()
    password = cfg.get("sender_password", "").strip()
    recipients_str = cfg.get("recipient_emails", "").strip()

    if not sender or not password or not recipients_str:
        return {"success": False, "error": "发件人邮箱、密码/授权码或收件人未配置"}

    recipients = [r.strip() for r in recipients_str.replace(";", ",").split(",") if r.strip()]
    if not recipients:
        return {"success": False, "error": "有效收件人列表为空"}

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    subject = f"📰 每日全球宏观与市场晚报内参 - {today_str}"

    msg = MIMEMultipart('alternative')
    msg['From'] = Header(f"Antigravity 投研晚报 <{sender}>", 'utf-8')
    msg['To'] = Header(", ".join(recipients), 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    html_part = MIMEText(rendered_html, 'html', 'utf-8')
    msg.attach(html_part)

    try:
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
            server.starttls()
            
        server.login(sender, password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()
        print(f"✅ 邮件已成功发送至 {len(recipients)} 个收件人: {', '.join(recipients)}")
        return {"success": True, "message": f"邮件已成功发送至: {', '.join(recipients)}"}
    except Exception as e:
        print(f"⚠️ 邮件发送失败: {e}")
        return {"success": False, "error": f"SMTP 错误: {str(e)}"}

if __name__ == "__main__":
    print("Email module ready.")

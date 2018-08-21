# encoding: UTF-8

import smtplib
from email.mime.text import MIMEText
_user = "gongkai1000@qq.com"
_pwd  = "mmrphtjvhvetbjij"
_to   = "gongkai@dachuizichan.com"

msg = MIMEText("Test")
msg["Subject"] = "测试一下"
msg["From"]    = _user
msg["To"]      = _to

try:
    s = smtplib.SMTP_SSL("smtp.qq.com", 465)
    s.login(_user, _pwd)
    s.sendmail(_user, _to, msg.as_string())
    s.quit()
    print("Success!")
except smtplib.SMTPException,e: 
    print ("Falied,%s" %e) 
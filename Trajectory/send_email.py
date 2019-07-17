#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
Created on Tue May 21 11:16:03 2019
Author: Gerardo A. Rivera Tello
Email: grivera@igp.gob.pe
-----
Copyright (c) 2019 Instituto Geofisico del Peru
-----
"""

import pandas as pd
import os, datetime

def send_mail(profnum):
    from email.mime.multipart import MIMEMultipart 
    from email.mime.text import MIMEText 
    from email.mime.base import MIMEBase 
    from email import encoders
    import smtplib

    fromaddr = "grivera@igp.gob.pe"
    gmail_password = os.getenv('USER_PASS')
    filename = f"prof{profnum}_clim_trajr16_latest.png"

    toaddr = ["gerardo_art@hotmail.com","andres.32mflores@gmail.com"]

    print(f"Sending email to the following recipients: {toaddr}")

    msg = MIMEMultipart() 
    msg['From'] = fromaddr 
    msg['To'] = ','.join(toaddr)
    msg['Subject'] = f"[AUTO] ARGO Profiler {profnum} update"
    body = f"The ARGO profiler #{profnum} trajectory has been updated with a new \
entry.\n Attached you can find the latest profile data.\n\n"
    msg.attach(MIMEText(body, 'plain')) 
    
    attachment = open(f"/home/grivera/GitLab/argo/Trajectory/Output/{filename}", "rb") 
    
    p = MIMEBase('application', 'octet-stream') 
    p.set_payload((attachment).read()) 
    
    # encode into base64 
    encoders.encode_base64(p) 
    p.add_header('Content-Disposition', f"attachment; filename= {filename}") 
    
    msg.attach(p) 
    # creates SMTP session 
    s = smtplib.SMTP_SSL('smtp.gmail.com', 465) 
    s.ehlo()
    s.login(fromaddr, gmail_password)
    text = msg.as_string() 
    s.sendmail(fromaddr, toaddr, text) 
    s.close()

if __name__ == "__main__":
    latest_plot = "3901231"
    send_mail(latest_plot)
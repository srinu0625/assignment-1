import smtplib
sender_mail="srinivasreddy.dumpali@gmail.com"
resever_mail="srinivasreddy.d0625@gmail;.com"
password=input(str("9000123577"))
message="this is from python code "
server=smtplib.SMTP("smtp@gmail.com",100)
server.starttls()
server.login(sender_mail,password)
print("---------------login_sucessfull--------------------")
server.sendmail(sender_mail,resever_mail,password)
print("Mail  has send to ----",resever_mail)


import threading;
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText 
import smtplib
from tg.configuration import AppConfig, config

import time
from surveymodel import *
import transaction

log = logging.getLogger(__name__);
from tgext.pylogservice import LogDBHandler;
__all__ = ['SendMailScheduler', 'SendMailUser' ] 

class SendMailScheduler(object):
    def __init__(self):
        dh = LogDBHandler( config=config,request=request);        
        log.addHandler(dh)
       
    
    def sendmail(self):
        self.sendmail = SendMail.querySendMail(page_size = 100)
        
        log.info("Query size : %s" %(len(self.sendmail)))
        
        for send in self.sendmail:
            print send
            sendMailUser = SendMailUser(send.sender_name,send.receive,send.subject,send.content)
            if( sendMailUser.sendToUser() ) :
                send.updateStatus()
                log.info("Status send to %s (%s) : True"  %(send.receive, send.id_send_mail))
            else:
                log.info("Status send to %s (%s) : False"  %(send.receive, send.id_send_mail))
            
        
        if (len(self.sendmail) >0):
            log.info("Commit Database success")
            transaction.commit()
            

class SendMailUser(threading.Thread):  
    def __init__(self,mailFrom, mailTo,mailSubject, mailContent):
        threading.Thread.__init__(self);
        self.sendType =0;
        self.SMTP_SERVER = config['smtp_server'] ;
        self.SMTP_PORT= config['smtp_port'] ;
        self.SMTP_USER = config['smtp_user'] ;
        self.SMTP_PASSWORD = config['smtp_password'] ;   
        
        self.emailTemplate = SystemEnvironment.getEmailTemplate()   
        self.mailFrom = mailFrom
        self.mailTo = mailTo
        self.mailSubject = mailSubject
        self.mailContent = mailContent
    
    def run(self):
        self.sendToUser();
    
    
    
    def sendToUser(self):
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.mailSubject;
            msg['From'] = self.mailFrom + '<' +self.SMTP_USER +'>'; #       self.SMTP_USER #self.mailFrom;
            msg['To'] = self.mailTo;
            
            part1 = MIMEText(self.mailContent, 'html');
            msg.attach(part1)
            
            
            server = smtplib.SMTP(self.SMTP_SERVER,self.SMTP_PORT) 
            server.ehlo()
            server.starttls()
            server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            server.sendmail(self.SMTP_USER, [self.mailTo], msg.as_string())            
            
            
            server.close();
            return True
            
        except Exception as e:
            log.exception("error : %s" %str(e)); 
            return False
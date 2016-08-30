
import threading;
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText 
import smtplib
from tg.configuration import AppConfig, config
from tg import request
import time
#from surveymodel import *
import transaction
from sqlalchemy import create_engine; 
from sqlalchemy.sql import text
from .models import  DeclarativeBase, init_model, DBSession, SendMail
from datetime import datetime
import logging;
log = logging.getLogger(__name__);
from tgext.pylogservice import LogDBHandler;
__all__ = ['SendMailScheduler', 'SendMailUser' ] 

class SendMailScheduler(object):
    def __init__(self):
        dh = LogDBHandler( config=config,request=request);        
        log.addHandler(dh)
        self.sendMail = SendMail
        self.sqlConfig = config['sqlalchemy.url'] ;
        self.engine = create_engine(self.sqlConfig);  
        
        self.querymail = text("select * from sur_send_mail where status='W'")
        self.queryupdatestatus = text("update sur_send_mail set status=:status , sended_date=:senddate where id_send_mail=:id")
        self.emailtemplate = text("select description from sur_sys_environment where environment_key='EMAIL_TEMPLATE'")
        
        init_model(self.engine)
        
    def __template__(self):
        self.template = self.engine.execute(self.emailtemplate)
        self.temp_template =''
        for r in self.template:
            self.temp_template=r['description']
        return self.temp_template
    
    def sendmail(self):
        conn  = self.engine.connect()
        result  = self.engine.execute(self.querymail)
        template = self.__template__()
        
        for r in result:
            print r['sender_name']
            
            self.email_content = {}
            self.email_content['email_content'] = r['content']
        
            for k,v in  self.email_content.iteritems():
                template = template.replace('[%s]' % k,v)
            
            
            
            sendMailUser = SendMailUser(r['sender_name'],r['receive'],r['subject'], template )
            
            
            
            
            
            if( sendMailUser.sendToUser() ) :
                self.engine.execute( self.queryupdatestatus, {'status':'F', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
                log.info("Status send to %s (%s) : True"  %(r['receive'] , r['id_send_mail'] ))
                print ("Status send to %s (%s) : True"  %(r['receive'], r['id_send_mail'] ))
            else:
                log.info("Status send to %s (%s) : False"  %(r['receive'], r['id_send_mail'] ))
                print ("Status send to %s (%s) : False"  %(r['receive'], r['id_send_mail'] ))
            del r
        
        #if (len(self.sendmail) >0):
        #    log.info("Commit Database success")
        #    print ("Commit Database success")
        #    transaction.commit()
        
        conn.close() 
        transaction.commit()
        del conn
        del result
        self.engine.dispose()

class SendMailUser(threading.Thread):  
    def __init__(self,mailFrom, mailTo,mailSubject, mailContent):
        threading.Thread.__init__(self);
        self.sendType =0;
        self.SMTP_SERVER = config['smtp_server'] ;
        self.SMTP_PORT= config['smtp_port'] ;
        self.SMTP_USER = config['smtp_user'] ;
        self.SMTP_PASSWORD = config['smtp_password'] ;   
        
        #self.emailTemplate = SystemEnvironment.getEmailTemplate()   
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
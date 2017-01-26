
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
from sqlalchemy.pool import NullPool
log = logging.getLogger(__name__);
from tgext.pylogservice import LogDBHandler
__all__ = ['SendMailScheduler', 'SendMailUser' ] 

class SendMailScheduler(object):
    def __init__(self):
        #dh = LogDBHandler( config=config,request=request);        
        #log.addHandler(dh)
        self.sendMail = SendMail
        self.sqlConfig = config['sqlalchemy.url'] ;
        self.engine = create_engine(self.sqlConfig,                                    
                       pool_size=20, max_overflow=0);  
        
        self.querymail = text("select * from sur_send_mail where status='W'")
        self.queryupdatestatus = text("update sur_send_mail set status=:status , sended_date=:senddate where id_send_mail=:id")
        self.emailtemplate = text("select description from sur_sys_environment where environment_key='EMAIL_TEMPLATE'")
        self.serverurl = text("select description from sur_sys_environment where environment_key='SERVER_URL'")
        
        self.urltemplate = "http://{0}/images/imagermc/{1}"
        
        init_model(self.engine)
        
        self.template = self.__template__()
        self.url = self.__serverurl__()
        
    def __template__(self):
        self.template = self.engine.execute(self.emailtemplate)
        self.temp_template =''
        for r in self.template:
            self.temp_template=r['description']
            del r
        return self.temp_template
    
    def __serverurl__(self):
        self.url = self.engine.execute(self.serverurl)
        self.temp_template ='localhost'
        for r in self.url:
            self.temp_template=r['description']
            del r
        return self.temp_template
    
    
    def __setSendMail(self,result):
        data = []
        for r in result:
            self.engine.execute( self.queryupdatestatus, {'status':'S', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
            data.append(r)
        transaction.commit()    
        result.close()
        return data
    def sendmail(self):
        conn  = self.engine.connect()
        result  = self.engine.execute(self.querymail)
        template = self.template
        result = self.__setSendMail(result)
        #print "sendMail : %s" %(len(result))
        for r in result:
            self.email_content = {}
            self.email_content['email_content'] = r['content']
            self.email_content['url_check'] = self.urltemplate.format(self.url, r['gen_code'])
            
            template = self.template
        
            for k,v in  self.email_content.iteritems():
                template = template.replace('[%s]' % k,v)
            
            
            
            sendMailUser = SendMailUser(r['sender_name'],r['receive'],r['subject'], template )
            if( sendMailUser.sendToUser() ) :
                self.engine.execute( self.queryupdatestatus, {'status':'F', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
                #log.info("Status send to %s (%s) : True"  %(r['receive'] , r['id_send_mail'] ))
                print ("Status send to %s (%s) : True"  %(r['receive'], r['id_send_mail'] ))
            else:
                self.engine.execute( self.queryupdatestatus, {'status':'W', 'senddate':None, 'id':r['id_send_mail']    }   )
                #log.info("Status send to %s (%s) : False"  %(r['receive'], r['id_send_mail'] ))
                print ("Status send to %s (%s) : False"  %(r['receive'], r['id_send_mail'] ))
            del r
        
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
            msg['Date'] = time.asctime()
            part1 = MIMEText(self.mailContent, 'html', "utf-8");
            msg.attach(part1)
            
           
            #server = smtplib.SMTP_SSL(host=self.SMTP_SERVER,port=self.SMTP_PORT) 
            server = smtplib.SMTP(host=self.SMTP_SERVER,port=self.SMTP_PORT)
            server.set_debuglevel(False)
            #server.ehlo()
            server.starttls()
            server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            server.sendmail(self.SMTP_USER, [self.mailTo], msg.as_string())            
            
            
            server.quit();
            return True
            
        except Exception as e:
            #log.exception("error : %s" %str(e));
            print ("error : %s" %str(e));
            return False
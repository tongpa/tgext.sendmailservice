
import threading;
#from email.MIMEMultipart import MIMEMultipart
#from email.MIMEText import MIMEText 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        self.SMTP = []
        self.sendMail = SendMail
        self.sqlConfig = config['sqlalchemy.url'] ;
        self.engine = create_engine(self.sqlConfig,                                    
                       pool_size=20, max_overflow=0);  
        
        self.querymail = text("select * from sur_send_mail where status='W'")
        self.queryupdatestatus = text("update sur_send_mail set status=:status , sended_date=:senddate where id_send_mail=:id")
        self.emailtemplate = text("select description from sur_sys_environment where environment_key='EMAIL_TEMPLATE'")
        self.serverurl = text("select description from sur_sys_environment where environment_key='SERVER_URL'")
        
        self.query_report_sended = text("select * from sur_report_send_mail_date where active=1 and id_mail_service =:id and date_sended = CURRENT_DATE")
        self.update_report_current_messages = text("UPDATE sur_report_send_mail_date SET current_number_messages=(current_number_messages + 1) WHERE active=1 and date_sended = CURRENT_DATE AND id_mail_service =:id")
        self.insert_report_sended =text("INSERT INTO sur_report_send_mail_date (id_mail_service, date_sended, current_number_messages, limit_messages, create_date) VALUES (:id, CURRENT_DATE, :current_number, :limit_messages, UTC_TIMESTAMP)")
         
        self.query_smtp_config = text("select * from sur_sys_mail_service where active = 1 ORDER BY 'order';")
        
        
        self.urltemplate = "http://{0}/images/imagermc/{1}"
        
        init_model(self.engine)
        
        self.template = self.__template__()
        self.url = self.__serverurl__()
        
        #self.__getSMTP__()
        
 
        
        
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
    
    def __getSMTP__(self):
        if len(self.SMTP) == 0:
            print "smtp is zero"
            result = self.engine.execute(self.query_smtp_config)
            for r in result:
                self.SMTP.append(r)
                del r
            result.close()
            del result
        
    
    def __updateReportSendMail__(self,smtps):
        self.id_mail = 1
        self.limit_messages = 8000
        if smtps :
            self.id_mail = smtps.id_mail_service
            self.limit_messages = smtps.max_messages_per_day
        result  = self.engine.execute( self.query_report_sended,{'id':self.id_mail} )
        if result.rowcount == 0:
            self.engine.execute( self.insert_report_sended,{'id': self.id_mail, 'current_number' :1, 'limit_messages': self.limit_messages} )
        else:
            self.engine.execute( self.update_report_current_messages,{'id':1} )
        result.close()
        del result
    
    def __setSendMail(self,result):
        data = []
        for r in result:
            self.engine.execute( self.queryupdatestatus, {'status':'S', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
            data.append(r)
        transaction.commit()    
        result.close()
        return data
    
    def __checkSMTP(self,smtps):
        if smtps and len(smtps) > 0:
            return smtps[0]
        return None
    
    def sendmailWithSMTP(self,smtps):
        if smtps:
            
            conn  = self.engine.connect()
            result  = self.engine.execute(self.querymail)
            template = self.template
            result = self.__setSendMail(result)
            #print "sendMail : %s" %(len(result))
            
            smtp = self.__checkSMTP(smtps)
            for r in result:
                self.email_content = {}
                self.email_content['email_content'] = r['content']
                self.email_content['url_check'] = self.urltemplate.format(self.url, r['gen_code'])
                
                template = self.template
            
                for k,v in  self.email_content.iteritems():
                    template = template.replace('[%s]' % k,v)
                
                
                
                sendMailUser = SendMailUser(r['sender_name'],r['receive'],r['subject'], template,smtps=smtp )
                if( sendMailUser.sendToUser() ) :
                    self.engine.execute( self.queryupdatestatus, {'status':'F', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
                    #log.info("Status send to %s (%s) : True"  %(r['receive'] , r['id_send_mail'] ))
                    
                    self.__updateReportSendMail__(smtps=smtp);
                    
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
            del smtp
            self.engine.dispose()
        else:
            print "not config smtp server in database"
        
        
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
            
            
            
            sendMailUser = SendMailUser(r['sender_name'],r['receive'],r['subject'], template,smtps=None )
            if( sendMailUser.sendToUser() ) :
                self.engine.execute( self.queryupdatestatus, {'status':'F', 'senddate':datetime.now(), 'id':r['id_send_mail']    }   )
                #log.info("Status send to %s (%s) : True"  %(r['receive'] , r['id_send_mail'] ))
                
                self.__updateReportSendMail__();
                
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
    def __init__(self,mailFrom, mailTo,mailSubject, mailContent, smtps):
        threading.Thread.__init__(self);
        self.sendType =0;
        if smtps :
            print smtps
            self.SMTP_SERVER = smtps.smtp_server
            self.SMTP_PORT= smtps.smtp_port
            self.SMTP_USER = smtps.smtp_user
            self.SMTP_PASSWORD = smtps.smtp_password
            self.ISEHLO = smtps.is_ehlo
            self.ISTLS = smtps.is_tls
            self.DEBUGLEVEL = smtps.debuglevel
            self.MAX_PER_DAY  = smtps.max_messages_per_day
        
        else:
            
            self.SMTP_SERVER = config['smtp_server'] ;
            self.SMTP_PORT= config['smtp_port'] ;
            self.SMTP_USER = config['smtp_user'] ;
            self.SMTP_PASSWORD = config['smtp_password'] ;  
            self.ISEHLO = 1
            self.ISTLS = 1
            self.DEBUGLEVEL = 0
            self.MAX_PER_DAY  = 90000
        
        #self.emailTemplate = SystemEnvironment.getEmailTemplate()   
        self.mailFrom = mailFrom
        self.mailTo = mailTo
        self.mailSubject = mailSubject
        self.mailContent = mailContent
    
    def run(self):
        self.sendToUser();
    
    
    
    def sendToUser_new(self):        
           
        try:
            
            server = smtplib.SMTP(host=self.SMTP_SERVER,port=self.SMTP_PORT)
            server.set_debuglevel(0)
            print server.ehlo()
            print server.starttls()
            
            text = "Hi!\nHow are you?\nHere is the link you wanted:\n smtp"
            
            print "user %s password %s " %(self.SMTP_USER, self.SMTP_PASSWORD)
            

            print server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            
            msg_a = MIMEMultipart('alternative')
            #msg = msg.format(sender, t, subject, date, body )
            msg_a['From'] = "Pollsurfvey Teams <%s>" %(self.SMTP_USER)  
            msg_a['To'] = self.mailTo
            msg_a['Subject'] = self.mailSubject
            msg_a['Date'] = datetime.now().strftime( "%d/%m/%Y %H:%M" )
        
            part1 = MIMEText(text, 'plain' , "utf-8")
            part2 = MIMEText(self.mailContent, 'html' , "utf-8")
        
            msg_a.attach(part1)
            msg_a.attach(part2)
        
            
            print server.sendmail(self.SMTP_USER, self.mailTo , msg_a.as_string())
            
            server.quit()    
            return True
            
        except Exception as e:
            #log.exception("error : %s" %str(e));
            print ("error : %s" %str(e));
            return False
        
    
    def sendToUser(self):
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.mailSubject
            msg['From'] = "%s <%s>" %("Pollsurfvey Teams" , self.SMTP_USER) #self.mailFrom
            msg['To'] = self.mailTo
            msg['Date'] = datetime.now().strftime( "%d/%m/%Y %H:%M" )
            
  
            part1 = MIMEText(self.mailContent, 'html', "utf-8")
            #part2 = MIMEText("sample", 'plain' , "utf-8")
            
            msg.attach(part1)
            #msg.attach(part2)
           
            #server = smtplib.SMTP_SSL(host=self.SMTP_SERVER,port=self.SMTP_PORT) 
            server = smtplib.SMTP(host=self.SMTP_SERVER,port=self.SMTP_PORT)
            server.set_debuglevel(self.DEBUGLEVEL)
            if self.ISEHLO:
                server.ehlo()
            if self.ISTLS:
                server.starttls()
            server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            server.sendmail(self.SMTP_USER, self.mailTo, msg.as_string())            
            
            
            server.quit();
            return True
            
        except Exception as e:
            #log.exception("error : %s" %str(e));
            print ("error : %s" %str(e));
            return False
 
import logging;
import threading;
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText 
import smtplib
from tg.configuration import AppConfig, config
 
from tg import request

try:
    from pollandsurvey import model
except ImportError:
    from ad2targetweb import model

log = logging.getLogger(__name__);

#from  logsurvey import LogDBHandler;
from tgext.pylogservice import LogDBHandler;
__all__ = ['SendMailService'] 
class SendMailService(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self);
        self.sendType =0;
        self.SMTP_SERVER = config['smtp_server'] ;
        self.SMTP_PORT= config['smtp_port'] ;
        self.SMTP_USER = config['smtp_user'] ;
        self.SMTP_PASSWORD = config['smtp_password'] ;
        
        dh = LogDBHandler( config=config,request=request);        
        log.addHandler(dh)
        
    
    
    def run(self):
        if self.sendType == 1:
            self._forgotPassword();
        if self.sendType == 2:
            self._activateEmail();
        if self.sendType == 3: 
            self._sendVolunteer();
        if self.sendType == 4: 
            self._activateEmail();    
        pass;
    
    def sendActivate(self,email):
        self.email = email;
        self.sendType =2; 
        
    def sendForgotPassword(self,email):
        self.email = email;
        self.sendType =1;
       
    def sendreActivate(self,email):
        self.email = email;
        self.sendType =  4; 
       
    def _activateEmail(self):
        self.__sendEmailByTemplate();
               
    def _forgotPassword(self):
        self.__sendEmailByTemplate();
        
    def _sendVolunteer(self):
        
        try:
            print "send email";
             
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.email.get('subject');
            msg['From'] = self.email.get('from') + '<' +self.SMTP_USER +'>'; # 
            msg['To'] = self.email.get('email');
            #print "email : " ,self.email.get('from'); 
            
            part1 = MIMEText(self.template, 'html');
            msg.attach(part1)
            
            
            server = smtplib.SMTP(self.SMTP_SERVER,self.SMTP_PORT) 
            server.ehlo()
            server.starttls()
            server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            server.sendmail(self.SMTP_USER, [self.email.get('email')], msg.as_string())
            
            #print msg.as_string()
            server.close();
        except Exception as e:
            log.exception(str(e)); 
    
    
    def sentEmail(self,email,template):
        self.email = email
        self.template = template
        self.sendType = 3 
        
        self.start()
        
    
    def __sendEmailByTemplate(self):
        try:
            #print "send email";
            print self.sendType
            
            self.forgot_template = model.EmailTemplate.getTemplateBy(self.sendType);
            
            print self.forgot_template
            
            template = self.forgot_template.content_template;
            for k,v in  self.email.iteritems():
                template = template.replace('[%s]' % k,v)
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = self.forgot_template.subject;
            msg['From'] = self.forgot_template.sender+ '<' +self.SMTP_USER +'>';
            msg['To'] = self.email.get('email');
            
            part1 = MIMEText(template, 'html');
            msg.attach(part1)
            
            
            server = smtplib.SMTP(self.SMTP_SERVER,self.SMTP_PORT) 
            server.ehlo()
            server.starttls()
            server.login(self.SMTP_USER, self.SMTP_PASSWORD)
            server.sendmail(self.SMTP_USER, [self.email.get('email')], msg.as_string())
            
            
            
            server.close();
        except Exception as e:
            log.exception(e); 
    
        
        
        
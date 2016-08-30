import tgscheduler
from tg.configuration import milestones
from tgext.pluggable import app_model
from tg.configuration import AppConfig, config
from tg import request
from tgscheduler import start_scheduler
from tgscheduler.scheduler import add_interval_task

from sqlalchemy.ext.declarative import declarative_base
from tgext.pluggable import PluggableSession

from surveymodel import *
import transaction
DBSession = PluggableSession()
DeclarativeBase = declarative_base()
import logging;
log = logging.getLogger(__name__);
from tgext.pylogservice import LogDBHandler;
__all__ = ['MailScheduler', 'myThread'] 

from .sendmailscheduler import SendMailScheduler
from surveymodel import *

def start_task():
    tgscheduler.start_scheduler()
    mailScheduler = MailScheduler()
    tgscheduler.add_interval_task( action= mailScheduler.printTask, taskname="test1" , interval=5, initialdelay=20)

    
class MailScheduler(object):
    myCurrentThread = []
    lengThread = 1
    def __init__(self):
        dh = LogDBHandler( config=config,request=request);        
        log.addHandler(dh)
        
        self.threadid = 1
        log.info('init Thread')
        for num in range(0,self.lengThread):
            self.myCurrentThread.append(myThread(num, "Thread-"+str(num), (self.lengThread -1) ))
        

    def manageThread(self):
        for self.num in range(0,self.lengThread):
            if (not self.myCurrentThread[self.num].isAlive() ):
                self.myCurrentThread[self.num]  = myThread(self.num, "Thread-"+str(self.num), 1)
                return self.myCurrentThread[self.num]
        return None
    def printTask(self):
        
        self.cThread = self.manageThread();
        if(self.cThread is not None):
            log.info("Start current Thread %s" %self.cThread.getName())
            self.cThread.showThread() 
        
        

import threading
import time
exitFlag = 0
class myThread (threading.Thread):
    def __init__(self, threadID, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
    def run(self):
        print ("Start Thread %s" %self.name)
        log.info("Start Thread %s" %self.name)
        
        
        
        
        sendMailScheduler = SendMailScheduler()
        sendMailScheduler.sendmail()
        del sendMailScheduler
        log.info("Exiting Thread %s" %self.name)
        #transaction.commit()
        #DBSession.close()
        #DBSession.dispose()
    def showThread(self):
        self.start()
        
def print_time(threadName, delay, counter):
    while counter:
        if exitFlag:
            threadName.exit()
        time.sleep(delay)
        print "%s: %s: %s" % (threadName, counter, time.ctime(time.time()))
        counter -= 1

"""
def update_stocks():
    
    print 'Hello Update'
        

import tgscheduler
def start_tgscheduler():
    
    tgscheduler.start_scheduler()
    tgscheduler.add_interval_task( action= update_stocks, taskname="test1" , interval=5, initialdelay=5)

from tg.configuration import milestones
milestones.config_ready.register(start_tgscheduler)
"""
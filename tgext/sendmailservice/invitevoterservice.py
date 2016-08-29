import tgscheduler

#from tgscheduler import start_scheduler
#from tgscheduler.scheduler import add_interval_task
    
class SampleScheduler(object):
    def __init__(self):
        tgscheduler.start_scheduler()
        self.threadid = 1
        self.mythread = myThread(1, "Thread-"+str(self.threadid), 1)
        tgscheduler.add_interval_task( action= self.printTask, taskname="test1" , interval=5, initialdelay=2)
        self.mythread.showThread()
        
    
    def printTask(self):
        
        print "is alive : %s" %self.mythread.isAlive()
        if (not self.mythread.isAlive() ):
            print '*************************************'
            self.mythread = myThread(1, "Thread-"+str(self.threadid), 1)
            self.mythread.showThread()
            


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
        print "Starting " + self.name
        print_time(self.name, self.counter, 8)
        print "Exiting " + self.name

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
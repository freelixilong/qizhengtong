# code: UTF-8
# 
import logging  
import logging.handlers  
  
def getLogger(logFile = "spider.log", name= "info"):
    handler = logging.handlers.RotatingFileHandler(logFile, maxBytes = 1024*1024, backupCount = 5)   
    fmt = '%(asctime)s - %(filename)s:%(lineno)s - %(name)s - %(message)s'  
      
    formatter = logging.Formatter(fmt)  
    handler.setFormatter(formatter)    
      
    logger = logging.getLogger(name)  
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger  
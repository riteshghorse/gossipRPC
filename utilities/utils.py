"""
Author: Ritesh G

Methods to initialize the generation, return timestamp and difference in timestamp.
"""
import datetime

def getCurrentGeneration():
    h, m, s = str(datetime.datetime.now()).split(" ")[1].split('.')[0].split(':')
    return int(h) * 3600

def getTimeStamp():
    return str(datetime.datetime.now())


# doesn't cover milliseconds difference
def getDiffInSeconds(time1):
    date2 = datetime.datetime.now()
    date1 = datetime.datetime.strptime(time1, '%Y-%m-%d %H:%M:%S.%f')
    
    timedelta = date2 - date1
    return timedelta.seconds + (timedelta.microseconds)//1000000
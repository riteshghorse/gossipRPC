import datetime

def getCurrentGeneration():
    h, m, s = str(datetime.datetime.now()).split(" ")[1].split('.')[0].split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def getTimeStamp():
    return str(datetime.datetime.now()).split(" ")[1].split('.')[0]
    
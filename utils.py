import datetime

def getCurrentGeneration():
    h, m, s = str(datetime.datetime.now()).split(" ")[1].split('.')[0].split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def getTimeStamp():
    return datetime.datetime.now()


# doesn't cover milliseconds difference
def getDiffInSeconds(time1):
    
    date2 = datetime.datetime.now()
    # date1 = datetime.datetime.strptime(time1, '%Y-%m-%d %H:%M:%S.%f')
    timedelta = date2 - time1
    # diff = timedelta.days * 24 * 3600 + timedelta.seconds + timedelta.microseconds
    print(timedelta)
    return timedelta.seconds + (timedelta.microseconds)//1000000
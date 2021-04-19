import datetime


def getCurrentGeneration():
    h, m, s = str(datetime.datetime.now()).split(" ")[1].split(".")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + int(s)


def getTimeStamp():
    return str(datetime.datetime.now())


# doesn't cover milliseconds difference
def getDiffInSeconds(time1):

    date2 = datetime.datetime.now()
    date1 = datetime.datetime.strptime(time1, "%Y-%m-%d %H:%M:%S.%f")
    # print('**************************************')
    # print(type(time1), type(date2))
    # print(time1, date2)

    # print('**************************************')
    # date1 = time1
    # if(str(type(time1)) != "<class 'datetime.datetime'>"):
    # date1 = datetime.datetime.strptime(str(time1), '%Y%m%dT%H:%M:%S.%f')
    timedelta = date2 - date1
    # diff = timedelta.days * 24 * 3600 + timedelta.seconds + timedelta.microseconds
    # print(timedelta)
    return timedelta.seconds + (timedelta.microseconds) // 1000000

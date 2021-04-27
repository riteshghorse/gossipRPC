import json


def getTimeStamp():
    return 1


f = open('us.json', 'r')

data = json.load(f)

for k,v in data['node1:5000'].items():
    print(k, v)
    print('\n\n')

f.close()


# "last_updated_time": "\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}.\d{6}"
import json

with open('settings.json', 'r') as settings:
    data=settings.read()


    obj = json.loads(data)

print(str(obj))
print(str(obj['settings']['temp']))
print(str(obj['settings']['temp']['max']))

from lib.bruntapi import BruntAPI
import json

def main():
    """ """ 
    creds=json.loads(open("creds.json").read())
    bapi = BruntAPI()
    print("Calling Brunt")
    bapi.login(creds['username'], creds['password'])
    print("    Logged in, gettings things.")
    things = bapi.getThings()
    print(f"    { len(things) } thing(s) found.")
    state = bapi.getState('Blind')
    print(f"    Current status of { state['NAME'] } is position { state['currentPosition'] }")
    newPos = 100
    if int(state['currentPosition']) == 100:
        newPos = 90
    print(f"    Setting { state['NAME'] } to position { newPos }")
    res = bapi.changePosition('Blind', newPos)
    print('    Success!' if res else '    Fail!')
    
if __name__ == '__main__':
    main()
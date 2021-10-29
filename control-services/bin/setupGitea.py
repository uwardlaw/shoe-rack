#!/usr/bin/env python3
import requests
import json
import time
import getpass
import os
import pprint

# Checks the status code from the html request and exits
#   the program if the operation was not successful
def checkStatus(response):
    # Debugging tool
    # print()
    # print(vars(response))
    # print()
    if response.status_code >= 200 and response.status_code <= 206:
        return
    else:
        print("Operation returned non success status: " + str(response.status_code))
        pprint.pprint(vars(response))
    exit()

# Most items are given a name when created, but
#  need to specified by ID when used to create other items
#  This function looks up an item by its name and returns
#  the ID
def getIDFromName(s, url, key, name):
    response = s.get(url=url)
    # This is great if you need to view every piece of the response
    #   when debugging
    # print()
    # pprint.pprint(vars(response))
    # print()

    reply = json.loads(response.text)

    #pprint.pprint(dict)

    if isinstance(reply, list):
        for item in reply:
            if item[key] == name:
                print("Found ID: " + str(item["id"]))
                return item["id"]
    elif isinstance(reply, dict):
        if reply.get(key) == name:
            print("Found ID: " + str(reply["id"]))
            return reply["id"]

    print("ID not found")
    return None

def main():
    ### CONFIGURATION ITEMS ###

    # The gitea host URL
    host = "http://localhost:3000/api/v1"

    # The local filepath for ROUS in the Gitea container
    configurationRepositoryPath = "/data/git/rous"
    configurationRepositoryName = "rous"

    # User for configurations and administration
    configurationUser = "config"
    passwd = ''
    organizationName = "333TRS"

    ### TOP LEVEL VARIABLES ###
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    s = requests.Session()
    s.headers.update(headers)
    sessionToken = ""
    cleanSessionToken = False

    print("-----GITEA CONFIGURATION")

    # Check to see if the configuration user exists
    stream = os.popen("sudo docker exec -it gitea su git bash -c"       + \
                      "\"gitea admin user list "                        + \
                      "| grep " + configurationUser                     + \
                      "| tr -s ' ' "                                    + \
                      "| cut -d ' ' -f 2\"")

    user = stream.read().strip()

    print("---LOGGING IN")

    # If the user does not exist, create them
    if user != configurationUser:
        print("---CREATING " + configurationUser + " USER")
        passwd = getpass.getpass(prompt="Password: ")

        os.system("sudo docker exec -it gitea su git bash -c"              + \
                  " \"gitea admin user create --admin"                     + \
                  " --username " + configurationUser                       + \
                  " --email fake@a.com"                                    + \
                  " --password " + passwd                                  + \
                  " --must-change-password=false\"")

        s.auth = (configurationUser, passwd)

    # If the user does exist, query for a token to confirm login
    else:
        print("---FOUND " + configurationUser + " USER")
        splitHost = host.split("//")
        api = "/users/" + configurationUser + "/tokens"

        while True:
            passwd = getpass.getpass(prompt="Password: ")

            s.auth = (configurationUser, passwd)
            response = s.get(url=host+api)

            # If a 200 was not received, something other than authentication happened
            if response.status_code == 200:
                break

    api = "/users/" + configurationUser + "/tokens"

    tokenID = getIDFromName(s=s, url=host+api, key="name", name="configurationToken")

    if tokenID != None:
        print("---REVOKING OLD TOKEN")

        api = "/users/" + configurationUser + "/tokens/" + str(tokenID)
        response = s.delete(url=host+api)
        checkStatus(response)

    print("---CREATING TOKEN")

    api = "/users/" + configurationUser + "/tokens"
    data = '{"name": "configurationToken"}'
    print(data)

    response = s.post(url=host+api, data=data)
    checkStatus(response)

    sessionToken = json.loads(response.text)["sha1"]
    print(sessionToken)

    tokenID = getIDFromName(s=s, url=host+api, key="name", name="configurationToken")

    token = 'Token ' + sessionToken
    s.headers.update({'Authorization': 'Token {sessionToken}'})


    print("---CREATING 333TRS ORGANIZATION")

    api = "/orgs"
    data =  '{'                              +\
            '"username": "333TRS"'           +\
            '}'
    print(data)

    orgID = getIDFromName(s=s, url=host+api, key="username", name="333TRS")
    if orgID == None:
        response = s.post(url=host+api, data=data)
        checkStatus(response)

    print("---CREATING ROUS REPOSITORY ")

    api = "/repos/" + organizationName + "/" + configurationRepositoryName

    repoID = getIDFromName(s=s, url=host+api, key="name", name=configurationRepositoryName)
    if repoID == None:
        api = "/repos/migrate"
        data = '{ "clone_addr": "' + configurationRepositoryPath + '", ' + \
               '"private": false, '                                      + \
               '"repo_name": "rous", '                                   + \
               '"repo_owner": "333TRS" }'
        print(data)

        response = s.post(url=host+api, data=data)
        checkStatus(response)


    ### TESTING - TRY TO CHANGE DEFAULT BRANCH NAME

#    api = "/repos/" + organizationName + "/" + configurationRepositoryName

#    data = '{"default_branch": "master"}'
#    print(data)

#    response = s.patch(url=host+api, data=data)
#    pprint.pprint(vars(response))
#    checkStatus(response)

    ### TESTING - REMOVE ME BEFORE COMMIT ###

#    print("ROUS RESPONSE")
#    api = "/repos/" + organizationName + "/rous"
#    response = s.get(url=host+api)
#    response = json.loads(response.text)
#    pprint.pprint(response)

#    print("TEST2 RESPONSE")
#    api = "/repos/" + organizationName + "/test2"
#    response = s.get(url=host+api)
#    response = json.loads(response.text)
#    pprint.pprint(response)

    ### END TESTING ###


    print("---REVOKING TOKEN")

    api = "/users/" + configurationUser + "/tokens/" + str(tokenID)

    response = s.delete(url=host+api)
    checkStatus(response)

if __name__ == "__main__":
    main()

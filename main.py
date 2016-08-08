from flask import Flask, flash, redirect, render_template, request, session, abort
import os
import json
import requests
import re

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

def getAppDetails(envs):
    appDetails = getCuratedAppDetails(envs)
    retDict = {}
    names = []
    counts = []
    appCpus = []
    appMem = []
    totalTasks = 0
    for item in ['tasks', 'apps', 'cpus', 'mem']:
        dictItem = {}
        names = []
        values = []
        totalValue = 0
        for team, value in appDetails[item].items():
            names.append(team)
            values.append(value)
            totalValue += value
        dictItem['name'] = names
        dictItem['data'] = values
        dictItem['total'] = totalValue
        retDict[item] = dictItem

    retDict['tasks']['title'] = '{} tasks are running on RogerOS ({})...'.format(retDict['tasks']['total'], '+'.join(envs))
    retDict['apps']['title'] = '...which are instances of {} applicatons.'.format(retDict['apps']['total'])
    retDict['cpus']['title'] = '{} cores (cpus) are currently allocated to them...'.format(retDict['cpus']['total'])
    retDict['mem']['title'] = ' ...along with a total of {} mb of memory.'.format(retDict['mem']['total'])
    retDict['tasks']['headers'] = ['name', 'count']
    retDict['apps']['headers'] = ['name', 'count']
    retDict['cpus']['headers'] = ['name', 'allocation']
    retDict['mem']['headers'] = ['name', 'allocation']


    return retDict

def getTeamNamesDict():
    return json.loads(os.environ['TEAMS'])

def getCuratedAppDetails(envs):
    teamNames = getTeamNamesDict()
    tasks = {}
    apps = {}
    cpus = {}
    mem = {}
    for env in envs:
        rawData = getRawAppDetails(env)
        for id, (running, cpusAlloc, memAlloc) in rawData.items():
            team = 'others'
            for team_name, patterns in teamNames.items():
                if isMatchingName(id, patterns):
                        team = team_name
                        break
            if team in tasks:
                apps[team] += 1
                tasks[team] += running
                cpus[team] += cpusAlloc
                mem[team] += memAlloc
            else:
                apps[team] = 1
                tasks[team] = running
                cpus[team] = cpusAlloc
                mem[team] = memAlloc

    return { 'tasks':tasks, 'apps': apps, 'cpus':cpus, 'mem':mem }

def isMatchingName(name, patterns):
    for item in patterns:
        if item in name:
            return True
    return False

def getRawAppDetails(env):
    endpoints = json.loads(os.environ['MARATHON_ENDPOINTS'])
    url = endpoints[env] + '/v2/apps'
    resp = requests.get(url, auth=(os.environ['MARATHON_USER'], os.environ['MARATHON_PWD']))
    rdata = resp.json()
    apps = {}
    for app in rdata['apps']:
        apps [app['id']] = [ app['tasksRunning'], float(app['instances']) * app['cpus'], float(app['instances']) * app['mem'] ]
    return apps

@app.route("/")
def index():
    endpoints = json.loads(os.environ['MARATHON_ENDPOINTS'])
    envs = endpoints.keys()
    selectedEnvs = envs
    env = request.args.get('env')
    if env and env in envs:
        selectedEnvs = [env]
    apps = getAppDetails(selectedEnvs)
    return render_template('index.html',**locals())

if __name__ == "__main__":
    app.run(debug=os.getenv('DEBUG', ''))

import json
from datetime import datetime, date
from time import gmtime
import urllib.request
import urllib.error
import urllib.parse
import regex
import re
import os
import sys
import xmlrpc.client
import configparser
import base64

# function for reading settings from external file
def getConfigValue(key):
	config = configparser.ConfigParser(interpolation=None)
	try:
		config.read("config.ini")
		configDict = {
			"username": config['Settings']['username'],
			"password": config['Settings']['password']
		}
		return configDict.get(key)
	except KeyError as e:
		print("Error: Cannot read key '"+key+"' from file 'config.ini'")

#fetch usernam and password from ini file
username = getConfigValue("username")
password = getConfigValue("password")

#Frage gekündetes Mitglied ab
#username_input = input('Welcher Nutzer hat gekündigt: ')
username_input = "test"
if len(username_input) == 0:
	print('Invalid input. Exiting...')
	sys.exit(0)

# init xmlrpc stuff
wikiurl = "https://"+username+":"+password+"@mitgliederverwaltung.opennet-initiative.de/"
proxy = xmlrpc.client.ServerProxy(wikiurl + "?action=xmlrpc2", allow_none=True)
mc = xmlrpc.client.MultiCall(proxy)
# create a password manager
password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

try:
    pagename = 'TestPage'
    text = 'This is a line of text'
    mc.putPage(pagename, text)
    #mc.getAllPages()
    result = mc()
    for i in result:
        print(i)
except xmlrpc.client.Fault as err:
    print("A fault occurred")
    print("Fault code: %d" % err.faultCode)
    print("Fault string: %s" % err.faultString)

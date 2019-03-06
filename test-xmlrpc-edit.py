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
import ssl

# function for reading settings from external file
def getConfigValue(key):
	config = configparser.ConfigParser(interpolation=None)
	try:
		config.read("config.ini")
		configDict = {
			"certfile": config['Settings']['certfile'],
		        "keyfile": config['Settings']['keyfile'],
                        "password": config['Settings']['password']
		}
		return configDict.get(key)
	except KeyError as e:
		print("Error: Cannot read key '"+key+"' from file 'config.ini'")

#fetch cert, key and password from ini file
certfile = getConfigValue("certfile")
keyfile  = getConfigValue("keyfile")
password = getConfigValue("password")

#Frage gekündetes Mitglied ab
#username_input = input('Welcher Nutzer hat gekündigt: ')
username_input = "test"
if len(username_input) == 0:
	print('Invalid input. Exiting...')
	sys.exit(0)

# init xmlrpc stuff
sslcontext = ssl.SSLContext()
if len(keyfile) > 0 :
	sslcontext.load_cert_chain(certfile, password=password, keyfile=keyfile)
else:
	sslcontext.load_cert_chain(certfile, password=password)
wikiurl = "https://mitgliederverwaltung.opennet-initiative.de/"
proxy = xmlrpc.client.ServerProxy(wikiurl + "?action=xmlrpc2", allow_none=True, context=sslcontext)
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

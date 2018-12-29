#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Dieses Skript hilft dabei alle Mitgliedsanträge, welche bisher in einem Ordner liegen ins MoinMoin hochzuladen.
# Dieses Skript wird nur einmalig im Rahmen der DSGVO Kompatibilität benötigt.
# Ziel ist es, keinerlei personenbezogener Daten im git zu haben. Alle Daten sollen in MoinMoin liegen.
#

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

# get all active members
mc.getAllPages()
memberpages = mc()
# loop through all active members
memberpages = memberpages[0] #needed because structure seems to be nested in substructure
for member in memberpages:
	print("Member: "+member)
	#only handle member pages
	if member.startswith("Mitglieder/") == False:
		print(" No valid member page.")
		continue

	#does this member already has document as attachment?
	docs = mc.listAttachments()
	if (docs):
		print(" Attachments: "+str(docs))
		#skip user because there is already document
		continue
	#
	# How to search for a file if we do not know how the file is named?
	# We need to search for similar names. Use forname as start.
	#
	# extract forename
	m = regex.search(r'Mitglieder\/(.*?) ', member)
	forename = ''
	if (m):
		forename = m.group(1)
		print(" Forename: "+forename)
	#  ask for substring
	username_input = input(' Nach welchem Teilstring suchen ['+forename+']: ')
	if len(username_input) == 0:
		username_input = forename
		print(" Select default: "+forename)

	#  find all potential documents from Eintritt und Änderung
	rx = re.compile(r''+username_input+'')
	for path, dnames, fnames in os.walk('/home/leo/Documents/opennet/FinanzVorstand2017/on_verein_dokumente/Mitglieder'):
		r = []
		r.extend([os.path.join(path, x) for x in fnames if rx.search(x)])
		for f in r:
			#  select potential document
			yn = input(' Upload ' + str(f) + ' [n]: ')
			if yn == "y":
				text = open(f, 'rb+').read()
				data = xmlrpc.client.Binary(text)
				mc2 = xmlrpc.client.MultiCall(proxy)
				try:
					mc2.putAttachment(member, f, data)
					result = mc2()
					if result[0] == True:
						print(" Removing file.")
						os.remove(f)
				except xmlrpc.client.Fault as err:
					print("A fault occurred")
					print("Fault code: %d" % err.faultCode)
					print("Fault string: %s" % err.faultString)
			else:
				print(" Ignoring because user wants to.")

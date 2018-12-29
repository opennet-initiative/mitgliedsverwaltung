#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Dieses Skript findet alle Mitglieder, welche noch altes Bezahlungsmodell haben (Jx=10.00 Qy=15.00)
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

# init xmlrpc stuff
wikiurl = "https://"+username+":"+password+"@mitgliederverwaltung.opennet-initiative.de/"
proxy = xmlrpc.client.ServerProxy(wikiurl + "?action=xmlrpc2", allow_none=True)
# create a password manager
password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

# loop through all active members
memberpages = proxy.getAllPages()
for member in memberpages:
	print("Member: "+member)
	#only handle member pages
	if member.startswith("Mitglieder/") == False:
		print(" No valid member page.")
		continue

	#page = proxy.getPage(member)
	page = proxy.getPage('Mitglieder/Steven Trinks')
	#print("--------------------------------------------------")
	#print(page)
	#print("--------------------------------------------------")
	# search for "Beitragsmodell.*=15.00"
	res = page.find("=15.00")
	if res > -1:
		m = regex.search(r'Beitragsmodell:: (.*)', page)
		paymethod = ''
		if (m):
			paymethod = m.group(1)
			print(" Beitragsmodell: "+paymethod)

		m = regex.search(r'Beitragsmodell:: J.*?=.* Q(.*?)=15.00', page)
		qmonat = ''
		if (m):
			qmonat = m.group(1)
			print(" Quartal: "+qmonat)
			print(" Neues Beitragsmodell:: Q"+qmonat+"=17.50")

		m = regex.search(r'Vorname:: (.*?)\n', page)
		forename = m.group(1)
		print("  Vorname: " + forename)
		m = regex.search(r'E-Mail:: (.*?)\n', page)
		emailaddr = m.group(1)
		print("  Email: " + emailaddr)
		m = regex.search(r'MandatsID:: (.*?)\n', page)
		mandatsid = m.group(1)
		print("  MandatsID: " + mandatsid)


	exit(0) #debug

exit(0)

emailaddr =""
subj = "Opennet: Anpassung Beitragsmodell"
body = """ Hallo XXX,

derzeit zahlst du deinen Opennet Mitgliedsbeitrag noch in folgendem (alten) Rhythmus:
- jährlich 10,00€
- quartalsweise 15,00€ (derzeit QXXXXX)
Insgesamt sind das 70,00€ im Jahr.

Wir würden gern die Verwaltung vereinfachen und gleichzeitig den Mitgliedern Retoure-Gebühren sparen.
Hierfür wollen wir bei dir die Zahlweise auf alleinig quartalsweise ändern.
Somit würdest du zukünftig in folgendem Rhythmus zahlen:
- quartalsweise 17,50€ (im  QXXXXXXXX)

Der Gesamtbeitrag (70,00€) bleibt gleich. Hier ändert sich nichts. Lediglich der Rhythmus ändert sich von jährlich+quartalsweise nach quartalsweise.

Wenn es keinen Widersprich gibt, würde ich die Umstellung im XXXXXXXXX durchführen.

Vielen Danke,
Martin Garbe
Finanzvorstand, Mitgliederverwaltung
Opennet Initiative e.V.
"""

cmd = "thunderbird -compose \"subject='"+subj+"',to='"+emailaddr+"',body='"+body+"'\""
os.system(cmd)

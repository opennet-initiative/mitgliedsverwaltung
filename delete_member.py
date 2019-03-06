#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Dieses Skript hilft dem Mitgliederverwalter der Opennet Initiative e.V.
# beim Austritt von Vereinsmitgliedern
#

import json
from datetime import datetime, date
from time import gmtime
import time
import urllib.request
import urllib.error
import urllib.parse
import regex
import re
import os
import sys
import xmlrpc.client
import configparser
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
		print("Error: Cannot read key '"+key+"' from file 'config.ini'", file=sys.stderr)

#fetch cert, key and password from ini file
certfile = getConfigValue("certfile")
keyfile  = getConfigValue("keyfile")
password = getConfigValue("password")

#Frage gekündetes Mitglied ab
username_input = input('Welcher Nutzer hat gekündigt: ')
if len(username_input) == 0:
    print('Invalid input. Exiting...')
    sys.exit(0)

#
#Nutzer Seite finden
#
# init xmlrpc stuff
sslcontext = ssl.SSLContext()
if len(keyfile) > 0 :
	sslcontext.load_cert_chain(certfile, password=password, keyfile=keyfile)
else:
	sslcontext.load_cert_chain(certfile, password=password)
wikiurl = "https://mitgliederverwaltung.opennet-initiative.de/"
proxy = xmlrpc.client.ServerProxy(wikiurl + "?action=xmlrpc2", allow_none=True, context=sslcontext)

returned_users = [] #similar users
final_pagename = "" #found member
try:
    pagelist = proxy.getAllPages()
    #print(pagelist)

    user = ""
    for pagename in pagelist:
        #is this a "Mitglieder" page?
        if pagename.find('Mitglieder/') != -1:
            #cut prefix ()'Mitglieder/') in results
            user = pagename[11:]
        else:
            #skip this page
            continue

        if str.lower(user).find(str.lower(username_input)) != -1:
            print('Found similar user: ' + user)
            returned_users.append( pagename )

    if len(returned_users) > 1:
        print('Stoppe Skript weil mehrere Nutzer gefunden wurden. Bitte sei beim nächsten Start spezifischer.')
        sys.exit(1)
    elif len(returned_users) == 1:
        final_pagename = returned_users[0]
        #print("TMP set final_pagename: " + final_pagename)
    else:
        print('Keinen solchen Nutzer gefunden.')
        sys.exit(1)
except xmlrpc.client.Fault as err:
    print("A fault occurred")
    print("Fault code: %d" % err.faultCode)
    print("Fault string: %s" % err.faultString)
    sys.exit(1)


#
# Austrittsdatum angeben
#
cancel_date = input('Offizielles Austrittsdatum (YY-MM-DD): ')
if len(cancel_date) == 0:
    print('Invalid input. Exiting...')
    sys.exit(0)
try:
    enddate = datetime.strptime(cancel_date, "%y-%m-%d")
    today = datetime.today()
    delta = today - enddate
    #Plausibilitätsprüfung
    print("Kündigung war vor " + str(delta.days) + "Tagen.")
except Exception as e:
    print("Error checking date input. Please check Kündigungsdatum carefully later.")
input("\nPress enter to continue...\n")


#
# get user page
#
pagename = final_pagename #z.B. u'Mitglieder/Martin Garbe'
text = proxy.getPage(pagename)
print("=======Mitgliederdatenbank - alte Seite=========================\n" + text)
print()
print()


# Kündigungsdatum eintragen
text = re.sub('Austrittsdatum::', "Austrittsdatum:: 20" + cancel_date, text, re.M)
# Mitgliedschaftsstatus ändern
text = re.sub('Mitgliedschaft:.*?ja', "Mitgliedschaft:: nein", text, re.M)
# diverse Informationen löschen
text = re.sub('Mitgliedsart:.*?\n', "Mitgliedsart::\n", text, re.M)
text = re.sub('Kontoinhaber:.*?\n', "Kontoinhaber::\n", text, re.M)
text = re.sub('IBAN:.*?\n', "IBAN::\n", text, re.M)
text = re.sub('BIC:.*?\n', "BIC::\n", text, re.M)
text = re.sub('Zahlungsaussetzung:.*?\n', "Zahlungsaussetzung::\n", text, re.M)
text = re.sub('Bank:.*?\n', "Bank::\n", text, re.M)

quoted_name=urllib.parse.quote(pagename) #convert special characters for later usage in URL
print("=======Mitgliederdatenbank - neue Seite=========================")
print("=======https://mitgliederverwaltung.opennet-initiative.de/"+quoted_name+"?action=edit =====================")
print(text)
print("===============================================================")



#
#generiere Abschiedsmail
#
print("======Abschiedsemail========")
print("Öffne Email in Thunderbird für Abschied. TODO: ändere Absender in Thunderbird\n")

firstname = "VORNAME!!!!!!!!!!!!!!!!!"
m = regex.search(r'Vorname:: (.*?)\n', str(text))
if (m):
   firstname = m.group(1)
else:
    print("!!!!!!!!!!!!!!!!!!!!\nError when extracting 'Vorname'. Please check generated email carefully.\n!!!!!!!!!!!!!!!!!!!!!!!")
email = "EMAIL!!!!!!!!!!!!!!!!!!!!!"
m = regex.search(r'E-Mail:: (.*?)\n', str(text))
if (m):
   email = m.group(1)
else:
    print("!!!!!!!!!!!!!!!!!!!!\nError when extracting 'Email'. Please check generated email carefully.\n!!!!!!!!!!!!!!!!!!!!!!!!!!!")

subj = "Bestätigung des Austritts aus Opennet-Initiative e.V."
body = """Hallo """+firstname+""",

hiermit bestätige ich deinen Austritt aus der Opennet Initiative e.V.
Den Beitragseinzug, deinen Eintrag in unserer Mailing-Liste und deinen Eintrag in unserer Mitgliederliste habe ich gelöscht.

Vielen Dank für deine bisherige Unterstützung.

Martin Garbe
Mitgliederverwaltung
Opennet-Initiative e.V.
"""

cmd = "thunderbird -compose \"subject='"+subj+"',to='"+email+"',cc=vorstand@opennet-initiative.de,body='"+body+"'\""
os.system(cmd)

#
#aus Mailingliste austragen
#
print("======Mailingliste austragen==========")
print("https://list.opennet-initiative.de/mailman/admin/mitglieder/members/remove")
print(email)

#
#Zertifikatsrückruf generieren
#
print("\n======Zertifikat zurückrufen + AP Nr. im Wiki löschen lassen======")
m = regex.search(r'ID:: (.*?)\n', str(text))
if (m):
   mid = m.group(1)
else:
    print("!!!!!!!!!!!!!!!!!!!!\nError when extracting 'ID'. \n!!!!!!!!!!!!!!!!!!!!!!!")
    mid = "XX" #add default value so that email can be send nevertheless
m = regex.search(r'\n( Vorname::.*) Mitgliedschaft::', str(text), flags=regex.MULTILINE|regex.DOTALL)
if (m):
	userdata = m.group(1)
	subj = "Zertifikat revoken - Austritt aus Verein - ID: " + mid
	body = """ Hallo Admins,

die unten stehende Person ist ausgetreten. Könnt ihr bitte das Zertifikat der folgenden Personen zurückziehen?

""" + userdata + """

Vielen Danke,
Martin"""

	cmd = "thunderbird -compose \"subject='"+subj+"',to='admin@opennet-initiative.de',body='"+body+"'\""
	os.system(cmd)
	print("Suche AP Nr. in https://wiki.opennet-initiative.de/wiki/Opennet_Nodes")
	print("Öffne Email in Thunderbird für Abschied. TODO: ändere Absender in Thunderbird\n")

	#os.system('echo "' + m.group(1) + '" | xclip -sel clip')  #copy to clipboard
else:
    print("Error when extracting userdata.")

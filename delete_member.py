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
		print("Error: Cannot read key '"+key+"' from file 'config.ini'", file=sys.stderr)

#fetch usernam and password from ini file
username = getConfigValue("username")
password = getConfigValue("password")

#Frage gekündetes Mitglied ab
username_input = input('Welcher Nutzer hat gekündigt: ')
if len(username_input) == 0:
    print('Invalid input. Exiting...')
    sys.exit(0)

#
#suche mögliche URLs und zeige diese an
#
#TODO schreibe Webseitenzugriff unten auf xmlrpc um. Funktion: getAllPages()
#
# init xmlrpc stuff
wikiurl = "https://"+username+":"+password+"@mitgliederverwaltung.opennet-initiative.de/"
proxy = xmlrpc.client.ServerProxy(wikiurl + "?action=xmlrpc2", allow_none=True)
mc = xmlrpc.client.MultiCall(proxy)
# create a password manager
password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()

# Add the username and password.
username_input_esc = urllib.parse.quote(username_input) #convert characters for being URL compatible. Else URL will be invalid later.
# If we knew the realm, we could use it instead of None.
url = "https://mitgliederverwaltung.opennet-initiative.de/Mitglieder?action=fullsearch&context=180&titlesearch=Titles&value=" + username_input_esc
password_mgr.add_password(None, url, username, password)

handler = urllib.request.HTTPBasicAuthHandler(password_mgr)

# create "opener" (OpenerDirector instance)
opener = urllib.request.build_opener(handler)

# use the opener to fetch a URL
search_members = "" #gefundene Mitglieder in MitgliederDB
html = ""
userpageurl = ""
try:
    data = opener.open(url)
    html = data.read()

    #was the user webpage found or only a list of users?
    if '<ol start' in str(html):
        #found user list

        #extract html with result list
        m = re.search(r'<ol start(.*?)<\/ol>', str(html))
        if m == None:
            print('Error: no user found. Exiting...')
            sys.exit(0)
        html = m.group(1)
        #list all users found. then exit.
        for html_group in html.split("<li>"):
            m = re.search(r'href=\"/(.*?)\"', str(html_group))
            if m:
                print(urllib.parse.unquote(m.group(1)))
        print('Stoppe Skript weil mehrere Nutzer gefunden wurden. Bitte sei beim nächsten Start spezifischer.')
        sys.exit(1)
    else:
        userpageurl = data.geturl()
        username_input = data.geturl().replace("https://mitgliederverwaltung.opennet-initiative.de/","")
        username_input = urllib.parse.unquote(username_input)
        print('\nUser page found: ' + username_input + "\n")
except urllib.error.URLError as e:
    print("Error fetching website. "+e.reason)


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
pagename = username_input #z.B. u'Mitglieder/Martin Garbe'
mc.getPage(pagename)
result = mc()
raw = tuple(result)
text = raw[0]
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

cmd = "thunderbird -compose \"subject='"+subj+"',to='"+email+"',cc=vorstand@opennet-initiative.de.de,body='"+body+"'\""
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
m = regex.search(r'\n( Vorname::.*) Mitgliedschaft::', str(text), flags=regex.MULTILINE|regex.DOTALL)
if (m):
	userdata = m.group(1) + "20" + cancel_date
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

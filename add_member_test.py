#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Dieses Skript hilft dem Mitgliederverwalter der Opennet Initiative e.V.
# beim Hinzufügen neuer Vereinsmitglieder
#

import json
from datetime import date
from time import gmtime
import urllib.request
import urllib.error
import urllib.parse
import urllib3
import re
import os
import configparser

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

print("Bitte kopiere das JSON vom Mitgliedsantrag hier rein. Danach drücke (2x) Enter (eine leere Zeile beendet die Eingabe).")
sentinel = '' # ends when this string is seen
json_string = '\n'.join(iter(input, sentinel))

#file = open("input.json","r")
#json_string = file.read()
parsed_json = json.loads(json_string)

rtime = gmtime(parsed_json["upload_timestamp"])
rdate = date.fromtimestamp( parsed_json["upload_timestamp"] ) #registered date
rdateiso = rdate.isoformat()

today = date.today()
datetoday = today.isoformat()

membertype = {
  "full": "ordentlich",
  "active": "aktiv",
  "sponsor": "fördern"
}

money = "" #how much money has to be paid per year/quarter
if parsed_json["membership"] == "full":
  beitr_model = "J" + str(today.month) + "=10.00"
  money = "10,00"
elif parsed_json["payment"] == "yearly":
  beitr_model = "J" + str(today.month) + "=70.00"
  money = "70,00"
elif parsed_json["payment"] == "quarterly":
  relmonth = today.month % 3  #jan(1),feb(2),mae(0),apr(1),...
  if relmonth == 0:
    relmonth += 3    #jan(1),feb(2),mae(3),apr(1),...
  beitr_model = "Q" + str(relmonth) + "=17.50"
  money = "17,50"
elif parsed_json["membership"] == "sponsor":
  beitr_model = "J" + str(today.month) + "=" + parsed_json["sponsorfee"]
  money = parsed_json["sponsorfee"]
else:
  beitr_model = "error"

invest = ""
if len(parsed_json["investgrant"].strip()) > 0:
  invest = parsed_json["investgrant"]+"@"+str(rdate.year)+"-"+str(rdate.month)


# Add the username and password.
# If we knew the realm, we could use it instead of None.
url = "https://mitgliederverwaltung.opennet-initiative.de/Mitglieder"


http=urllib3.PoolManager(cert_file= certfile,cert_reqs='CERT_REQUIRED',key_file=keyfile)
result=http.request('GET',url);


# use the opener to fetch a URL
mi_id = "" #MitgliederID
ma_id = "" #MandatID
try:
  
  html =result.data 
  m = re.search(r'freie Mitglieds- und Mandats-ID: ([\d]+) / ([\d]+) ', str(html))
  if (m):
     mi_id = m.group(1)
     ma_id = m.group(2)
except urllib.error.URLError as e:
  print("Error fetching website. "+e.reason)

quoted_name=urllib.parse.quote(parsed_json["firstname"] + " " + parsed_json["lastname"]) #convert special characters for later usage in URL
template = """
=======Mitgliederdatenbank - neue Seite=========================
=======https://mitgliederverwaltung.opennet-initiative.de/Mitglieder/"""+quoted_name+"""?action=edit&backto=Mitglieder&template=MitgliederTemplate =====================
<<TableOfContents()>>

= Mitglied =
 ID:: """+mi_id+"""
 Vorname:: """+parsed_json["firstname"]+"""
 Nachname:: """+parsed_json["lastname"]+"""
 StrasseNr:: """+parsed_json["street"]+" "+parsed_json["housenumber"]+"""
 PLZ:: """+parsed_json["zip"]+"""
 Ort:: """+parsed_json["place"]+"""
 E-Mail:: """+parsed_json["mail"]+"""
 Eintrittsdatum:: """+rdateiso+"""
 Austrittsdatum::
 Mitgliedschaft:: ja
 Mitgliedsart:: """+membertype.get(parsed_json["membership"],"unknown")+"""
 Kontoinhaber:: """+parsed_json["accountholder"]+"""
 IBAN:: """+parsed_json["iban"]+"""
 BIC::
 MandatsID:: """+ma_id+"""
 Mandatsdatum:: """+rdateiso+"""
 Beitragsmodell:: """+beitr_model+"""
 Investitionskostenzuschuss:: """+invest+"""
 Zahlungsaussetzung:: nein
 AP-Nr:: """+parsed_json["opennetid"]+"""
 Offene Aufgaben::

= Verlauf =


= Lastschriftvorlage =
<<OpennetLastschrift()>>


= Anhänge =
 * [[attachment:Aufnahmeantrag.pdf|Aufnahmeantrag]]
<<AttachInfo()>>
"""

print(template)

print("""
===========Unterschriebener Antrag===========================
Den unterschriebenen Antrag hochladen.


""")

beitragseinzug = ""
if beitr_model[0] == "J":
    beitragseinzug = money + " jährlich im " + today.strftime("%b")
elif beitr_model[0] == "Q":
    beitragseinzug = money + " quartalsweise beginnend im " + today.strftime("%b")

subj = "Willkommen bei Opennet"
body = """Hallo """+parsed_json["firstname"]+""",

seit heute bist du offiziell Mitglied des Opennet-Initiative e.V.

Wir wünschen dir viel Spaß in unserem Netzwerk. Komm gern zu unseren
Montagstreffen in die Frieda23 (Raum 3.08) um unser Tun kennenzulernen
und mitzumachen.

Über Veranstaltungen wie die Jahresvollversammlung informieren wir dich
ein bis zwei Mal im Jahr per E-Mail. Ich habe dich dafür in unseren
Mitglieder-E-Mail-Verteiler eingetragen.

Deinen finanziellen Beitrag werden wir folgendermaßen von deinem Konto einziehen: """+beitragseinzug+"""

Deine MandatsID lautet: """+ma_id+"""

Martin Garbe
Mitgliederverwaltung
Opennet-Initiative e.V.
"""

cmd = "thunderbird -compose \"subject='"+subj+"',from=mitgliederverwaltung@opennet-initiative.de,to='"+parsed_json["mail"]+"',cc=vorstand@opennet-initiative.de,body='"+body+"'\""
print("======Begrüßungsemail========")
print("Öffne Email in Thunderbird für Begrüßung. TODO: ändere Absender in Thunderbird\n")
os.system(cmd)

#Hilfetext für Abbuchung InvestZuschuss per SEPA Basislastschrift
if len(parsed_json["investgrant"].strip()) > 0:
    print(
"""
======SEPA Basislastschrift für InvestZuschuss=======
Zahlungspflichtiger:  """+parsed_json["accountholder"]+"""
IBAN:                 """+parsed_json["iban"]+"""
Betrag:               """+parsed_json["investgrant"]+"""
Verwendungszweck:     Opennet Investitionskostenzuschuss Hardware
Fälligkeitsdatum:     """+str(today.day+2)+"."+str(today.month)+"."+str(today.year)+"""
Mandatsreferenz:      """+ma_id+"""
Unterschrieben am:    """+str(rdate.day)+"."+str(rdate.month)+"."+str(rdate.year)+"""
Ausführungsart:       einmalig
====================================

Aus Geräteverfolgung https://wiki.opennet-initiative.de/wiki/Ger%C3%A4teverfolgung austragen?

====================================
"""
    )

#
#in Mailingliste eintragen
#
print("======Mailingliste eintragen==========")
print("https://list.opennet-initiative.de/mailman/admin/mitglieder/members/add")
print(parsed_json["mail"])

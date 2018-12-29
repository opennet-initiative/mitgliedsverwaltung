#/bin/bash

ORIGTEXT="Retouren Retoure SEPA Lastschrift vo m 18.09.2018, Rueckgabegrun d: MS03 Rückgabegrund vom K reditinstitut nicht spezifi ziert SVWZ: RETURN/REFUND, Jahresbeitrag Opennet Initi ative e.V. ENTG: 2,95 EUR E ntgelt Rücklastschrift/Rück scheck IBAN: DE123456789111 23456789 BIC: DEUTDEDBROS; Max Muster"

#Goal: format text for copy&paste in LibreOffice
#
# example:
#Max Muster	18.09.18		nicht spez.		72.95	2.95	DE1234567891111 23456789 		J9=70.00	info@localhost.lan		Retouren Retoure SEPA Lastschrift vo m 18.09.2018, Rueckgabegrun d: MS03 Rückgabegrund vom K reditinstitut nicht spezifi ziert SVWZ: RETURN/REFUND, Jahresbeitrag Opennet Initi ative e.V. ENTG: 2,95 EUR E ntgelt Rücklastschrift/Rück scheck IBAN: DE123456789111 23456789 BIC: DEUTDEDBROS; Max Muster

#init variable
OUT=""

#name
ret=$(echo "$ORIGTEXT" | cut -d";" -f 2 | sed -e 's/^[[:space:]]*//')
echo $ret
OUT="$OUT$ret\t"

#date
ret=$(echo "$ORIGTEXT" | cut -d" " -f 7 | cut -d',' -f 1)
echo $ret
OUT="$OUT$ret\t"

#reserved for "Zahlungsaussetzung"
OUT="$OUT.\t"

#reason
ret=$(echo "$ORIGTEXT" | sed -n -r 's/.*(MS.*?)SVWZ.*/\1/p')
echo $ret
OUT="$OUT$ret\t"

OUT="$OUT.\t"

#RETOURE_REAL
ret="TODO get from Gnucash"
echo $ret
OUT="$OUT$ret\t"

#CHARGES
ret=$(echo "$ORIGTEXT" | sed -n -r 's/.*ENTG: (.*) EUR.*/\1/p')
echo $ret
OUT="$OUT$ret\t"

#IBAN
ret=$(echo "$ORIGTEXT" | sed -n -r 's/.*IBAN:.(.*).BIC.*/\1/p')
echo $ret
OUT="$OUT$ret\t"

#BIC
OUT="$OUT.\t"

#PAYMODE
ret="TODO get from wiki"
echo $ret
OUT="$OUT$ret\t"

#EMAIL
ret="TODO get from wiki"
echo $ret
OUT="$OUT$ret\t"

OUT="$OUT\t"

#ORIG_BANK_TEXT
ret="$ORIGTEXT"
echo $ret
OUT="$OUT$ret\t"

echo
echo "Result:"
echo $OUT

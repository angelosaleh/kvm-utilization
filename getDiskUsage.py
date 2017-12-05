#!/usr/bin/python

import commands

def get_df():
  diskuse = commands.getoutput("df -h")
  diskuse = diskuse.split("\n")

  trs=''
  
  rowcounter=1
  for disk in diskuse:
    trs+='<tr>'
    fields = disk.strip().split()
    internalrowcounter=0
    for infields in fields:
      if rowcounter == 1:
        if len(fields) == 7 and internalrowcounter == 5:
          trs+='<th>'+infields+' '+fields[6]+'</th>'
          break
        else:
          trs+='<th>'+infields+'</th>'
      else:
        trs+='<td>'+infields+'</td>'
      internalrowcounter += 1
    rowcounter += 1
    trs+='</tr>'
  print trs

get_df()

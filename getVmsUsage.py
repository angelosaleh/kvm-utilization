#!/usr/bin/python

import commands,re,xml.etree.ElementTree as ET

def get_df():
  diskuse = commands.getoutput("df -h")
  diskuse = diskuse.split("\n")

  trs = ''

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
  return '<div class="resourcesdiv"><h3>DISK USAGE</h3><table><tr><th colspan="6">df -- display free disk space</th></tr>'+trs+'</table></div>'

toppart = '<!doctype html><html><head><link rel="stylesheet" href="styles.css"><title>KVM utilizaion on '+commands.getoutput("hostname -s")+'</title></head><body>'
diskusetable = get_df()

indexf = open('index.html','w')
indexf.write(toppart)
indexf.write(diskusetable)

allocatedram = 0
installedram = commands.getoutput("dmidecode --type memory | awk '/Size/ {print $0}' | awk '/MB/ {print $2}'")
installedram = installedram.split("\n")
installedram = map(float, installedram)
installedram = sum(installedram)/1024
freeram=0
cpudetailtable=''
allocatedcpus = 0
installedcpus = commands.getoutput("lscpu | awk '/^CPU\(s\):/ {print $2}'")
freecpus=0
vms = commands.getoutput("virsh list --all")
vms = vms.split("\n")

counter=-1
for vmi in vms:
  counter += 1
  if counter < 2 or counter == len(vms)-1:
    continue
  vm = vmi.strip().split()
  vmxml = commands.getoutput("virsh dumpxml "+vm[1])
  vmxml = vmxml.split("\n")
  cpu = '<root>'
  for detailxml in vmxml:
    if re.search("memory", detailxml):
      memory = re.search('\d+', detailxml)
      allocatedram += float(memory.group(0))/1024/1024

    if re.search("cpu", detailxml):
      cpu += detailxml+'\n'

  cpu += '</root>'
  cpu = ET.fromstring(cpu)
  for vcpu in cpu.iter('vcpu'):
    if vcpu.attrib.has_key("current"):
      allocatedcpus += int(vcpu.attrib['current'])
    else:
      allocatedcpus += int(vcpu.text)

freeram = float(installedram - allocatedram)
freeram = '<td style="background-color: red;">'+str(freeram) if freeram < 0 else '<td>'+str(freeram)
freecpus = int(int(installedcpus) - allocatedcpus)
freecpus = '<td style="background-color: red;">'+str(freecpus) if freecpus < 0 else '<td>'+str(freecpus)

ramtable='<div class="resourcesdiv">'
ramtable+='<h3>RAM USAGE</h3>'
ramtable+='<canvas id="ramchart"></canvas>'
ramtable+='<table>'
ramtable+='<tr>'
ramtable+='<th>Installed</th>'
ramtable+='<th>Allocated</th>'
ramtable+='<th>Free</th>'
ramtable+='</tr>'
ramtable+='<tr>'
ramtable+='<td>'+str(installedram)+'G</td>'
ramtable+='<td>'+str(allocatedram)+'G</td>'
ramtable+=freeram+'G</td>'
ramtable+='</tr>'
ramtable+='</table>'
ramtable+='</div>'

cpudiv='<div class="resourcesdiv">'
cpudiv+='<h3>CPU USAGE</h3>'
cpudiv+='<table>'
cpudiv+='<tr>'
cpudiv+='<th>Total CPUs</th>'
cpudiv+='<th>Allocated</th>'
cpudiv+='<th>Free</th>'
cpudiv+='</tr>'
cpudiv+='<tr>'
cpudiv+='<td>'+installedcpus+'</td>'
cpudiv+='<td>'+str(allocatedcpus)+'</td>'
cpudiv+=freecpus+'</td>'
cpudiv+='</tr>'
cpudiv+='</table>'
cpudiv+=cpudetailtable
cpudiv+='</div>'

indexf.write(ramtable)
indexf.write(cpudiv)
indexf.write('</body></html>')
indexf.close()

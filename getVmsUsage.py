#!/usr/bin/python

import commands,re,xml.etree.ElementTree as ET

def get_df():
  diskuse = commands.getoutput("df -h")
  diskuse = diskuse.split("\n")
  trs = ''
  rowcounter=1
  for disk in diskuse:
    trs += '<tr>'
    fields = disk.strip().split()
    internalrowcounter=0
    for infields in fields:
      if rowcounter == 1:
        if len(fields) == 7 and internalrowcounter == 5:
          trs += '<th>' + infields + ' ' + fields[6] + '</th>'
          break
        else:
          trs += '<th>' + infields + '</th>'
      else:
        trs += '<td>' + infields + '</td>'
      internalrowcounter += 1
    rowcounter += 1
    trs += '</tr>'
  return '<div class="resourcesdiv"><h3>DISK USAGE</h3><table><tr><th colspan="6">df -- display free disk space</th></tr>' + trs + '</table></div>'

toppart = '<!doctype html><html><head><link rel="stylesheet" href="styles.css"><title>KVM utilizaion on ' + commands.getoutput("hostname -s") + '</title></head><body>'
diskusetable = get_df()

indexf = open(commands.getoutput("hostname -s") + '.html','w')
indexf.write(toppart)
indexf.write(diskusetable)

allocatedram = 0
installedram = commands.getoutput("dmidecode --type memory | awk '/Size/ {print $0}' | awk '/MB/ {print $2}'")
installedram = installedram.split("\n")
installedram = map(float, installedram)
installedram = sum(installedram)/1024
freeram = 0
cpupinningtable = ''
cpupthreadsiblinstable = ''
allocatedcpus = 0
installedcpus = commands.getoutput("lscpu | awk '/^CPU\(s\):/ {print $2}'")
numaconf = commands.getoutput("lscpu | awk '/^NUMA node\w CPU\(s\):/ {print $1,$2,$4}'")
freecpus = 0
cputune = {}
cpupinningusage = {}
vms = commands.getoutput("virsh list --all")
vms = vms.split("\n")
allvmsdets = ''
totaldiskusage = 0
allocatedmaxcpus = 0

cpupthreadsiblinstable = '<h3>Thread Siblings List</h3>'
cpupthreadsiblinstable += '<table>'
cpupthreadsiblinstable += '<tr>'
cpupinningtable = '<h3>CPU PINNING</h3>'
cpupinningtable += '<table>'
cpupinningtable += '<tr>'
socketkey = 0
numaconf = numaconf.split("\n")
for numanode in numaconf:
  numanode = numanode.split(" ")
  cputune[socketkey] = []
  if re.search("-", numanode[2]):
    numanode[2] = numanode[2].split("-")
    indexrangenumanode = int(numanode[2][0])
    lengthrangenumanode = int(numanode[2][1])
    numanode[2] = []
    while (indexrangenumanode <= lengthrangenumanode):
      numanode[2].append(indexrangenumanode)
      indexrangenumanode += 1
  else:
    numanode[2] = numanode[2].split(",")
  cputune[socketkey].append(numanode[0] + ' ' + numanode[1])
  cputune[socketkey].append(numanode[2])
  cpupinningtable += '<th>' + cputune[socketkey][0] + '</th>'
  cpupthreadsiblinstable += '<th>' + cputune[socketkey][0] + '</th>'
  socketkey += 1
cpupinningtable += '</tr>'
cpupthreadsiblinstable += '</tr>'

counter =- 1
for vmi in vms:
  counter += 1
  if counter < 2 or counter == len(vms)-1:
    continue
  vm = vmi.strip().split()
  vmxml = commands.getoutput("virsh dumpxml " + vm[1])
  allvmsdets += '<tr><td>' + vm[1] + '</td>'
  allvmsdets += '<td>' + vm[2] + '</td>'
  vmautostart = commands.getoutput("virsh list --autostart | grep -c " + vm[1])
  if int(vmautostart) > 0:
    allvmsdets += '<td>yes</td>'
  else:
    allvmsdets += '<td>no</td>'
  vmxml = vmxml.split("\n")
  cpu = '<root>'
  disk = '<root>'
  for detailxml in vmxml:
    if re.search("memory", detailxml):
      memory = re.search('\d+', detailxml)
      allocatedram += float(memory.group(0))/1024/1024
    if re.search("cpu", detailxml):
      cpu += detailxml + '\n'
    if re.search("disk|file", detailxml):
      disk += detailxml + '\n'
  cpu += '</root>'
  disk += '</root>'
  disks = ''
  diskssizes = ''
  cpu = ET.fromstring(cpu)
  disk = ET.fromstring(disk)
  for vcpu in cpu.iter('vcpu'):
    if vcpu.attrib.has_key("current"):
      allocatedcpus += int(vcpu.attrib['current'])
    else:
      allocatedcpus += int(vcpu.text)
  for vdisk in disk.iter('source'):
    if vdisk.attrib.has_key("file"):
      disks += vdisk.attrib['file'] + '<br>'
      diskssizes += commands.getoutput("du -sh " + vdisk.attrib['file'] + " | awk '{ print $1 }'") + '<br>'
  allvmsdets += '<td>' + diskssizes + '</td>'
  allvmsdets += '<td>' + disks + '</td>'
  allvmsdets += '<td>' + str(float(memory.group(0))/1024/1024) + 'G</td>'
  allvmsdets += '</tr>'
  for vcputune in cpu.iter('cputune'):
    for vcpupin in vcputune:
      cpupinning = vcpupin.attrib['cpuset'].split(",")
      for physicalcpupinning in cpupinning:
        for numaindex in range(len(cputune)):
          if physicalcpupinning in cputune[numaindex][1]:
            if cpupinningusage.has_key(physicalcpupinning):
              if not re.search(vm[1], cpupinningusage[physicalcpupinning]):
                cpupinningusage[physicalcpupinning] = cpupinningusage[physicalcpupinning] + '<br>' + vm[1]
            else:
              cpupinningusage[physicalcpupinning] = vm[1]

if len(cpupinningusage) > 0:
  numaindex1 = 0
  while (numaindex1 < len(cputune[0][1])):
    cpupinningtable += '<tr>'
    cpupthreadsiblinstable += '<tr>'
    numacpupinning = ''
    numaindex2 = 0
    while (numaindex2 < len(cputune)):
      cpupinningtable += '<th>' + str(cputune[numaindex2][1][numaindex1]) + '</th>'
      if cpupinningusage.has_key(cputune[numaindex2][1][numaindex1]):
        numacpupinning += '<td>' + cpupinningusage[cputune[numaindex2][1][numaindex1]] + '</td>'
      else:
        numacpupinning +=  '<td></td>'
      threadsibling = commands.getoutput("cat /sys/devices/system/cpu/cpu" + str(cputune[numaindex2][1][numaindex1]) + "/topology/thread_siblings_list")
      if threadsibling.isdigit():
        cpupthreadsiblinstable += '<td>' + threadsibling + '</td>'
      elif not re.search(threadsibling, cpupthreadsiblinstable):
          cpupthreadsiblinstable += '<td>' + threadsibling + '</td>'
      numaindex2 += 1
    cpupinningtable += '</tr>'
    cpupinningtable += '<tr>' + numacpupinning + '</tr>'
    cpupthreadsiblinstable += '</tr>'
    numaindex1 += 1
  cpupinningtable += '</table>'
  cpupthreadsiblinstable += '</table>'
else:
  cpupinningtable = ''
  numaindex1 = 0
  while (numaindex1 < len(cputune[0][1])):
    cpupthreadsiblinstable += '<tr>'
    numaindex2 = 0
    while (numaindex2 < len(cputune)):
      threadsibling = commands.getoutput("cat /sys/devices/system/cpu/cpu" + str(cputune[numaindex2][1][numaindex1]) + "/topology/thread_siblings_list")
      if threadsibling.isdigit():
        cpupthreadsiblinstable += '<td>' + threadsibling + '</td>'
      elif not re.search(threadsibling, cpupthreadsiblinstable):
          cpupthreadsiblinstable += '<td>' + threadsibling + '</td>'
      numaindex2 += 1
    cpupthreadsiblinstable += '</tr>'
    numaindex1 += 1
  cpupthreadsiblinstable += '</table>'

freeram = float(installedram - allocatedram)
freeram = '<td style="background-color: red;">' + str(freeram) if freeram < 0 else '<td>' + str(freeram)
freecpus = int(int(installedcpus) - allocatedcpus)
freecpus = '<td style="background-color: red;">' + str(freecpus) if freecpus < 0 else '<td>' + str(freecpus)

ramtable = '<div class="resourcesdiv">'
ramtable += '<h3>RAM USAGE</h3>'
ramtable += '<canvas id="ramchart"></canvas>'
ramtable += '<table>'
ramtable += '<tr>'
ramtable += '<th>Installed</th>'
ramtable += '<th>Allocated</th>'
ramtable += '<th>Free</th>'
ramtable += '</tr>'
ramtable += '<tr>'
ramtable += '<td>' + str(installedram) + 'G</td>'
ramtable += '<td>' + str(allocatedram) + 'G</td>'
ramtable += freeram + 'G</td>'
ramtable += '</tr>'
ramtable += '</table>'
ramtable += '</div>'

cpudiv = '<div class="resourcesdiv">'
cpudiv += '<h3>CPU USAGE</h3>'
cpudiv += '<table>'
cpudiv += '<tr>'
cpudiv += '<th>Total CPUs</th>'
cpudiv += '<th>Allocated</th>'
cpudiv += '<th>Free</th>'
cpudiv += '</tr>'
cpudiv += '<tr>'
cpudiv += '<td>'+ installedcpus + '</td>'
cpudiv += '<td>'+ str(allocatedcpus) + '</td>'
cpudiv += freecpus + '</td>'
cpudiv += '</tr>'
cpudiv += '</table>'
cpudiv += cpupthreadsiblinstable
cpudiv += cpupinningtable
cpudiv += '</div>'

allvmsdiv = '<div class="resourcesdiv">'
allvmsdiv += '<h3>ALL VMS USAGE</h3>'
allvmsdiv += '<table>'
allvmsdiv += '<tr>'
allvmsdiv += '<th>VM Name</th>'
allvmsdiv += '<th>State</th>'
allvmsdiv += '<th>Autostart</th>'
allvmsdiv += '<th>Disk</th>'
allvmsdiv += '<th>Location</th>'
allvmsdiv += '<th>RAM</th>'
allvmsdiv += '<th>Current CPU</th>'
allvmsdiv += '<th>Max CPU</th>'
allvmsdiv += '</tr>'
allvmsdiv += allvmsdets
allvmsdiv += '<tr>'
allvmsdiv += '<th>Total</th>'
allvmsdiv += '<th></th>'
allvmsdiv += '<th></th>'
allvmsdiv += '<th>' + str(totaldiskusage) + 'G</th>'
allvmsdiv += '<th></th>'
allvmsdiv += '<th>' + str(allocatedram) + 'G</th>'
allvmsdiv += '<th>' + str(allocatedcpus) + '</th>'
allvmsdiv += '<th>' + str(allocatedmaxcpus) + '</th>'
allvmsdiv += '</tr>'
allvmsdiv += '</table>'
allvmsdiv += '</div>'

indexf.write(ramtable)
indexf.write(cpudiv)
indexf.write(allvmsdiv)
indexf.write('</body></html>')
indexf.close()

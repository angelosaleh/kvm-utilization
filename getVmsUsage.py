#!/usr/bin/python

import commands,re,xml.etree.ElementTree as ET

def get_df():
  diskuse = commands.getoutput("df -h")
  diskuse = diskuse.split("\n")
  trs = ''
  rowcounter = 1
  sametrflag = False
  for disk in diskuse:
    if not sametrflag:
      trs += '<tr>'
    else:
      sametrflag = False
    fields = disk.strip().split()
    if len(fields) == 1:
      trs += '<td>' + fields[0] + '</td>'
      sametrflag = True
      continue
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

hostname = commands.getoutput("hostname -s")
toppart = '<!doctype html><html><head><link rel="stylesheet" href="styles.css"><title>KVM utilizaion on ' + hostname + '</title></head><body>'
diskusetable = get_df()

indexf = open(hostname + '.html','w')
indexf.write(toppart)
indexf.write('<h2 class="maintitle" >kvm utilization on ' + hostname + ' as of ' + commands.getoutput("date") + '</h2>')
indexf.write(diskusetable)

allocatedram = 0
allocatedmaxram = 0
installedramMB = commands.getoutput("dmidecode --type memory | awk '/Size/ {print $0}' | awk '/MB/ {print $2}'")
installedramGB = commands.getoutput("dmidecode --type memory | awk '/Size/ {print $0}' | awk '/GB/ {print $2}'")
if installedramMB != '':
  installedramMB = installedramMB.split("\n")
  installedramMB = map(float, installedramMB)
  installedramMB = round(sum(installedramMB)/1024,1)
else:
  installedramMB = 0

if installedramGB != '':
  installedramGB = installedramGB.split("\n")
  installedramGB = map(float, installedramGB)
  installedramGB = round(sum(installedramGB),1)
else:
  installedramGB = 0

installedram = installedramMB + installedramGB
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
    cpuranges = numanode[2].split(",")
    numanode[2] = []
    for each_cpuranges in cpuranges:
      each_cpuranges = each_cpuranges.split("-")
      indexrangenumanode = int(each_cpuranges[0])
      lengthrangenumanode = int(each_cpuranges[1])
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
  if len(vm) > 3:
    allvmsdets += '<td>' + vm[2] + ' ' + vm[3] + '</td>'
  else:
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
    if re.search("currentMemory", detailxml):
      currentMemory = re.search('\d+', detailxml)
      allocatedram += float(currentMemory.group(0))/1024/1024
    if re.search("memory", detailxml):
      memory = re.search('\d+', detailxml)
      allocatedmaxram += float(memory.group(0))/1024/1024
    if re.search("cpu", detailxml):
      cpu += detailxml + '\n'
    if re.search("disk|source", detailxml):
      disk += detailxml + '\n'
  cpu += '</root>'
  disk += '</root>'
  disks = ''
  diskssizes = ''
  currentcpus = ''
  maxcpus = ''
  cpu = ET.fromstring(cpu)
  disk = ET.fromstring(disk)
  et_cpu_vcpu_iterator = ''
  et_cpu_cputune_iterator = ''
  et_disk_source_iterator = ''

  if hasattr(cpu, 'iter'):
    et_cpu_vcpu_iterator = cpu.iter('vcpu')
    et_cpu_cputune_iterator = cpu.iter('cputune')
    et_disk_source_iterator = disk.iter('source')
  else:
    et_cpu_vcpu_iterator = cpu.getiterator('vcpu')
    et_cpu_cputune_iterator = cpu.getiterator('cputune')
    et_disk_source_iterator = disk.getiterator('source')

  for vcpu in et_cpu_vcpu_iterator:
    if vcpu.attrib.has_key("current"):
      allocatedcpus += int(vcpu.attrib['current'])
      currentcpus = vcpu.attrib['current']
    else:
      allocatedcpus += int(vcpu.text)
    allocatedmaxcpus += int(vcpu.text)
    maxcpus = vcpu.text
    if not currentcpus:
      currentcpus = vcpu.text
  for vdisk in et_disk_source_iterator:
    if vdisk.attrib.has_key("file"):
      disks += vdisk.attrib['file'] + '<br>'
      sizeofimage = commands.getoutput("du " + vdisk.attrib['file'] + " | awk '{ print $1 }'")
      try:
        sizeofimage = round(float(sizeofimage)/1024/1024,1)
      except:
        sizeofimage = 0
      totaldiskusage += sizeofimage
      diskssizes += str(sizeofimage) + 'G<br>'
    elif vdisk.attrib.has_key("dev"):
      disks += vdisk.attrib['dev'] + '<br>'
      sizeofimage = commands.getoutput("fdisk -l " + vdisk.attrib['dev'] + " | grep Disk | head -1 | awk '{ print $5 }' ")
      sizeofimage = round(float(sizeofimage)/1000/1000/1000,1)
      totaldiskusage += sizeofimage
      diskssizes += str(sizeofimage) + 'G<br>'
  allvmsdets += '<td>' + diskssizes + '</td>'
  allvmsdets += '<td>' + disks + '</td>'
  allvmsdets += '<td>' + str(round(float(currentMemory.group(0))/1024/1024,1)) + 'G</td>'
  allvmsdets += '<td>' + str(round(float(memory.group(0))/1024/1024,1)) + 'G</td>'
  allvmsdets += '<td>' + currentcpus + '</td>'
  allvmsdets += '<td>' + maxcpus + '</td>'
  allvmsdets += '</tr>'
  for vcputune in et_cpu_cputune_iterator:
    for vcpupin in vcputune:
      if re.search("-", vcpupin.attrib['cpuset']):
        cpupinningranges = vcpupin.attrib['cpuset'].split(",")
        cpupinning = []
        for each_cpupinningranges in cpupinningranges:
          each_cpupinningranges = each_cpupinningranges.split("-")
          indexrangecpupinning = int(each_cpupinningranges[0])
          lengthrangecpupinning = int(each_cpupinningranges[1]) if len(each_cpupinningranges) == 2 else indexrangecpupinning
          while (indexrangecpupinning <= lengthrangecpupinning):
            cpupinning.append(indexrangecpupinning)
            indexrangecpupinning += 1
      else:
        cpupinning = vcpupin.attrib['cpuset'].split(",")
      for physicalcpupinning in cpupinning:
        physicalcpupinning = str(physicalcpupinning)
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

allocatedram = round(allocatedram,1)
allocatedmaxram = round(allocatedmaxram,1)
freeram = float(installedram - allocatedram)
freeram = round(freeram,1)
freeram = '<td style="background-color: red;">' + str(freeram) if freeram < 0 else '<td>' + str(freeram)
freecpus = int(int(installedcpus) - allocatedcpus)
freecpus = '<td style="background-color: red;">' + str(freecpus) if freecpus < 0 else '<td>' + str(freecpus)

ramtable = '<div class="resourcesdiv">'
ramtable += '<div class="resourcesdivpie">'
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
allvmsdiv += '<th>Current RAM</th>'
allvmsdiv += '<th>Max RAM</th>'
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
allvmsdiv += '<th>' + str(allocatedmaxram) + 'G</th>'
allvmsdiv += '<th>' + str(allocatedcpus) + '</th>'
allvmsdiv += '<th>' + str(allocatedmaxcpus) + '</th>'
allvmsdiv += '</tr>'
allvmsdiv += '</table>'
allvmsdiv += '</div>'

javascript = '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.1/Chart.bundle.min.js" '
javascript += 'integrity="sha256-N4u5BjTLNwmGul6RgLoESPNqDFVUibVuOYhP4gJgrew=" crossorigin="anonymous"></script>'
javascript += '<script>'
javascript += 'var ramctx = document.getElementById("ramchart");'
javascript += 'data = {'
javascript += 'datasets: [{data: ['
javascript +=  str(float(installedram - allocatedram)) if float(installedram - allocatedram) > 0 else '0'
javascript += ',' + str(allocatedram) + '],'
javascript += 'backgroundColor:['
javascript += '"green",'
javascript += '"red",'
javascript += ']'
javascript += '}],'
javascript += 'labels: ['
javascript += '"Free ' + str(float(installedram - allocatedram)) + 'G",'
javascript += '"Allocated '+ str(allocatedram) + 'G"'
javascript += '],'
javascript += '};'
javascript += ''
javascript += 'var myPieChart = new Chart(ramctx,{'
javascript += 'type: "pie",'
javascript += 'data: data,'
javascript += 'options: {'
javascript += 'tooltips: {'
javascript += 'callbacks: {'
javascript += 'label: function(tooltipItem, data) {'
javascript += 'return data.labels[tooltipItem.index];'
javascript += '}'
javascript += '}'
javascript += '},'
javascript += 'legend: {'
javascript += 'onClick: (e) => e.stopPropagation()'
javascript += '}'
javascript += '}'
javascript += '});'
javascript += '</script>'

indexf.write(ramtable)
indexf.write(cpudiv)
indexf.write(allvmsdiv)
indexf.write(javascript)
indexf.write('</body></html>')
indexf.close()

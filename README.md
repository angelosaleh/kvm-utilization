# kvm-utilization
Resources used by VMs running on a kvm host.

## Usage
Just run the command ./getVmsUsage.py and a report with a chart and tables will be created into a html file (hostname.html), reporting how the resources are allocated. This code has been tested on Centos 6 and 7.

## Dependencies
  - Of course the Host has to be a linux
  - dmidecode
  - df
  - du
  - awk
  - grep
  - virsh
  - lscpu

## Source

https://github.com/angelosaleh/kvm-utilization
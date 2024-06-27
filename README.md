# Smokeping-Configs
 
A repository containing my personalised Smokeping configs to popular cloud services, such as:

Popular DNS servers

Alibaba Cloud
Amazon AWS
Linode
Oracle Cloud
OVH
Vultr


The easiest way to set this up is create a folder inside your Smokeping config then in your main Targets file do the following


```
@include /config/Smokeping-Configs/dns.conf
@include /config/Smokeping-Configs/alibaba.conf
@include /config/Smokeping-Configs/amazonaws.conf
@include /config/Smokeping-Configs/linode.conf
@include /config/Smokeping-Configs/oraclecloud.conf
@include /config/Smokeping-Configs/ovh.conf
@include /config/Smokeping-Configs/vultr.conf
```


To make IPv6 work and spread out ICMP pings for IPv4 add the following to your Probes config

```
+ FPing
binary = /usr/sbin/fping
protocol = 4
hostinterval = 15
offset = 0%
pings = 20
step = 300
timeout = 1.5

+ FPing6
binary = /usr/sbin/fping
protocol = 6
hostinterval = 15
offset = 0%
pings = 20
step = 300
timeout = 1.5
```
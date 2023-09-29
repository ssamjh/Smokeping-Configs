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


```@include /config/Smokeping-Configs/dns.conf
@include /config/Smokeping-Configs/alibaba.conf
@include /config/Smokeping-Configs/amazonaws.conf
@include /config/Smokeping-Configs/linode.conf
@include /config/Smokeping-Configs/oraclecloud.conf
@include /config/Smokeping-Configs/ovh.conf
@include /config/Smokeping-Configs/vultr.conf
```
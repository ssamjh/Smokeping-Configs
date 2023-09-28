# Smokeping-Configs
 
A repository containing my personalised Smokeping configs to popular cloud services, such as:

OVH

Amazon AWS

Oracle Cloud

Digital Ocean

Popular DNS servers


The easiest way to set this up is create a folder inside your Smokeping config then in your main Targets file do the following


```@include /config/FOLDER-NAME/dns.conf
@include /config/FOLDER-NAME/amazonaws.conf
@include /config/FOLDER-NAME/oraclecloud.conf
@include /config/FOLDER-NAME/ovh.conf
@include /config/FOLDER-NAME/linode.conf
@include /config/FOLDER-NAME/vultr.conf
```
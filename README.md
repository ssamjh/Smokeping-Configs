# Smokeping-Configs

A repository containing my personalised Smokeping configs to popular cloud services, such as:

Popular DNS servers

Alibaba Cloud
Amazon AWS
Hetzner
Linode
Oracle Cloud
OVH
Vultr


The easiest way to set this up is create a folder inside your Smokeping config then in your main Targets file do the following


```
@include /config/Smokeping-Configs/dns.conf
@include /config/Smokeping-Configs/alibaba.conf
@include /config/Smokeping-Configs/amazonaws.conf
@include /config/Smokeping-Configs/hetzner.conf
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

## DNS IPv4/IPv6 split

The DNS configs (`dns.conf` and `dns_probe.conf`) are split into separate IPv4 and IPv6 target files. By default both are included, giving you dual-stack monitoring.

If your server does not have IPv6 connectivity, simply remove the IPv6 `@include` line from `dns.conf` and/or `dns_probe.conf`:

```
# dns.conf - remove the v6 line to disable IPv6 targets
@include dns_v4_targets.conf
@include dns_v6_targets.conf

# dns_probe.conf - same approach
@include dns_probe_v4_targets.conf
@include dns_probe_v6_targets.conf
```

You can also remove individual providers by deleting their entry from the relevant target file.

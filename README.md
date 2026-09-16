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


The easiest way to set this up is to clone this repo into a folder inside your
Smokeping config, then add a single line to your main Targets file:

```
@include /config/Smokeping-Configs/all.conf
```

`all.conf` pulls in every provider. When a new provider is added upstream you
just `git pull` and it appears - no change to your Targets file.

### Only want some providers?

Don't edit `all.conf` - local edits there will conflict on your next pull.
Instead, skip it and include the individual files you want:

```
@include /config/Smokeping-Configs/dns.conf
@include /config/Smokeping-Configs/dns_probe.conf
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

## Maintenance scripts

The helper scripts in `scripts/` are for maintaining this repo - you don't need
them to use the configs. Run them from anywhere; they resolve the `.conf` files
in the repo root automatically.

```
python scripts/check_endpoints.py              # validate every host (DNS + ping)
python scripts/check_endpoints.py vultr.conf   # just one file
python scripts/update_amazonaws.py --dry-run   # refresh AWS IPs from AWS's published data
python scripts/update_oraclecloud.py --dry-run # refresh OCI IPs from Oracle's published data
```

`update_amazonaws.py` and `update_oraclecloud.py` only cover providers that
publish their per-region IP ranges. The remaining providers are maintained by
hand, since their endpoint hostnames can't be derived from any published list.

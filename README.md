# Smokeping-Configs

A repository containing my personalised Smokeping configs to public endpoints, such as:

* Local network hosts (excluded from repo, sensitive)
* Quic (excluded from repo, under NDA)
* Popular DNS servers
* Common services
* Geographic targets
* Alibaba Cloud
* Amazon AWS, popular and dynamically generated from the [EC2 Reachability Test](http://ec2-reachability.amazonaws.com/)
* Apple
* Linode
* Oracle Cloud
* OVH
* Vultr

## Installation

Clone the repo to your Smokeping config folder, then add the following to the end of `Targets`:

```
@include /config/Smokeping-Configs/targets.conf
```

# Smokeping-Configs

A repository containing my personalised Smokeping configs to public endpoints, such as:

* Local network hosts (excluded from repo, sensitive)
* Quic (excluded from repo, under NDA)
* Popular DNS servers
* Common services (gaming, social media)
* Geographic targets (mirrors, universities)
* Alibaba Cloud
* Amazon AWS, both static region front-ends and endpoints dynamically generated from the [EC2 Reachability Test](http://ec2-reachability.amazonaws.com/)
* Apple
* Linode
* Oracle Cloud
* OVH
* Vultr

## Installation

1. Clone the repo to your Smokeping config folder.
2. Populate `local.conf` and `quic.conf` as desired, or remove them from `targets.conf`.
3. Add the following to the end of `Targets`:

```
@include /config/Smokeping-Configs/targets.conf
```

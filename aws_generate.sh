#!/bin/bash

file="amazonaws_generated.conf"

ipv4=$(curl http://ec2-reachability.amazonaws.com/ | grep -Po '(?<=<tr> <td>).*(?=</td> </tr>)')
#ipv6=$(curl http://ipv6.ec2-reachability.amazonaws.com/ | grep -Po '(?<=<tr> <td>).*(?=</td> </tr>)')
regex='([0-9a-z\-]+)<\/td>([\s])<td>([0-9\.\/]+)<\/td>([\s])<td>([0-9\.]+)<\/td>([\s])<td([\s])id="test"><img([\s])src="http:\/\/([0-9a-z\-\.]+)\/green-icon.gif">'

rm -f "${file}"
echo "+ AmazonAWSGenerated" | tee -a "${file}" > /dev/null 2>&1
echo "menu = Amazon AWS Generated" | tee -a "${file}" > /dev/null 2>&1
echo "title = Amazon AWS (generated from EC2 Reachability Test)" | tee -a "${file}" > /dev/null 2>&1
echo "" | tee -a "${file}" > /dev/null 2>&1
echo "" | tee -a "${file}" > /dev/null 2>&1

i=0
last_region=""
while IFS= read -r line; do
    region=$(perl -0777 -ne "print \$1 if m/${regex}/" <<< "$line")
    net=$(perl -0777 -ne "print \$3 if m/${regex}/" <<< "$line")
    ip=$(perl -0777 -ne "print \$5 if m/${regex}/" <<< "$line")
    #host=$(perl -0777 -ne "print \$9 if m/${regex}/" <<< "$line")

    if [ "${region}" == "${last_region}" ]; then
        i=$((i + 1))
        region_str="${region}_${i}"
    else
        i=0
        region_str="${region}"
    fi

    echo "${region_str}"
    echo "++ ${region_str}" | tee -a "${file}" > /dev/null 2>&1
    echo "menu = ${region_str}" | tee -a "${file}" > /dev/null 2>&1
    #echo "title = ${region_str} (${net})" | tee -a "${file}" > /dev/null 2>&1
    #echo "" | tee -a "${file}" > /dev/null 2>&1
    #echo "+++ cURL" | tee -a "${file}" > /dev/null 2>&1
    #echo "menu = cURL" | tee -a "${file}" > /dev/null 2>&1
    #echo "probe = Curl" | tee -a "${file}" > /dev/null 2>&1
    #echo "title = ${host} cURL" | tee -a "${file}" > /dev/null 2>&1
    #echo "host = ${host}" | tee -a "${file}" > /dev/null 2>&1
    #echo "" | tee -a "${file}" > /dev/null 2>&1
    #echo "+++ Ping" | tee -a "${file}" > /dev/null 2>&1
    #echo "menu = Ping" | tee -a "${file}" > /dev/null 2>&1
    #echo "probe = Ping" | tee -a "${file}" > /dev/null 2>&1
    echo "title = ${ip}" | tee -a "${file}" > /dev/null 2>&1
    echo "host = ${ip}" | tee -a "${file}" > /dev/null 2>&1
    echo "" | tee -a "${file}" > /dev/null 2>&1
    last_region="${region}"
done <<< "$ipv4"

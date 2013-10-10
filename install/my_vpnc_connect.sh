#!/usr/bin/env bash


# test for root
if [[ "$USER" != "root" ]]; then
    echo "$0 must be executed as root"
    exit;
fi


# print script usage
usage() {
    cat <<EOF
usage: $0 options
    
    Set up postgres database
    
    OPTIONS:
    -h      Show this message
    -l      use local-port 0
EOF
exit
}


#Process the arguments
while getopts hl opt
do
    case "$opt" in
        h) usage;;
        l) vpnc_connect_infix="--local-port 0";;
    esac
done


# get original gateway to make sure it exists afterward
DEFAULT_ROUTE_LINE=$(route -n | grep ^0.0.0.0)

# connect to VPN: must insert login credentials
vpnc-connect $vpnc_connect_infix --gateway xdata.data-tactics-corp.com --id xdata && \
	route add -net 10.1.93.0 netmask 255.255.255.0 dev tun0 && \
	route add -net 10.1.92.0 netmask 255.255.255.0 dev tun0 && \
	route add -net 10.1.90.0 netmask 255.255.255.0 dev tun0 && \
	route del -net 0.0.0.0 tun0

# make sure tun0 exists before proceeding
if [[ -z $(ifconfig | grep tun0) ]]; then
	echo "interface tun0 doesn't exist; assuming vpnc-connect failed"
	exit
fi

# make sure original gateway exists
if [[ -z $(route -n | grep ^0.0.0.0 | grep $DEFAULT_IF$) ]]; then
	DEFAULT_GATEWAY=$(awk '{print $2}' <(echo $DEFAULT_ROUTE_LINE))
	DEFAULT_IF=$(awk '{print $NF}' <(echo $DEFAULT_ROUTE_LINE))
	route add -net 0.0.0.0 gw $DEFAULT_GATEWAY dev $DEFAULT_IF
fi

# make sure /etc/resolv.conf works
> /etc/resolv.conf.tmp
for CONF_STR in "nameserver 10.1.90.10" \
	"nameserver 10.1.2.10" \
	"nameserver 127.0.0.1" \
	"search xdata.data-tactics-corp.com"
do
	if [[ -z $(grep "$CONF_STR" /etc/resolv.conf) ]]; then
		cat <(echo "$CONF_STR") >> /etc/resolv.conf.tmp
	fi
done
cat /etc/resolv.conf >> /etc/resolv.conf.tmp
cp /etc/resolv.conf.tmp /etc/resolv.conf

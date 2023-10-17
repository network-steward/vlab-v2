# Set the base image to Ubuntu
FROM ubuntu

# Update the repository sources list and install gnupg2
RUN apt-get update && apt-get install -y tcpdump bridge-utils ifupdown curl vlan ifenslave gnupg vim traceroute iputils-ping kmod lldpd ssh

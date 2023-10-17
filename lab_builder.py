from jinja2 import Environment, FileSystemLoader, Template, DebugUndefined
import time
import random
import yaml
import os
import shutil
import libvirt
from libvirt import libvirtError
import settings
from pydantic import BaseModel
from typing import Optional, Union

if __name__ != "virtuallab":
    print(f"Please call this script from virtualLabCLI! Quitting..")
    quit()

class KVM(BaseModel):
    hostname: str
    loopbacks: Optional[list] = None
    type: str
    management_mac: str
    mgmtip: Optional[str] = None
    interfaces: Optional[list] = None
    image_name: Union[list, str, dict]
    role: Optional[str] = None
    console_port: Optional[int] = None
    vlans: Optional[list] = None
    L3_VRF: Optional[list] = None
    mlag: Optional[str] = None
    bridge_domain: Optional[list] = None
    linecards: Optional[list] = None

    def make_xml(self, project_name): 
        """ 
        Creates the KVM xml files used as a configuration for each KVM vm. 
        """

        env = Environment(loader = FileSystemLoader([f"{settings.path}", f"{settings.path}"]), trim_blocks = True, lstrip_blocks=True, undefined=DebugUndefined)


        self.__dict__.update({'path' : f"{settings.path}/{project_name}/"})
        self.__dict__.update({'kvm_image_path' : f"{settings.path}/{project_name}/{settings.kvm_image_path}"})

        template = env.get_template('veos-xml.j2')
        if os.path.exists(f"{settings.path}/{project_name}/{self.hostname}.xml"):
            print(f"{self.__dict__}") #for debug
            os.remove(f"{settings.path}/{project_name}/{self.hostname}.xml")
            print(f"removed {settings.path}/{project_name}/{self.hostname}.xml")
        else:
            print(f"{settings.path}/{project_name}/{self.hostname}.xml does not exist! Creating!")
        with open(f"{settings.path}/{project_name}/{self.hostname}.xml", 'a') as config:
            config.write(template.render(self.__dict__))
            print(f"created {settings.path}/{project_name}/{self.hostname}.xml !")
 
    
    def image_init(self, project_name):
        """
        this will check to see if the images are in place for hosts defined in the yaml
        """

        if self.type == 'veos':
            image = f"{settings.veos_image}"
        elif self.type == 'vjunos':
            image = f"{settings.vjunos_image}"

        if os.path.exists(f"{settings.path}/{project_name}/{settings.kvm_image_path}{self.image_name}"):
            print(f"{settings.path}/{project_name}/{settings.kvm_image_path}{self.image_name} image already exists! not creating image!")
        else:
            print(f"{settings.path}/{project_name}/{settings.kvm_image_path}{self.image_name} doesn't exist! creating!")
            shutil.copy(f"{settings.base_kvm_images}{image}", f"{settings.path}/{project_name}/{settings.kvm_image_path}{self.image_name}" )   

    
    def init_tap(self):
        """
        create tap interfaces
        """

        for i in self.interfaces:
            print(f"creating tap interface {self.hostname}-{i['interface']}")
            os.system(f"ip tuntap add {self.hostname}-{i['interface']} mode tap")

    def delete_tap(self):
        """
        create tap interfaces
        """
      
        for i in self.interfaces:
            print(f"deleting tap interface {self.hostname}-{i['interface']}")
            os.system(f"ip tuntap del {self.hostname}-{i['interface']} mode tap")

    def init_ovs(self):
        """
        no ovswitch python library creates bridges and also passes options.. so onto the CLI we go
        """
        for i in self.interfaces:
            print(f"creating ovs bridge {i['bridge']}")
            os.system(f"ovs-vsctl add-br {i['bridge']}")
            os.system(f"ovs-vsctl set bridge {i['bridge']} other-config:forward-bpdu=true")


    def delete_ovs(self):
        """
        delete ovs bridges for ALL hosts in inventory file
        """
        for i in self.interfaces:
            print(f"deleting ovs bridge {i['bridge']}")
            os.system(f"ovs-vsctl del-br {i['bridge']}")


    def init_vm(self, project_name):
        """
        define the VM in KVM
        """
  
        with libvirt.open("qemu:///system") as virsh:
            with open (f"{settings.path}/{project_name}/{self.hostname}.xml") as f:
                xml = f.read()
            try:
                virsh_device = virsh.defineXML(xml)
                print(f"{settings.path}/{project_name}/{self.hostname} has been defined!")
            except libvirtError as e:
                if "already exists" in str(e):
                    print(e)


    def start_vm(self, project_name):
        """
        start the VM 
        """
        with libvirt.open("qemu:///system") as virsh:

            try:
                vm = virsh.lookupByName(self.hostname)
                vm.create()
                print(f"{settings.path}/{project_name}/{self.hostname} has been started!")
            except libvirtError as e:
                if "already running" in str(e):
                    print(f"{settings.path}/{project_name}/{self.hostname} is already running!")
                            
        
    def stop_vm(self, project_name):
        """
        stop the VM 
        """
        with libvirt.open("qemu:///system") as virsh:
            try:
                vm = virsh.lookupByName(self.hostname)
                vm.destroy()
                print(f"{settings.path}/{project_name}/{self.hostname} has been destroyed/stopped!")
            except libvirtError as e:
                if "Domain not found" in str(e):
                    print(f"{e}")             
                                

    def undefine_vm(self, project_name):
        """
        define the VM in KVM
        """
        with libvirt.open("qemu:///system") as virsh:
            try:
                virsh_device = virsh.lookupByName(self.hostname)
            except libvirtError as e:
                    if "Domain not found" in str(e):
                        print(e)
            if virsh_device.isActive():
                print(f"{settings.path}/{project_name}{self.hostname} is still active - please destroy first")
            else:
                virsh_device.undefine()
                print(f"{settings.path}/{project_name}{self.hostname} has been undefined")


class containers(BaseModel):
    """
    Container class for creating containers. Interfaces and routes are optional incase someone has/is 
    creating an experimental container they can still use this script to turn up but must configure the network by hand
    """
    hostname: str
    node_type: str
    docker_image: str
    mgmtip: str
    interfaces: Optional[list] = None
    routes: Optional[list] = None

    def init_container(self):
        """
         Creates containers from container image already created outside this script 
        """
        print(f"creating container {self.hostname}")
        os.system(f"docker run -d --name {self.hostname} -h {self.hostname} --ip {self.mgmtip} --cap-add=NET_ADMIN -i -t {self.docker_image} /bin/bash")

    def init_cont_interfaces(self):
        """
        Create and connect the logical docker interfaces to the OVS bridge found in the inventory file
        """
        print(f"creating container interfaces for host {self.hostname}")
        for i in self.interfaces:
            if i['type'] == "logical":
                os.system(f"ovs-docker add-port {i['bridge']} {i['interface']} {self.hostname}")

    def init_cont_conf(self):
        """
        Configure the logical and bond interfaces for the docker container 
        """
        print(f"creating container interfaces for host {self.hostname}")
        for i in self.interfaces:
            os.system(f"docker exec -it {self.hostname} ip link set {i['interface']} up")
            os.system(f"docker exec -it {self.hostname} ip address add {i['ip_address']} dev {i['interface']}")

    def container_interface_delete(self):
        """
        Delete the interface from docker
        """
        print(f"deleting container interfaces for host {self.hostname}")
        for i in self.interfaces:
            if i['type'] == "logical":
                os.system(f"ovs-docker del-port {i['bridge']} {i['interface']} {self.hostname}")

    def container_delete(self):
        """
        Delete the container
        """
        print(f"delete container {self.hostname}")
        os.system(f"docker stop {self.hostname}")
        os.system(f"docker rm {self.hostname}")

    def init_lldp(self):
        """
        For now just used to start lldp but could be used to start any service in the future on the containers.
        Perhaps could be avoided during the container build process but being lazy for now.
        """
        print(f"starting LLDP on {self.hostname}")
        os.system(f"docker exec -it {self.hostname} service lldpd start")

    def init_static_routes(self):
        """
        deploy known static routes so we can do inter SVI routing between groups that land in the L3 VRF
        """
        if 'routes' in self.__dict__:
            print(f"deploying static routes on {self.hostname}")                 
            for r in self.routes:
                print(f"deploying static route {r['subnet']} via gw {r['gateway']} on {self.hostname}")
                os.system(f"docker exec -it {self.hostname} route add -net {r['subnet']} gw {r['gateway']}")
        else:
            print(f"container {self.hostname} contains no static routes!")
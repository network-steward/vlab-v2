from cProfile import label
from jinja2 import Environment, FileSystemLoader, Template, DebugUndefined
import yaml
import argparse
import lab_builder
from pydantic import BaseModel


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start and Stop a Network Virtual Lab.')
    group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('-p', '--project', dest='project', type=str, required=True,
                        help="Specify the project name which is often the subdirectory the project resides in.")

    group.add_argument('-a', '--action', dest='action', type=str, choices=['startvlab','stopvlab'],
                        help='specify an action for KVMS of the vlab')

    group.add_argument('-s', '--subaction', dest='subaction', type=str, nargs="+", action="extend",
                        choices=['image_init','create_xml', 'create_tap', 'create_ovs', 'define_vm', 'start_vm', 
                        'stop_vm','delete_tap', 'delete_ovs', 'undefine_vm',  ],
                        help='Allow a user to call a subaction of startvlab or stopvlab.')

    parser.add_argument('--hosts', dest='hosts', type=str, nargs="+", required=True,
                        help="at minimum specify '--hosts all' or specify the name of the host in the inventory file.")


    args = parser.parse_args()
    KVMS =[]

    print(f" the project name is: {args.project}")
    if args.project:

        node_configs_inventory = f"{args.project}/configs/inventory.yml"
        with open(f"{node_configs_inventory}", 'r') as file:
            kvm_hosts = yaml.safe_load(file)

    if args.hosts[0] == 'all':
# for debug if object insantiation fails [ (KVMS.append(lab_builder.KVM(**host_inv)), print(host_inv['hostname'])) for host_inv in kvm_hosts ['kvm_nodes'] ]
        [ KVMS.append(lab_builder.KVM(**host_inv)) for host_inv in kvm_hosts ['kvm_nodes'] ]        
    else:
        [ KVMS.append(lab_builder.KVM(**host_inv)) for node_name in args.hosts for host_inv in kvm_hosts['kvm_nodes'] if host_inv['hostname'] == node_name ]

    

    if args.action == 'startvlab':
        for v in KVMS:
            v.make_xml(args.project)
            v.image_init(args.project)
            v.init_tap()
            v.init_ovs()
            v.init_vm (args.project)
            v.start_vm(args.project)

    elif args.action == 'stopvlab':
        for v in KVMS:
            v.stop_vm(args.project)
            v.delete_tap()
            if args.hosts[0] == 'all':
                v.delete_ovs()
                v.undefine_vm(args.project)
    
    elif args.action == 'config_fpc':
        for v in KVMS:
            v.config_fpc()

    if args.subaction != None:
        for a in args.subaction:
            print(f"Performing {a} !")
            if a == "image_init":
                for v in KVMS:
                    v.image_init(args.project)
            elif a == "create_xml":    
                for v in KVMS:
                    v.create_xml(args.project)
            elif a == "create_tap":    
                for v in KVMS:
                    v.create_tap()
            elif a == "create_ovs":    
                for v in KVMS: 
                    v.create_ovs()
            elif a == "define_vm":
                for v in KVMS:
                    v.define_vm(args.project)
            elif a == "start_vm":
                for v in KVMS:            
                    v.start_vm(args.project)
            elif a == "stop_vm":    
                for v in KVMS:             
                    v.stop_vm()
            elif a == "delete_tap": 
                for v in KVMS:
                    v.delete_tap()
            elif a == "delete_ovs":    
                for v in KVMS:            
                    v.delete_ovs()
            elif a == "undefine_vm":    
                for v in KVMS:
                    v.undefine_vm(args.project)


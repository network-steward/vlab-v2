from jinja2 import Environment, FileSystemLoader, Template, DebugUndefined
import yaml
import argparse
import virtuallab
import settings



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start and Stop a Containers that connect to the Virtual Lab.')
    group = parser.add_mutually_exclusive_group(required=True)

    parser.add_argument('-p', '--project', dest='project', type=str, required=True,
                        help="Specify the project name which is often the subdirectory the project resides in.")

    group.add_argument('-a', '--action', dest='action', type=str, choices=['start_containers','stop_containers'],
                        help='either specify action start_containers or stop_containers to start/stop the containers')

    group.add_argument('-s', '--subaction', dest='subaction', type=str, nargs="+", action="extend",
                        choices=['init_container','init_cont_interfaces', 'init_cont_conf', 'init_lldp', 
                        'init_static_routes', 'container_interface_delete','container_delete'],
                        help='Allow a user to call a subaction of start_containers or stop_containers.')

    parser.add_argument('--hosts', dest='hosts', type=str, nargs="+", required=True,
                        help="at minimum specify '--hosts all' or specify the name of the host in the inventory file.")

    args = parser.parse_args()
    containers = []


    with open(f"{args.project}/configs/inventory.yml", 'r') as file:
        container_hosts = yaml.safe_load(file)

    if args.hosts[0] == 'all':
            [ containers.append(virtuallab.containers(**host_inv)) for host_inv in container_hosts['container_nodes'] ]     
    else:
        for node_name in args.hosts:
            [ containers.append(virtuallab.containers(**host_inv)) for c in args.hosts for host_inv in container_hosts if host_inv['hostname'] == c]  

    if args.action == 'start_containers':
        for c in containers:
            c.init_container()
            c.init_cont_interfaces()
            c.init_cont_conf()
            c.init_lldp()
            c.init_static_routes()
    elif args.action == 'stop_containers':
        for c in containers:        
            c.container_interface_delete()
            c.container_delete()  

    if args.subaction != None:
        for a in args.subaction:
            print(f"Performing {a} !")
            if a == "init_container":
                for c in containers:
                    c.init_container()
            elif a == "init_cont_interfaces":    
                for c in containers:
                    c.init_cont_interfaces()
            elif a == "init_cont_conf":    
                for c in containers:
                    c.container_interface_configure()
            elif a == "init_lldp":    
                for c in containers:
                    c.init_lldp()
            elif a == "init_static_routes":    
                for c in containers:
                    c.init_static_routes()
            elif a == "container_interface_delete":    
                for c in containers:
                    c.container_interface_delete()
            elif a == "container_delete":    
                for c in containers:
                    c.container_delete() 
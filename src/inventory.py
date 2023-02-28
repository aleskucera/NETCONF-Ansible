from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


def create_inventory(devices_configuration: list, output_path: str) -> None:
    """Creates an Ansible inventory file from the list of devices.

    :param devices_configuration: The list of devices.
    :param output_path: The path to the output file.
    """
    
    inventory = CommentedMap()
    inventory['all'] = CommentedMap()
    inventory['all']['hosts'] = CommentedMap()

    for device in devices_configuration:
        inventory['all']['hosts'][device['name']] = CommentedMap()
        inventory['all']['hosts'][device['name']]['ansible_host'] = device['ip_address']
        inventory['all']['hosts'][device['name']]['ansible_user'] = device['username']
        inventory['all']['hosts'][device['name']]['ansible_password'] = device['password']

    yaml.dump(inventory, open(output_path, 'w'))

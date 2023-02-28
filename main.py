import os
import subprocess
from ruamel.yaml import YAML

from src import CzechLightROADMConfig, create_inventory

yaml = YAML()


def main():
    print('\n==================================================')
    print('\t CzechLight ROADM Configuration Script')
    print('==================================================\n')

    # Set host_key_checking to False
    d = dict(os.environ)
    d['ANSIBLE_HOST_KEY_CHECKING'] = 'False'

    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('backup', exist_ok=True)
    os.makedirs('checkup', exist_ok=True)

    devices = yaml.load(open('config/devices.yaml', 'r').read())
    inventory_file = os.path.join(os.getcwd(), 'playbooks', 'inventory.yaml')
    create_inventory(devices, inventory_file)

    for device in devices:
        print(f"\nINFO: Processing device: {device['name']} ({device['ip_address']})")

        final_config_file = os.path.join(os.getcwd(), 'data', f"{device['name']}.xml")
        backup_path = os.path.join(os.getcwd(), 'backup', f"{device['name']}_backup.xml")
        proposed_config_file = os.path.join(os.getcwd(), 'config', f"{device['name']}.yaml")
        channel_plan_file = os.path.join(os.getcwd(), 'data', f"{device['name']}_channel_plan.xml")
        media_channels_file = os.path.join(os.getcwd(), 'data', f"{device['name']}_media_channels.xml")

        print(f'\t - INFO: Downloading current configuration from {device["ip_address"]}')
        res = subprocess.run(['ansible-playbook', 'playbooks/get_config.yaml',
                              '-e', f"channel_plan_file={channel_plan_file} media_channels_file={media_channels_file}",
                              '--limit', device['name'], '-i', inventory_file], env=d)

        if res.returncode != 0:
            print(f'\t - ERROR: Downloading configuration from {device["ip_address"]} failed')
            continue

        device_config = CzechLightROADMConfig(channel_plan_file=channel_plan_file,
                                              current_config_file=media_channels_file,
                                              proposed_config_file=proposed_config_file,
                                              mode=device['mode'])

        if device['validate']:
            print(f'\t - INFO: Comparing current configuration with proposed configuration from:'
                  f'\n\t\t{proposed_config_file}')
            device_config.create_summary(os.path.join(os.getcwd(), 'checkup'))
            print(f'\t - INFO: Comparison finished. Summary saved to {os.path.join(os.getcwd(), "checkup")}')
            i = input(f'\t - QUESTION: Do you want to continue with the configuration of this device? [y/n]\n\t\t')
            if i.lower() != 'y':
                print(f'\t - Skipping device {device["name"]}')
                continue
        else:
            print(f'\t - WARNING: Skipping validation of the configuration')

        device_config.create_config(final_config_file)
        print(f'\t - INFO: Configuration created. Saving to {final_config_file}')

        print(f'\t - INFO: Uploading configuration to {device["ip_address"]}')
        # Split the backup path to the directory and the filename
        backup_path = os.path.split(backup_path)
        res = subprocess.run(['ansible-playbook', 'playbooks/set_config.yaml',
                              '-e', f"configuration_file={final_config_file} "
                                    f"backup_dir={backup_path[0]} backup_file={backup_path[1]}",
                              '--limit', device['name'], '-i', inventory_file], env=d)

        print(f'\t - INFO: Configuration uploaded successfully')


if __name__ == '__main__':
    main()

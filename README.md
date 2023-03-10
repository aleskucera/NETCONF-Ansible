# Configuration script for the ROADM devices via the NETCONF protocol and Ansible

This repository contains a Python script that allows to configure the ROADM devices easily and safely via
the [NETCONF protocol](https://en.wikipedia.org/wiki/NETCONF) and [Ansible](https://www.ansible.com/).

## Requirements

As mentioned above, the requirements for the script are Python 3 and its libraries. The script has been tested
with Python 3.10.

You can install the requirements with pip by running the following command:

    pip install -r environment/requirements.txt

or you can create an Anaconda environment with the following command:

    conda env create -f environment/environment.yaml

## Configuration

Before running the script, you need to create configuration files for the ROADM devices in the `config` folder.
For example, if you want to configure two ROADM devices, you will have to create `config/devices.yaml` and
specify the following variables

- **name**: Name of the device. Will be used for identification in the project files.
- **ip_address**: IP address of the ROADM device.
- **username**: The username for the SSH connection to the ROADM device.
- **password**: The password for the SSH connection to the ROADM device.
- **mode**: The mode of the configuration. Can be `merge` or `replace`.
- **validate**: Whether to validate the configuration before applying it. Can be `true` or `false`.

The configuration files for the ROADM devices are in the [YAML](https://en.wikipedia.org/wiki/YAML) format.
The following is an example of a configuration file for two ROADM devices:

    - name: roadm_1
      ip_address: 10.0.154.97
      username: dwdm
      password: dwdm
      mode: merge
      validate: true
    
    - name: roadm_2
      ip_address: 10.0.154.94
      username: dwdm
      password: dwdm
      mode: replace
      validate: true

After defining the devices in the `config/devices.yaml` file, you need to create the configuration files for
each device in the `config` folder. For example, if you want to configure the ROADM device with the name
`roadm_1`, you will have to create `config/roadm_1.yaml` with the following variables

- **description**: Description of the channel. (Optional)
- **leaf_port**: The leaf port of the ROADM device to which the channel is connected.
- **attenuation**: The attenuation of the channel in dB.
- **frequency_center**: The center frequency of the channel in THz.
- **frequency_span**: The frequency span of the channel in GHz.

The configuration files for the ROADM devices are also in the [YAML](https://en.wikipedia.org/wiki/YAML) format. The
following is an example of a configuration file for the ROADM device.

    - description: Test channel 1
      leaf_port: E1
      attenuation: 10.0
      frequency_center: 194.7 # THz
      frequency_span: 50  # GHz
    
    - description: Test channel 2
      leaf_port: E2
      attenuation: 1.0
      frequency_center: 194.6 # THz
      frequency_span: 100 # GHz

## Usage

To run the script, you need to run the following command:

    python main.py

The following steps will be performed:

1. The script will check the configuration files in the `config` folder and will create the Ansible inventory
   file `playbooks/inventory.yaml` for Ansible.
2. The current configuration will be loaded from the ROADM devices and saved in the `data` folder. The configuration
   is loaded via the NETCONF protocol using Ansible playbook `playbooks/get_config.yaml`.
3. If the variable `validate` is set to `true` in the configuration file for the ROADM device, the script will
   compare the current configuration with the new configuration and visualize the changes in the `checkup` folder. More
   about the checkup files can be found in the [Checkup](#checkup) section. Then the user will be asked to confirm
   the changes.
4. If the variable `validate` is set to `false` or the user confirms the changes, the script will apply the new
   configuration to the ROADM devices via the NETCONF protocol using Ansible playbook `playbooks/set_config.yaml`.

## Checkup

The script will create a summary of the changes in the `checkup` folder to visualize important information about
the differences between the current configuration and the new configuration. The following files will be created:

- **added_channels.yaml**: The channels that will be added to the ROADM device.
- **removed_channels.yaml**: The channels that will be removed from the ROADM device.
- **changed_channels.yaml**: The channels that will be changed on the ROADM device.
- **final_channels.yaml**: The final configuration of the ROADM device.



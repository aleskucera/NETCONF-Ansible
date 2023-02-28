import os

import xmltodict
import xml.etree.ElementTree as ET
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .channel import Channel

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


class CzechLightROADMConfig:
    """A class representing the configuration of the ROADM device. The class provides methods for loading, comparing and
    creating the configuration files.

    :param channel_plan_file: The path to the channel plan file in the form of an XML file loaded from the device.
    :param current_config_file: The path to the current configuration file in the form of an XML file loaded from the
                                device.
    :param proposed_config_file: The path to the proposed configuration file in the form of a YAML file created by the
                                user.
    :param mode: The mode of the configuration. Either "merge" or "replace".
    """

    def __init__(self, channel_plan_file: str, current_config_file: str, proposed_config_file: str,
                 mode: str = 'merge'):

        assert mode in ['merge', 'replace'], 'Invalid mode. Please use either "merge" or "replace".'
        self.mode = mode

        # Check if the files exist and extensions are correct
        if not os.path.isfile(channel_plan_file) and not channel_plan_file.endswith('.xml'):
            raise FileNotFoundError(f'The file {channel_plan_file} does not exist.')
        if not os.path.isfile(current_config_file) and not current_config_file.endswith('.xml'):
            raise FileNotFoundError(f'The file {current_config_file} does not exist.')
        if not os.path.isfile(proposed_config_file) and not proposed_config_file.endswith('.yaml'):
            raise FileNotFoundError(f'The file {proposed_config_file} does not exist.')

        # Load the channel plan and configuration files
        self.channel_plan = xmltodict.parse(open(channel_plan_file, 'r').read())
        self.current_channel_config = xmltodict.parse(open(current_config_file, 'r').read())
        self.proposed_channel_config = yaml.load(open(proposed_config_file, 'r').read())

        # Create the list of current channels
        self.current_channels = []
        for channel in self.current_channel_config['data']['media-channels']:
            self.current_channels.append(Channel(channel=channel, channel_plan=self.channel_plan, origin='xml'))

        # Create the list of proposed channels
        self.proposed_channels = []
        for channel in self.proposed_channel_config:
            self.proposed_channels.append(Channel(channel=channel, channel_plan=self.channel_plan, origin='yaml'))

        # Create the list of new, removed and changed channels
        self.added_channels, self.removed_channels, self.changed_channels, \
            self.merged_channels = self._calculate_statistics()

        if self.mode == 'merge':
            self.final_channels = self.merged_channels
            self.removed_channels = []
        elif self.mode == 'replace':
            self.final_channels = self.proposed_channels

    def _calculate_statistics(self) -> tuple[list[Channel], list[Channel], list[dict[str, Channel]], list[Channel]]:
        """Create a statistics of the proposed configuration compared to the current configuration.

        :return: A tuple of lists containing the added channels, removed channels, changed channels and merged channels.
        """

        added_channels, removed_channels, changed_channels, merged_channels = [], [], [], []

        for current_channel in self.current_channels:
            for proposed_channel in self.proposed_channels:
                if current_channel.name == proposed_channel.name:
                    if current_channel != proposed_channel:
                        changed_channels.append({'proposed': proposed_channel, 'current': current_channel})
                    break
            else:
                removed_channels.append(current_channel)

        for proposed_channel in self.proposed_channels:
            for current_channel in self.current_channels:
                if current_channel.name == proposed_channel.name:
                    break
            else:
                added_channels.append(proposed_channel)

        # Create the list of merged channels (proposed channels + removed channels)
        merged_channels = self.proposed_channels + removed_channels

        # sort the lists
        added_channels.sort()
        removed_channels.sort()
        changed_channels.sort(key=lambda x: x['current'].name)
        merged_channels.sort()

        return added_channels, removed_channels, changed_channels, merged_channels

    def create_config(self, output_file: str) -> None:
        """Create the configuration file in the form of an XML file.

        :param output_file: The path to the output file.
        """

        root = ET.Element("config")
        root.set("xmlns", "urn:ietf:params:xml:ns:netconf:base:1.0")

        for channel in self.final_channels:
            channel.create_xml_child(root)

        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8')

    def create_summary(self, output_dir: str):
        """Create a summary of the proposed configuration in form of YAML files.
        The created files are following:
            - added_channels.yaml
            - removed_channels.yaml
            - changed_channels.yaml
            - final_configuration.yaml
            
        :param output_dir: The path to the output directory.
        """

        os.makedirs(output_dir, exist_ok=True)

        added_channels_file = os.path.join(output_dir, 'added_channels.yaml')
        removed_channels_file = os.path.join(output_dir, 'removed_channels.yaml')
        changed_channels_file = os.path.join(output_dir, 'changed_channels.yaml')
        final_channels_file = os.path.join(output_dir, 'final_configuration.yaml')

        self._dump_channels([channel.to_map() for channel in self.added_channels], added_channels_file)
        self._dump_channels([channel.to_map() for channel in self.final_channels], final_channels_file)
        self._dump_channels([channel.to_map() for channel in self.removed_channels], removed_channels_file)

        changed_channels = [self._visualize_change(channel['proposed'], channel['current']) for channel in
                            self.changed_channels]
        self._dump_channels(changed_channels, changed_channels_file)

    @staticmethod
    def _visualize_change(proposed_channel: Channel, current_channel: Channel) -> CommentedMap:
        """Visualize the changes between the proposed channel and the current channel.

        :param proposed_channel: The proposed channel.
        :param current_channel: The current channel.
        """
        change = CommentedMap()
        proposed_channel_dict = proposed_channel.to_map()
        current_channel_dict = current_channel.to_map()

        for key in proposed_channel_dict:
            if proposed_channel_dict[key] != current_channel_dict[key]:
                change[key] = f'{current_channel_dict[key]} -> {proposed_channel_dict[key]}'
            else:
                change[key] = proposed_channel_dict[key]

        change.yaml_add_eol_comment('GHz', 'frequency_span')
        change.yaml_add_eol_comment('THz', 'frequency_center')

        return change

    @staticmethod
    def _dump_channels(channels: list[CommentedMap], output_file: str) -> None:
        """Dump the list of channels to the output file.

        :param channels: The list of channels.
        :param output_file: The path to the output file.
        """

        n_channels = len(channels)
        with open(output_file, 'w') as f:
            commented_channels = CommentedSeq(channels)
            for i in range(n_channels):
                commented_channels.yaml_set_comment_before_after_key(i, before='\n')

            if n_channels == 0:
                yaml.dump('No channels in this category', f)
            else:
                yaml.dump(commented_channels, f)

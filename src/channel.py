import xml.etree.ElementTree as ET
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

yaml = YAML()
yaml.indent(mapping=2, sequence=4, offset=2)


class Channel:
    """A class representing a media channel in the ROADM device. The class can be initialized from either a YAML file or
    an XML file.
    The purpose of the class is to provide a unified representation of the channel configuration, regardless of the
    origin of the configuration.
    The class provides methods for comparing two channels, creating a new XML child element and creating a new
    CommentedMap object for the YAML representation of the channel.

    :param channel: The channel configuration in the form of a dictionary.
    :param channel_plan: The channel plan in the form of a dictionary.
    :param origin: The origin of the channel configuration. Either "yaml" or "xml".
    """

    def __init__(self, channel: dict, channel_plan: dict, origin: str = 'yaml'):

        assert origin in ['yaml', 'xml'], 'Invalid origin. Please use either "yaml" or "xml".'
        self.origin = origin

        self.center_exp = 1e6
        self.span_exp = 1e3

        self.name = None
        self.port = None
        self.attenuation = None
        self.description = None
        self.frequency_span = None
        self.frequency_center = None
        self.lower_frequency = None
        self.upper_frequency = None

        self.channel_plan = None

        if self.origin == 'yaml':
            self._init_from_yaml(channel, channel_plan)
        elif self.origin == 'xml':
            self._init_from_xml(channel, channel_plan)

    def create_xml_child(self, parent) -> None:
        """Create the XML child element for the channel.
        The XML element is added to the parent XML element.

        :param parent: The parent XML element.
        """

        media_channels = ET.SubElement(parent, "media-channels")
        media_channels.set("xmlns", "http://czechlight.cesnet.cz/yang/czechlight-roadm-device")

        # Add the channel name
        channel = ET.SubElement(media_channels, "channel")
        channel.text = self.name

        # Add the ADD port and attenuation
        add = ET.SubElement(media_channels, "add")
        add_port = ET.SubElement(add, "port")
        add_port.text = self.port
        add_attenuation = ET.SubElement(add, "attenuation")
        add_attenuation.text = str(self.attenuation)

        # Add the DROP port and attenuation
        drop = ET.SubElement(media_channels, "drop")
        drop_port = ET.SubElement(drop, "port")
        drop_port.text = self.port
        drop_attenuation = ET.SubElement(drop, "attenuation")
        drop_attenuation.text = str(self.attenuation)

        # Add the description
        if self.description is not None:
            description = ET.SubElement(media_channels, "description")
            description.text = self.description

    def to_map(self) -> CommentedMap:
        """Create a CommentedMap object for the YAML representation of the channel.
        Used for visualization of the channel configuration.
        """

        ret = CommentedMap()
        ret['name'] = self.name
        ret['leaf_port'] = self.port
        ret['attenuation'] = self.attenuation
        ret['frequency_span'] = self.frequency_span
        ret['frequency_center'] = self.frequency_center
        ret['description'] = self.description

        ret.yaml_add_eol_comment('GHz', 'frequency_span')
        ret.yaml_add_eol_comment('THz', 'frequency_center')
        return ret

    def _init_from_yaml(self, channel: dict, channel_plan: dict):
        """Initialize the channel dictionary loaded from a YAML file.

        :param channel: The channel configuration in the form of a dictionary.
        :param channel_plan: The channel plan in the form of a dictionary.
        """

        self.origin = 'yaml'
        self.channel_plan = channel_plan

        assert 'leaf_port' in channel, 'Leaf port is missing.'
        assert 'attenuation' in channel, 'Attenuation is missing.'
        assert 'frequency_span' in channel, 'Frequency span is missing.'
        assert 'frequency_center' in channel, 'Frequency center is missing.'

        self.port = channel['leaf_port']
        self.attenuation = channel['attenuation']
        self.frequency_span = channel['frequency_span']
        self.frequency_center = channel['frequency_center']
        self.description = channel['description'] if 'description' in channel else None

        if not self._find_channel():
            raise ValueError(f'Channel with frequency center {self.frequency_center} and span '
                             f'{self.frequency_span} not found in the channel plan.')

    def _init_from_xml(self, channel: dict, channel_plan: dict):
        """Initialize the channel dictionary loaded from an XML file.

        :param channel: The channel configuration in the form of a dictionary.
        :param channel_plan: The channel plan in the form of a dictionary.
        """

        self.origin = 'xml'
        self.name = channel['channel']
        self.channel_plan = channel_plan

        if self.name != 'C-band':
            assert 'add' in channel, 'ADD port is missing.'
            assert 'drop' in channel, 'DROP port is missing.'
            assert 'attenuation' in channel['add'] and 'attenuation' in channel['drop'], \
                'Attenuation is missing.'
            assert 'port' in channel['add'] and 'port' in channel['drop'], 'Port is missing.'
            assert channel['add']['port'] == channel['drop']['port'], 'ADD and DROP ports are not the same.'
            assert channel['add']['attenuation'] == channel['drop']['attenuation'], \
                'ADD and DROP attenuation are not the same.'

            self.port = channel['add']['port']
            self.attenuation = float(channel['add']['attenuation'])
            self.description = channel['description'] if 'description' in channel else None

        if not self._find_channel():
            raise ValueError(f'Channel {self.name} not found in the channel plan.')

    def _find_channel(self) -> bool:
        """Find the channel in the channel plan and set the missing frequency attributes.
        Return True if the channel was found, False otherwise.
        """

        for channel in self.channel_plan['data']['channel-plan']['channel']:
            name = channel['name']
            lower_frequency = float(channel['lower-frequency'])
            upper_frequency = float(channel['upper-frequency'])

            if self.frequency_center is not None and self.frequency_span is not None:
                channel_lf = self.frequency_center * self.center_exp - self.frequency_span * self.span_exp / 2
                channel_uf = self.frequency_center * self.center_exp + self.frequency_span * self.span_exp / 2
                if channel_lf == lower_frequency and channel_uf == upper_frequency:
                    self.name = name
                    self.lower_frequency = lower_frequency
                    self.upper_frequency = upper_frequency
                    return True

            elif self.name is not None and name == self.name:
                self.lower_frequency = lower_frequency
                self.upper_frequency = upper_frequency

                frequency_span = self.upper_frequency - self.lower_frequency
                frequency_center = self.lower_frequency + frequency_span / 2

                self.frequency_span = frequency_span / self.span_exp
                self.frequency_center = frequency_center / self.center_exp
                return True

        return False

    def __str__(self):
        if self.origin == 'yaml':
            channel = '\nPROPOSED CHANNEL:\n'
        else:
            channel = '\nCURRENT CHANNEL:\n'
        return f'{channel}' \
               f'\t- Name: {self.name}\n' \
               f'\t- Port: {self.port}\n' \
               f'\t- Attenuation: {self.attenuation}\n' \
               f'\t- Lower frequency: {self.lower_frequency}\n' \
               f'\t- Upper frequency: {self.upper_frequency}\n' \
               f'\t- Description: {self.description}\n'

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if self.name == 'C-band':
            return self.name == other.name
        else:
            return self.name == other.name and self.port == other.port and self.attenuation == other.attenuation and \
                self.lower_frequency == other.lower_frequency and self.upper_frequency == other.upper_frequency

    def __ge__(self, other):
        return self.name >= other.name

    def __gt__(self, other):
        return self.name > other.name

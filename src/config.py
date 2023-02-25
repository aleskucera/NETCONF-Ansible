import yaml
import xmltodict
import xml.etree.ElementTree as ET


class Channel:
    def __init__(self, leaf_port: str, attenuation: float, frequency_center: float,
                 frequency_span: float, channel_plan: dict, description: str = None):

        self.description = description

        self.port = leaf_port
        self.attenuation = attenuation
        self.frequency_span = frequency_span
        self.frequency_center = frequency_center

        self.channel_plan = channel_plan

        self.name = None
        self.lower_frequency = None
        self.upper_frequency = None

        if not self._valid_channel():
            raise ValueError('Invalid channel. Please check the channel plan.')

    def create_xml(self, parent) -> None:
        """Create the XML configuration for the media channel.
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

    def _valid_channel(self) -> bool:
        """Validate the channel against the channel plan.
        If the channel is valid, the name, lower and upper frequency are set.
        """
        channel_lf = self.frequency_center * 10e6 - self.frequency_span * 10e3 / 2
        channel_uf = self.frequency_center * 10e6 + self.frequency_span * 10e3 / 2

        for channel in self.channel_plan['data']['channel-plan']['channel']:
            name = channel['name']
            lower_frequency = float(channel['lower-frequency'])
            upper_frequency = float(channel['upper-frequency'])

            if channel_lf == lower_frequency and channel_uf == upper_frequency:
                self.name = name
                self.lower_frequency = lower_frequency
                self.upper_frequency = upper_frequency
                return True

        return False

    def __str__(self):
        return f'MEDIA CHANNEL:\n' \
               f'\t- Name: {self.name}\n' \
               f'\t- Port: {self.port}\n' \
               f'\t- Attenuation: {self.attenuation}\n' \
               f'\t- Lower frequency: {self.lower_frequency}\n' \
               f'\t- Upper frequency: {self.upper_frequency}\n' \
               f'\t- Description: {self.description}'

    def __repr__(self):
        return self.__str__()


class CzechLightROADMConfig:
    def __init__(self, channel_plan_file: str, media_channels_file: str):
        self.channel_plan_file = channel_plan_file
        self.media_channels_file = media_channels_file

        self.channel_plan = xmltodict.parse(open(self.channel_plan_file, 'r').read())
        self.media_channels = yaml.safe_load(open(self.media_channels_file, 'r').read())

        self.channels = [Channel(**channel, channel_plan=self.channel_plan) for channel in self.media_channels]

    def create_config(self, output_path: str):
        """Create the XML configuration for the media channels. The configuration is written to the output path.
        :param output_path: The output path.
        """
        root = ET.Element("config")
        root.set("xmlns", "urn:ietf:params:xml:ns:netconf:base:1.0")

        for channel in self.channels:
            channel.create_xml(root)

        tree = ET.ElementTree(root)
        tree.write(output_path, encoding='utf-8')

    def __str__(self):
        out = '\n ====== MEDIA CHANNELS CONFIGURATION ====== \n'
        for channel in self.channels:
            out += '\n' + str(channel) + '\n'
        out += '\n ========================================== \n'
        return out

    def __repr__(self):
        return self.__str__()


if __name__ == '__main__':
    # Create a configuration object
    config = CzechLightROADMConfig(channel_plan_file='../data/channel_plan_1.xml',
                                   media_channels_file='../config/configuration_1.yaml')

    # Visualize the loaded configuration
    print(config)

    # Write the configuration to a file in XML format
    config.create_config('../config/configuration_1.xml')

from .base import OpenWrtConverter


class Wireless(OpenWrtConverter):
    netjson_key = 'interfaces'
    intermediate_key = 'wireless'
    _uci_types = ['wifi-iface']

    def to_intermediate(self):
        self._track_bridged_wifi()
        return super().to_intermediate()

    def to_intermediate_loop(self, block, result, index=None):
        wireless = self.__intermediate_wireless(block)
        if wireless:
            result.setdefault('wireless', [])
            result['wireless'].append(wireless)
        return result

    def __intermediate_wireless(self, interface):
        if 'wireless' not in interface:
            return
        wireless = interface['wireless']
        # inherit "disabled" attribute from interface if present
        wireless['disabled'] = interface.get('disabled')
        # add ifname
        wireless['ifname'] = interface['name']
        wireless.update(
            {
                '.type': 'wifi-iface',
                '.name': wireless.pop('id', None) or self.__get_auto_name(interface),
            }
        )
        # rename radio to device
        wireless['device'] = wireless.pop('radio')
        # mac address override
        if 'mac' in interface:
            wireless['macaddr'] = interface['mac']
        # map netjson wifi modes to uci wifi modes
        modes = {
            'access_point': 'ap',
            'station': 'sta',
            'adhoc': 'adhoc',
            'monitor': 'monitor',
            '802.11s': 'mesh',
        }
        wireless['mode'] = modes[wireless['mode']]
        # map advanced 802.11 netjson attributes to UCI
        wifi_options = {
            'ack_distance': 'distance',
            'rts_threshold': 'rts',
            'frag_threshold': 'frag',
        }
        for netjson_key, uci_key in wifi_options.items():
            value = wireless.pop(netjson_key, None)
            if value is not None:
                # ignore if 0 (autogenerated UIs might use 0 as default value)
                if value > 0:
                    wireless[uci_key] = value
        # determine encryption for wifi
        if 'encryption' in wireless:
            encryption = self.__intermediate_encryption(wireless)
            wireless.update(encryption)
        # attached networks (openwrt specific)
        # by default the wifi interface is attached
        # to its defining interface
        # but this behaviour can be overridden
        if not wireless.get('network'):
            # try to automatically determine whether
            # we should attach this interface to a bridge
            try:
                bridges = self._bridged_wifi[interface['name']]
            except KeyError:
                # default to the value of "network" or inteface name
                network = [interface.get('network', interface['name'])]
            else:
                network = bridges
            wireless['network'] = network
        wireless['network'] = (
            ' '.join(wireless['network']).replace('.', '_').replace('-', '_')
        )
        return self.sorted_dict(wireless)

    def __get_auto_name(self, interface):
        wifi_name = self._get_uci_name(interface['name'])
        return 'wifi_{0}'.format(wifi_name)

    def __intermediate_encryption(self, wireless):
        encryption = wireless.pop('encryption', {})
        disabled = encryption.get('disabled', False)
        protocol_mapping = {
            'wep_open': 'wep-open',
            'wep_shared': 'wep-shared',
            'wpa_personal': 'psk',
            'wpa2_personal': 'psk2',
            'wpa3_personal': 'sae',
            'wpa_personal_mixed': 'psk-mixed',
            'wpa2_personal_mixed': 'sae-mixed',
            'wpa_enterprise': 'wpa',
            'wpa2_enterprise': 'wpa2',
            'wpa3_enterprise': 'wpa3',
            'wpa_enterprise_mixed': 'wpa-mixed',
            'wpa2_enterprise_mixed': 'wpa3-mixed',
            'wps': 'psk',
        }
        # if encryption disabled return empty dict
        if not encryption or disabled or encryption['protocol'] == 'none':
            return {'encryption': 'none'}
        # otherwise configure encryption
        uci = encryption.copy()
        for option in ['protocol', 'key', 'cipher', 'disabled']:
            if option in uci:
                del uci[option]
        protocol = encryption['protocol']
        # default to protocol raw value in order
        # to allow customization by child classes
        uci['encryption'] = protocol_mapping.get(protocol, protocol)
        if protocol.startswith('wep'):
            uci['key'] = '1'
            uci['key1'] = encryption['key']
            # tell hostapd/wpa_supplicant key is not hex format
            if protocol == 'wep_open':
                uci['key1'] = 's:{0}'.format(uci['key1'])
        else:
            if (
                'enterprise' in protocol
                and 'eap_type' in uci
                and uci['eap_type'] == 'tls'
                and 'auth' in uci
            ):
                # remove auth if not needed
                # (not applicable to EAP-TLS)
                del uci['auth']
            if 'key' in encryption:
                uci['key'] = encryption['key']
        # add ciphers
        cipher = encryption.get('cipher')
        if cipher and protocol.startswith('wpa') and cipher != 'auto':
            uci['encryption'] += '+{0}'.format(cipher)
        return uci

    def to_netjson_loop(self, block, result, index):
        is_new = False
        interface = self.__get_netjson_interface(block)
        if not interface:
            is_new = True
            ifname = self.__netjson_wifi_get_ifname(block)
            interface = {'name': ifname, 'type': 'wireless'}
        wifi = self.__netjson_wifi(block, interface)
        interface['wireless'] = wifi
        if is_new:
            result.setdefault('interfaces', [])
            result['interfaces'].append(interface)
        return result

    def __netjson_wifi_get_ifname(self, block):
        """
        returns the ifname or alternatively returns
        the UCI block name as interface name
        (because ifname in wifi devices is optional)
        """
        return block.get('ifname', block['.name'].replace('wifi_', ''))

    def __netjson_wifi(self, wifi, interface):
        _name = wifi.pop('.name')
        if _name != self.__get_auto_name(interface):
            wifi['id'] = _name
        del wifi['.type']
        wifi['radio'] = wifi.pop('device')
        # convert UCI mode to NetJSON mode
        modes = {
            'ap': 'access_point',
            'sta': 'station',
            'adhoc': 'adhoc',
            'monitor': 'monitor',
            'mesh': '802.11s',
        }
        wifi['mode'] = modes[wifi['mode']]
        # convert 802.11 UCI attributes to NetJSON
        wifi_options = {
            'distance': 'ack_distance',
            'rts': 'rts_threshold',
            'frag': 'frag_threshold',
        }
        for uci_key, netjson_key in wifi_options.items():
            if uci_key not in wifi:
                continue
            wifi[netjson_key] = int(wifi.pop(uci_key))
        ifname = wifi.pop('ifname', interface['name'])
        if 'network' in wifi:
            if wifi['network'] in [ifname, interface.get('network')]:
                del wifi['network']
            else:
                wifi['network'] = wifi['network'].split()
        if 'macaddr' in wifi:
            interface['mac'] = wifi.pop('macaddr')
        # if interface is disabled wifi is also disabled
        if 'disabled' in wifi:
            interface['disabled'] = wifi.pop('disabled') == '1'
        self.__netjson_wifi_typecast(wifi)
        self.__netjson_encryption(wifi)
        return wifi

    def __netjson_wifi_typecast(self, wifi):
        for attr in [
            'hidden',
            'wds',
            'ft_over_ds',
            'ft_psk_generate_local',
            'ieee80211r',
            'rsn_preauth',
            'isolate',
            'doth',
            'wmm',
            'short_preamble',
            'start_disabled',
            'default_disabled',
        ]:
            if attr in wifi:
                wifi[attr] = wifi[attr] == '1'
        if 'reassociation_deadline' in wifi:
            try:
                wifi['reassociation_deadline'] = int(wifi['reassociation_deadline'])
            except ValueError:
                del wifi['reassociation_deadline']

    _encryption_keys = [
        'key',
        'server',
        'port',
        'wpa_group_rekey',
        'auth_server',
        'auth_port',
        'auth_secret',
        'auth_cache',
        'acct_port',
        'acct_server',
        'nasid',
        'ownip',
        'dae_client',
        'dae_port',
        'dae_secret',
        'dynamic_vlan',
        'vlan_naming',
        'vlan_tagged_interface',
        'vlan_bridge',
        'eap_type',
        'auth',
        'identity',
        'password',
        'ca_cert',
        'client_cert',
        'priv_key',
        'priv_key_pwd',
        'wps_config',
        'wps_device_name',
        'wps_device_type',
        'wps_label',
        'wps_manufacturer',
        'wps_pushbutton',
        'wps_pin',
    ]

    def __netjson_encryption(self, wifi):  # noqa: C901
        if 'encryption' not in wifi:
            return
        settings = {}
        wps = False
        # move encryption keys
        for key in self._encryption_keys:
            if key in wifi:
                settings[key] = wifi.pop(key)
                if key.startswith('wps_'):
                    wps = True
        # determine NetJSON protocol and cipher
        protocol = wifi.pop('encryption')
        # if encryption is diabled just set it to none and return
        if protocol == 'none':
            wifi['encryption'] = {'protocol': 'none'}
            return
        cipher = 'auto'
        if '+' in protocol:
            protocol, cipher = protocol.split('+', 1)
        if not wps:
            protocol_mapping = {
                'wep-open': 'wep_open',
                'wep-shared': 'wep_shared',
                'psk': 'wpa_personal',
                'psk2': 'wpa2_personal',
                'sae': 'wpa3_personal',
                'psk-mixed': 'wpa_personal_mixed',
                'sae-mixed': 'wpa2_personal_mixed',
                'wpa': 'wpa_enterprise',
                'wpa2': 'wpa2_enterprise',
                'wpa3': 'wpa3_enterprise',
                'wpa-mixed': 'wpa_enterprise_mixed',
                'wpa3-mixed': 'wpa2_enterprise_mixed',
            }
            settings['protocol'] = protocol_mapping[protocol]
            settings['cipher'] = cipher
        else:
            settings['protocol'] = 'wps'
        # wep key
        if protocol.startswith('wep'):
            index = settings['key']
            dict_key = 'key{0}'.format(index)
            key = wifi.pop(dict_key, '')
            if key.startswith('s:'):
                key = key[2:]
            settings['key'] = key
        # Management Frame Protection
        if 'ieee80211w' in wifi:
            settings['ieee80211w'] = wifi.pop('ieee80211w')
        # create NetJSON encryption object
        wifi['encryption'] = self.__netjson_encryption_typecast(settings)

    def __netjson_encryption_typecast(self, encryption):
        # type casting
        if 'port' in encryption:
            encryption['port'] = int(encryption['port'])
        if 'acct_port' in encryption:
            encryption['acct_port'] = int(encryption['acct_port'])
        if 'wps_label' in encryption:
            encryption['wps_label'] = encryption['wps_label'] == '1'
        if 'wps_pushbutton' in encryption:
            encryption['wps_pushbutton'] = encryption['wps_pushbutton'] == '1'
        return encryption

    def __get_netjson_interface(self, wifi):
        for interface in self.netjson.get('interfaces', []):
            ifname = self.__netjson_wifi_get_ifname(wifi)
            if interface['name'] == ifname:
                interface['type'] = 'wireless'
                return interface

    def to_netjson_clean(self, intermediate_data):
        result = super().to_netjson_clean(intermediate_data)
        return self.__fix_netjson_network(result)

    def __fix_netjson_network(self, result):
        """
        Figures out whether it should remove the network attribute
        From the netjson wifi interface (because it's redundant)
        """
        self._track_bridged_wifi(self.backend._intermediate_copy)
        for index, interface in enumerate(result):
            try:
                bridges = self._bridged_wifi[interface['ifname']]
            except KeyError:
                continue
            else:
                if bridges == interface.get('network', '').split(' '):
                    del result[index]['network']
        return result

    def _track_bridged_wifi(self, intermediate_data=None):
        """
        Keeps track of wireless interfaces which are members of
        bridges in order to automatically determine the "network"
        attribute value of the UCI or NetJSON configuration.
        """
        self._bridged_wifi = {}
        if not intermediate_data:
            intermediate_data = self.intermediate_data
        interfaces = intermediate_data.get('network', [])
        # Create a mapping of physical interface to bride interface name
        for interface in interfaces:
            if interface.get('type', None) != 'bridge':
                continue
            # Get list of bridge members
            try:
                bridge_members = self.__get_bridge_members(interface)
            except AttributeError:
                # Bridge interface does not contain bridge members.
                # Bridge is empty.
                continue
            bridge_name = interface['.name']
            if self.dsa:
                bridge_name = bridge_name.lstrip('device_')
            for physical_interface in bridge_members:
                # A physical interface can be a member of multiple
                # bridges. Hence, we create a list of bridge interfaces
                # for every physical interface.
                if physical_interface not in self._bridged_wifi:
                    self._bridged_wifi[physical_interface] = [bridge_name]
                elif bridge_name not in self._bridged_wifi[physical_interface]:
                    self._bridged_wifi[physical_interface].append(bridge_name)

    def __get_bridge_members(self, interface):
        if self.dsa and interface.get('ports', []):
            return interface.get('ports', [])
        return interface.get('ifname', None).split(' ')
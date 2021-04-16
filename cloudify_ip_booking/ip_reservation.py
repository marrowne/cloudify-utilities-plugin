import ipaddress
import platform


class IpReservation:
    def __init__(self, available=None, available_v4=None, available_v6=None):
        def _validate(param):
            if not isinstance(param, list):
                raise TypeError('available parameter should be a list!')

        self._available_v4 = []
        self._available_v6 = []

        if available:
            _validate(available)
            for addr in available:
                if type(ipaddress.ip_network(addr)) is ipaddress.IPv4Network:
                    self._available_v4.append(addr)
                elif type(ipaddress.ip_network(addr)) is ipaddress.IPv6Network:
                    self._available_v6.append(addr)
        else:
            if available_v4:
                _validate(available_v4)
                self._available_v4 = [ipaddress.ip_network(addr).compressed
                                      for addr
                                      in available_v4]
            if available_v6:
                _validate(available_v6)
                self._available_v6 = [ipaddress.ip_network(addr).compressed
                                      for addr
                                      in available_v6]

        self._available_v4 = self._available_v4 or ['0.0.0.0/0']
        self._available_v6 = self._available_v6 or ['::/0']

    @property
    def available(self):
        return self._available_v4 + self._available_v6

    @property
    def available_ipv4(self):
        return self._available_v4

    @property
    def available_ipv6(self):
        return self._available_v6

    def reserve(self, address):
        ip_network = ipaddress.ip_network(address)
        is_ip_reserved = False
        available = self._available_v4 \
            if ip_network.version == 4 else self._available_v6
        new_available = set()
        for network_str in available:
            network = ipaddress.ip_network(network_str)
            if ip_network.overlaps(network):
                result = network.address_exclude(ip_network)
                new_available = new_available.union(set(result))
                is_ip_reserved = True
            else:
                new_available.add(network)
        if ip_network.version == 4:
            self._available_v4 = [net.compressed for net in new_available]
        else:
            self._available_v6 = [net.compressed for net in new_available]
        return is_ip_reserved

    def free(self, address):
        ip_network = ipaddress.ip_network(address)
        if ip_network.version == 4:
            self._available_v4.append(ip_network.compressed)
        else:
            self._available_v6.append(ip_network.compressed)
        self.collapse_addresses()

    def reserve_range(self, from_address, to_address):
        reserved_nets = ipaddress.summarize_address_range(
            ipaddress.ip_address(from_address),
            ipaddress.ip_address(to_address)
        )
        v4_backup = self._available_v4
        v6_backup = self._available_v6
        for reserved in reserved_nets:
            if not self.reserve(reserved.compressed):
                # reserve unsuccessful -> rollback
                self._available_v4 = v4_backup
                self._available_v6 = v6_backup
                return False
        return True

    def free_range(self, from_address, to_address):
        freed_nets = ipaddress.summarize_address_range(
            ipaddress.ip_address(from_address),
            ipaddress.ip_address(to_address)
        )
        if ipaddress.ip_address(from_address).version == 4:
            self._available_v4.extend((net.compressed for net in freed_nets))
            print(self._available_v4)
        else:
            self._available_v6.extend((net.compressed for net in freed_nets))
        self.collapse_addresses()

    def is_free(self, address):
        ip_network = ipaddress.ip_network(address)
        available = self._available_v4 \
            if ip_network.version == 4 else self._available_v6
        for network_str in available:
            network = ipaddress.ip_network(network_str)
            if self._is_subnet_of(ip_network, network):
                return True
        return False

    def is_range_free(self, from_address, to_address):
        checked_nets = ipaddress.summarize_address_range(
            ipaddress.ip_address(from_address),
            ipaddress.ip_address(to_address)
        )
        for net in checked_nets:
            if not self.is_free(net.compressed):
                return False
        return True

    def collapse_addresses(self):
        v4_obj = [ipaddress.ip_network(net) for net in self._available_v4]
        self._available_v4 = [net.compressed for net
                              in ipaddress.collapse_addresses(v4_obj)]
        v6_obj = [ipaddress.ip_network(net) for net in self._available_v6]
        self._available_v6 = [net.compressed for net
                              in ipaddress.collapse_addresses(v6_obj)]

    @staticmethod
    def _is_subnet_of(a, b):
        if platform.sys.version_info.major >= 3 and \
                platform.sys.version_info.minor > 6:
            return a.subnet_of(b)
        else:  # workaround for Python < 3.7
            try:
                # Always false if one is v4 and the other is v6.
                if a._version != b._version:
                    raise TypeError(f"{a} and {b} are not of the same version")
                return (b.network_address <= a.network_address and
                        b.broadcast_address >= a.broadcast_address)
            except AttributeError:
                raise TypeError(f"Unable to test subnet containment "
                                f"between {a} and {b}")

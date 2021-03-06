'''
Created on 18 gru 2014

@author: ghalajko
'''

__lvs_version = None

import string
import os.path


if os.environ.has_key("DEV"):
    _IP_VS_FILE = '../../unittest/resource/ip_vs_2'
    _IP_VS_STAT_FILE = '../../unittest/resource/ip_vs_stats'
else:
    _IP_VS_FILE = '/proc/net/ip_vs'
    _IP_VS_STAT_FILE = '/proc/net/ip_vs_stats'

if not os.path.isfile(_IP_VS_FILE):
    raise RuntimeError("LVS is disabled. File \'"+_IP_VS_FILE+"\' not found.")

def ip_vs_stat():
    ipvs = []
    f = open(_IP_VS_STAT_FILE, 'rb')
    lines = f.read()
    data = lines.split('\n')
    v1 = [_hexToInt(x) for x in data[2].split()]
    v2 = [_hexToInt(x) for x in data[5].split()]
    data[2] = str_replace(data[2], data[2].split(), v1)
    data[5] = str_replace(data[5], data[5].split(), v2)

    for line in data:
        ipvs += [' ' + line + '\n']
    return ipvs

def ip_vs_parse():
    global __lvs_version
    v_endpoints = []
    with open(_IP_VS_FILE, 'rb') as f:
        if __lvs_version is None:
            __lvs_version = f.readline()
        else:
            next(f)

        # Skip 2 line heder
        next(f)
        next(f)

        current_v_edpoint = None

        for line in f:
            splited_line = line.split()
            if splited_line[0] == "->" and current_v_edpoint is not None:
                rs = RealServer(splited_line)
                current_v_edpoint.add_real_server(rs)
            else:
                current_v_edpoint = VirtualEndPoint(splited_line)
                v_endpoints.append(current_v_edpoint)
        
    return v_endpoints

def str_replace(s, old, new):
    for a, b in zip(old, new):
        s = s.replace(str(a), str(b))
    return s

def _hexToInt(hexstr):
    return int(hexstr,16)

def _parce_to_ip(hexip):
    ip_l = []
    for x in range(0, 4):
        pozs = x*2
        poze = pozs+2
        ip_l += [str(_hexToInt(hexip[pozs:poze]))]
    return string.join(ip_l,'.')

def _parce_to_port(hexip):
    splited_hexip = hexip.split(':')
    v = splited_hexip[1].lstrip('0')
    t = [v,'0'][len(v) <= 0]
    return str(_hexToInt(t))

class VirtualEndPoint(object):

    def __init__(self, args):
        self.mode = args[0]
        self.port = args[1]
        self.scheduler = args[2]
        if 3 < len(args):
            self.persistent = args[3]
            self.persistent_timeout = args[4]
            self.flags = args[5]
        else:
            self.persistent,self.persistent_timeout,self.flags = '','',''
        self.__real_servers = []
        if 'TCP' == self.mode:
            self.port = _parce_to_ip(self.port)+':'+_parce_to_port(self.port)
        elif 'FWM' == self.mode:
            self.port = str(_hexToInt(self.port))

    @property
    def real_servers(self):
        return self.__real_servers
    
    def sort_real_servers(self):
        self.__real_servers = sorted(self.__real_servers)

    def add_real_server(self, real_server):
        self.__real_servers.append(real_server)
        
    def __repr__(self):
        return  "(%s %s %s)" % (self.mode, self.port, ''.join(str(v) for v in self.__real_servers))

class RealServer(object):

    def __init__(self, args):
        self._ip = _parce_to_ip(args[1])
        self._port = _parce_to_port(args[1])
        self._forward_mode = args[2]
        self._weight = args[3]
        self._active_conn = args[4]
        self._inact_conn = args[5]

    def __repr__(self):
        return "(%s a=%s ina=%s)" % (self._ip,self._active_conn,self._inact_conn)

    def __cmp__(self, other):
        if hasattr(other, '_ip'):
            return cmp(self._ip,other._ip)

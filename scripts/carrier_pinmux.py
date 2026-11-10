"""Check carrier pins in compiled DTB properties, including default consumers."""
import struct
import re

def cells(value):
    if len(value) % 4:
        raise ValueError('Invalid DTB cell length')
    return struct.unpack('>'+str(len(value)//4)+'I', value)

def strings(value):
    return [s.decode() for s in value.rstrip(b'\0').split(b'\0')] if value else []

def enabled(nodes, path):
    parts = path.strip('/').split('/')
    return all(strings(nodes.get('/'+'/'.join(parts[:i]), {}).get('status', b'okay\0'))[0]
               in ('okay','ok') for i in range(len(parts)+1))

def audit_carrier_pinmux(nodes, config):
    phandles = {cells(p['phandle'])[0]:path for path,p in nodes.items() if 'phandle' in p}
    spi = strings(nodes.get('/aliases', {}).get('spi0', b''))
    if spi != ['/spi@ff500000'] or not enabled(nodes, spi[0]) or spi[0] not in nodes:
        raise ValueError('Carrier requires enabled SPI0 at /spi@ff500000')
    spi = spi[0]
    def pin_groups(path):
        groups = []
        for handle in cells(nodes[path].get('pinctrl-0', b'')):
            if handle not in phandles:
                raise ValueError('Unresolved default pinctrl handle')
            group = phandles[handle]
            values = cells(nodes[group].get('rockchip,pins', b''))
            if len(values) % 4:
                raise ValueError('Invalid Rockchip pin tuple')
            groups.extend((values[i],values[i+1],values[i+2],group) for i in range(0,len(values),4))
        return groups
    actual = {(b,l,f) for b,l,f,g in pin_groups(spi)}
    expected = {(1,17,4),(1,18,6),(1,16,4)}  # CLK/MOSI/CS0; never MISO on reset.
    if actual != expected:
        raise ValueError('Carrier SPI0 must claim only GPIO1_C1 CLK, C2 MOSI and C0 CS0; reset C3 must remain GPIO')
    device = spi+'/spidev@0'
    if device not in nodes or not enabled(nodes,device) or cells(nodes[device].get('reg',b'')) != (0,):
        raise ValueError('Carrier requires enabled spidev chip-select 0')
    if 'rockchip,spidev' not in strings(nodes[device].get('compatible',b'')):
        raise ValueError('Unexpected SPI0 user-space device binding')
    limit = cells(nodes[device].get('spi-max-frequency', b''))
    if len(limit) != 1 or limit[0] < 10_000_000:
        raise ValueError('Compiled SPI0 limit cannot support the carrier 10 MHz request')
    for path,p in nodes.items():
        if path.startswith(spi+'/') and path != device and enabled(nodes,path) and cells(p.get('reg',b'')) == (0,):
            raise ValueError('Another enabled SPI0 device competes for chip-select 0')
    protected = {(1,19),(1,20),(1,21),(1,22),(1,23),(1,24),(1,25),(0,4),(4,16),(4,17)}
    dormant = []
    for path,p in nodes.items():
        if not enabled(nodes,path):
            continue
        for bank,line,function,group in pin_groups(path):
            if (bank,line) not in protected:
                continue
            # The pinned SDK exposes a dormant sensor on the Down key. It must
            # stay unbound; enabling its driver can request/drive that GPIO.
            if (path == '/dht11_sensor' and (bank,line,function) == (1,23,0)
                    and strings(p.get('compatible',b'')) == ['dht11']
                    and config.get('CONFIG_DHT11') == 'n'):
                dormant.append({'node':path,'pin':'GPIO1_C7 / Down','driver':'CONFIG_DHT11=n'})
            else:
                raise ValueError(f'Carrier display/button pin claimed by enabled default consumer: {path} ({bank},{line},{function})')
    return {'spi0Node':spi,'spidevNode':device,'pins':sorted([list(p) for p in actual]),
            'resetMisoConflict':False,'compiledMaximumHz':limit[0],'requiredRuntimeHz':10_000_000,
            'dormantConsumers':dormant,
            'scope':'Compiled default pinctrl only; live GPIO ownership/pulls and runtime overlays require first-article checks'}

def audit_carrier_uart(nodes,config):
    """Reader UART2 pins and kernel console conflicts, not rootfs services."""
    expected='/serial@ff4c0000'
    if strings(nodes.get('/aliases',{}).get('serial2',b'')) != [expected] or expected not in nodes or not enabled(nodes,expected):
        raise ValueError('Carrier reader requires enabled UART2 / serial2')
    phandles={cells(p['phandle'])[0]:path for path,p in nodes.items() if 'phandle' in p}
    pins=[]
    for handle in cells(nodes[expected].get('pinctrl-0',b'')):
        if handle not in phandles:raise ValueError('Unresolved UART2 pinctrl')
        values=cells(nodes[phandles[handle]].get('rockchip,pins',b''))
        if len(values)%4:raise ValueError('Invalid UART2 pin tuple')
        pins.extend(tuple(values[i:i+3]) for i in range(0,len(values),4))
    if set(pins)!={(1,10,2),(1,11,2)}:raise ValueError('Reader UART2 must use GPIO1_B2/B3 mode 1 transfer pins')
    bootargs=' '.join(strings(nodes.get('/chosen',{}).get('bootargs',b'')))
    cmdline=config.get('CONFIG_CMDLINE','').strip('"')
    combined=bootargs+' '+cmdline
    if re.search(r'(?:^|\s)console=(?:ttyS2|ttyFIQ0)(?:[,\s]|$)',combined) or re.search(r'(?:^|\s)earlycon=\S*ff4c0000',combined,re.I):
        raise ValueError('UART2 reader conflicts with compiled serial console/early console')
    stdout=' '.join(strings(nodes.get('/chosen',{}).get('stdout-path',b'')))
    if stdout.split(':')[0] in ('serial2',expected) and config.get('CONFIG_SERIAL_8250_CONSOLE')!='n':
        raise ValueError('UART2 stdout can claim the reader console')
    dormant=[]
    for path,p in nodes.items():
        if not enabled(nodes,path) or 'rockchip,fiq-debugger' not in strings(p.get('compatible',b'')):continue
        if cells(p.get('rockchip,serial-id',b''))==(2,):
            if config.get('CONFIG_FIQ_DEBUGGER')!='n':raise ValueError('FIQ debugger can own the reader UART2')
            dormant.append({'node':path,'serialId':2,'driver':'CONFIG_FIQ_DEBUGGER=n'})
    return {'uartNode':expected,'alias':'serial2','pins':sorted([list(p) for p in pins]),
            'kernelConsoleConflict':False,'dormantConsumers':dormant,
            'scope':'Compiled UART pinmux/bootargs/config only; bootloader output, getty, driver installation and live PC/SC are not checked'}

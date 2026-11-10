import copy
import struct
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from carrier_pinmux import audit_carrier_pinmux,audit_carrier_uart

def cells(*values):
    return struct.pack('>'+str(len(values))+'I',*values)

class CarrierPinmuxTests(unittest.TestCase):
    def setUp(self):
        self.nodes = {'/':{}, '/aliases':{'spi0':b'/spi@ff500000\0'},
            '/spi@ff500000':{'pinctrl-0':cells(1,2,3),'status':b'okay\0'},
            '/spi@ff500000/spidev@0':{'reg':cells(0),'compatible':b'rockchip,spidev\0','spi-max-frequency':cells(50_000_000)},
            '/pinctrl/clk':{'phandle':cells(1),'rockchip,pins':cells(1,17,4,9)},
            '/pinctrl/mosi':{'phandle':cells(2),'rockchip,pins':cells(1,18,6,9)},
            '/pinctrl/cs':{'phandle':cells(3),'rockchip,pins':cells(1,16,4,9)}}

    def test_carrier_has_three_spi_pins_and_no_reset_claim(self):
        result = audit_carrier_pinmux(self.nodes,{})
        self.assertEqual(result['pins'],[[1,16,4],[1,17,4],[1,18,6]])

    def test_miso_on_reset_is_rejected(self):
        self.nodes['/pinctrl/mosi']['rockchip,pins'] += cells(1,19,6,9)
        with self.assertRaisesRegex(ValueError,'reset C3'):audit_carrier_pinmux(self.nodes,{})

    def test_framebuffer_cannot_share_cs0(self):
        self.nodes['/spi@ff500000/fbtft@0'] = {'reg':cells(0)}
        with self.assertRaisesRegex(ValueError,'competes'):audit_carrier_pinmux(self.nodes,{})
        self.nodes['/spi@ff500000/fbtft@0']['status'] = b'disabled\0'
        audit_carrier_pinmux(self.nodes,{})

    def test_down_key_dht_consumer_requires_disabled_driver(self):
        self.nodes['/dht11_sensor'] = {'compatible':b'dht11\0','pinctrl-0':cells(4)}
        self.nodes['/pinctrl/dht'] = {'phandle':cells(4),'rockchip,pins':cells(1,23,0,9)}
        for value in ('y','m',None):
            with self.assertRaisesRegex(ValueError,'claimed'):audit_carrier_pinmux(self.nodes,{'CONFIG_DHT11':value})
        result = audit_carrier_pinmux(self.nodes,{'CONFIG_DHT11':'n'})
        self.assertEqual(len(result['dormantConsumers']),1)

    def test_disabled_spi_and_low_clock_limit_fail(self):
        self.nodes['/spi@ff500000']['status'] = b'disabled\0'
        with self.assertRaises(ValueError):audit_carrier_pinmux(self.nodes,{})
        self.nodes['/spi@ff500000']['status'] = b'okay\0'
        self.nodes['/spi@ff500000/spidev@0']['spi-max-frequency'] = cells(1_000_000)
        with self.assertRaises(ValueError):audit_carrier_pinmux(self.nodes,{})

class CarrierUartTests(unittest.TestCase):
    def setUp(self):
        self.nodes={'/':{},'/aliases':{'serial2':b'/serial@ff4c0000\0'},
            '/serial@ff4c0000':{'pinctrl-0':cells(7)},
            '/pinctrl/uart':{'phandle':cells(7),'rockchip,pins':cells(1,10,2,9,1,11,2,9)}}
    def test_reader_uart_pins(self):
        self.assertEqual(audit_carrier_uart(self.nodes,{})['pins'],[[1,10,2],[1,11,2]])
    def test_serial_console_and_earlycon_are_rejected(self):
        for text in ('console=ttyS2,115200','console=ttyFIQ0','earlycon=uart8250,mmio32,0xff4c0000'):
            self.nodes['/chosen']={'bootargs':text.encode()+b'\0'}
            with self.assertRaises(ValueError):audit_carrier_uart(self.nodes,{})
        self.nodes.pop('/chosen')
        with self.assertRaises(ValueError):audit_carrier_uart(self.nodes,{'CONFIG_CMDLINE':'"rootwait console=ttyS2,115200"'})
    def test_fiq_requires_disabled_driver(self):
        self.nodes['/fiq-debugger']={'compatible':b'rockchip,fiq-debugger\0','rockchip,serial-id':cells(2)}
        for value in ('y','m',None):
            with self.assertRaises(ValueError):audit_carrier_uart(self.nodes,{'CONFIG_FIQ_DEBUGGER':value})
        self.assertEqual(len(audit_carrier_uart(self.nodes,{'CONFIG_FIQ_DEBUGGER':'n'})['dormantConsumers']),1)
    def test_wrong_uart_mux_is_rejected(self):
        self.nodes['/pinctrl/uart']['rockchip,pins']=cells(4,0,2,9,4,1,2,9)
        with self.assertRaises(ValueError):audit_carrier_uart(self.nodes,{})

if __name__ == '__main__':unittest.main()

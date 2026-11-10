"""GPIO label discovery with sparse/reordered device indices; no GPIO hardware."""
import importlib.util,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('gpio_bank_profile',ROOT/'scripts/configure-image-io-profile.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)

class GpioBankAliasTests(unittest.TestCase):
 def fixture(self,dev,labels):
  for index in labels:(dev/f'gpiochip{index}').touch()
  return lambda p:{'label':labels[int(p.name.removeprefix('gpiochip'))],'lines':32}
 def test_mini_bank4_uses_device3_and_is_idempotent(self):
  with tempfile.TemporaryDirectory() as tmp:
   dev=Path(tmp);reader=self.fixture(dev,{0:'gpio0',1:'gpio1',2:'gpio3',3:'gpio4'})
   result=helper.create_gpio_aliases(dev,reader)
   self.assertEqual((dev/'gpiochip-bank4').readlink(),Path('gpiochip3'))
   self.assertFalse((dev/'gpiochip4').exists());self.assertFalse(result['gpioLinesRequested'])
   self.assertEqual(helper.create_gpio_aliases(dev,reader),result)
 def test_upstream_numeric_symlink_is_not_counted_twice(self):
  with tempfile.TemporaryDirectory() as tmp:
   dev=Path(tmp);reader=self.fixture(dev,{0:'gpio0',1:'gpio1',2:'gpio3',3:'gpio4'})
   (dev/'gpiochip4').symlink_to('gpiochip3')
   result=helper.create_gpio_aliases(dev,reader)
   self.assertEqual((dev/'gpiochip-bank4').readlink(),Path('gpiochip3'))
   self.assertEqual((dev/'gpiochip4').readlink(),Path('gpiochip3'))
   self.assertEqual(helper.create_gpio_aliases(dev,reader),result)
 def test_reordered_devices_follow_labels(self):
  with tempfile.TemporaryDirectory() as tmp:
   dev=Path(tmp);reader=self.fixture(dev,{2:'gpio0',7:'gpio1',1:'gpio4'})
   helper.create_gpio_aliases(dev,reader)
   self.assertEqual((dev/'gpiochip-bank0').readlink(),Path('gpiochip2'))
   self.assertEqual((dev/'gpiochip-bank1').readlink(),Path('gpiochip7'))
   self.assertEqual((dev/'gpiochip-bank4').readlink(),Path('gpiochip1'))
 def test_ambiguous_or_missing_bank_fails_before_alias_writes(self):
  for labels in ({0:'gpio0',1:'gpio1'},{0:'gpio0',1:'gpio1',3:'gpio4',4:'gpio4'}):
   with tempfile.TemporaryDirectory() as tmp:
    dev=Path(tmp);reader=self.fixture(dev,labels)
    with self.assertRaises(ValueError):helper.create_gpio_aliases(dev,reader)
    self.assertEqual(list(dev.glob('gpiochip-bank*')),[])
 def test_existing_regular_file_is_preserved(self):
  with tempfile.TemporaryDirectory() as tmp:
   dev=Path(tmp);reader=self.fixture(dev,{0:'gpio0',1:'gpio1',3:'gpio4'})
   (dev/'gpiochip-bank4').write_text('public fixture')
   with self.assertRaises(ValueError):helper.create_gpio_aliases(dev,reader)
   self.assertEqual((dev/'gpiochip-bank4').read_text(),'public fixture')
   self.assertFalse((dev/'gpiochip-bank0').exists())
 def test_chip_info_uses_metadata_ioctl_without_line_requests(self):
  def ioctl(fd,request,buffer,mutate):
   self.assertEqual(request,0x8044B401);self.assertTrue(mutate)
   buffer[:]=struct.pack('32s32sI',b'gpiochip3',b'gpio4',32)
  with patch.object(helper.os,'open',return_value=17),patch.object(helper.os,'close') as close,patch.object(helper.fcntl,'ioctl',side_effect=ioctl):
   self.assertEqual(helper.gpio_chip_info('/dev/gpiochip3'),{'name':'gpiochip3','label':'gpio4','lines':32})
  close.assert_called_once_with(17)

if __name__=='__main__':unittest.main()

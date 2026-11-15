# SPDX-License-Identifier: MIT
from seedsigner_port.controller import Controller
from seedsigner_port.view_core import MainMenuView,ErrorView,UnhandledExceptionView
from seedsigner_port.view_scan import ScanView
from seedsigner_port.view_seed import SeedFinalizeView,SeedOptionsView
from seedsigner_port.renderer import Renderer
from seedsigner_port.app_screens import SeedFinalizeScreen,SeedOptionsScreen
from seedsigner_port.seed import Seed
from seedsigner_port.navigation import Destination
from seedsigner_port.decode_platform import FeatureUnavailable
import ui
controller=Controller.get_instance()
assert controller is Controller.get_instance()
assert controller.storage.num_seeds()==0
assert not controller.hardware_rng_is_healthy
main=MainMenuView()
assert not main.has_redirect
scan=ScanView()
assert not scan.decoder.is_complete
controller.storage.set_pending_seed(Seed(('abandon '*11+'about').split()))
view=SeedFinalizeView()
assert view.fingerprint=='73c5da0a'
renderer=Renderer.get_instance()
renderer.session.show_screen(SeedFinalizeScreen,{'fingerprint':view.fingerprint,'button_data':[view.FINALIZE]})
ui.key(10,True);ui.key(10,False)
assert renderer.session.screen_result(ui.event())==0
seed=controller.storage.finalize_pending_seed()
view=SeedOptionsView(seed)
renderer.session.show_screen(SeedOptionsScreen,{'fingerprint':seed.get_fingerprint(),'button_data':[view.SCAN_PSBT,view.EXPORT_XPUB,view.BACKUP]})
ui.key(20,True);ui.key(20,False);ui.key(10,True);ui.key(10,False)
assert renderer.session.screen_result(ui.event())==1000
error=UnhandledExceptionView(['FeatureUnavailable','public fixture','Unsupported public test option'])
assert not error.has_redirect
controller.storage.seeds[0].wipe();controller.storage.seeds=[]
ui.overlays(0,0)
renderer.session.show_screen('MainMenuScreen',{'title':'Home','button_data':[main.SCAN,main.SEEDS,main.TOOLS,main.SETTINGS]})
print('@@PASS original-view-init-real-finalize-options-events')

"""Original Controller startup/menu/back-stack with native Renderer, temporary deployment.

Startup interstitials are explicitly skipped; no claim of full startup parity.
Only rendering and scripted input are substituted. No View initialization or
Controller methods/models/health-worker methods are replaced.
"""
import json,sys,tempfile,time,os
from resources import process_snapshot
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),'/opt/src']
from seedsigner.models.settings import Settings
from seedsigner.models.settings_definition import SettingsConstants as C
from seedsigner.gui.renderer import Renderer
from seedsigner.views.view import View
from runtime import Runtime,install_view_dispatch
from renderer_bridge import install as install_renderer
from luckfox import LuckfoxHardware
class Buttons:
    def load(self,keys):self.keys=keys;self.start=None
    def __call__(self):
        now=time.monotonic()
        if self.start is None:self.start=now
        t=now-self.start-.3
        if t<0:return set()
        period=.15 if '--hardening' in sys.argv or '--network-fixture' in sys.argv else .4
        i=int(t/period)
        if i>=len(self.keys):
            if t>len(self.keys)*period+10:raise TimeoutError('Controller navigation stalled')
            return set()
        return {self.keys[i]} if t%period<period*.55 else set()
with tempfile.TemporaryDirectory(prefix='lvgl-controller-test-') as temporary:
    Settings.SETTINGS_FILENAME=str(Path(temporary)/'settings.json')
    settings=Settings.get_instance()
    settings.set_value(C.SETTING__PERSISTENT_SETTINGS,C.OPTION__DISABLED,save=False)
    settings.set_value(C.SETTING__WIPE_TIMER,C.WIPE_TIMER__DISABLED,save=False)
    hardware=LuckfoxHardware();buttons=Buttons();public_frame=bytearray(115200)
    def pixels(area,data):
        x1,y1,x2,y2=area;stride=(x2-x1+1)*2
        for row,y in enumerate(range(y1,y2+1)):public_frame[(y*240+x1)*2:(y*240+x2+1)*2]=data[row*stride:(row+1)*stride]
        hardware.pixels(area,data)
    runtime=Runtime(sys.argv[1],pixels,buttons,activity_sink=hardware.buttons.update_last_input_time)
    restore=install_view_dispatch(runtime,'/opt/src',Path(__file__).parent/'source-guards.json')
    restore_renderer=install_renderer(runtime,hardware,Renderer)
    original_initialize=View._initialize
    controller=None;seen=[];home_count=0;snapshots=[];version_scope=None;battery_scope=None;network_scope=None
    original_clear=runtime.clear
    def clear():
        if '--startup' in sys.argv and seen and seen[-1]=='OpeningSplashScreen':
            Path('/tmp/lvgl-public-startup.rgb565').write_bytes(public_frame)
        return original_clear()
    runtime.clear=clear
    original_run=runtime.run
    target='MemoryInfoScreen' if '--memory-info' in sys.argv else ('SystemInfoScreen' if '--system-info' in sys.argv else 'VersionScreen')
    if '--network-fixture' in sys.argv:target='ToolsNetworkInfoScreen'
    elif '--network-absent' in sys.argv:target='ErrorScreen'
    if '--donate' in sys.argv:target='DonateScreen'
    if '--hardening' in sys.argv:target='HardeningTestScreen'
    if '--battery-fixture' in sys.argv:target='BatteryInfoScreen'
    elif '--battery-not-detected' in sys.argv:target='WarningScreen'
    captured_network=[False]
    def input_keys():
        if target=='ToolsNetworkInfoScreen' and not captured_network[0]:
            Path('/tmp/lvgl-public-network.rgb565').write_bytes(bytes(public_frame));captured_network[0]=True
        if target=='MemoryInfoScreen' and getattr(runtime,'memory_info_stats',{}).get('samples',0)<3:return set()
        if target=='BatteryInfoScreen' and getattr(runtime,'battery_info_stats',{}).get('samples',0)<2:return set()
        return buttons()
    runtime.read_buttons=input_keys
    pages_seen=[];report_identity=[None]
    def run(screen,args):
        name=screen.__name__;seen.append(name)
        snapshots.append(dict(screen=name,python=process_snapshot(os.getpid()),native=process_snapshot(runtime.host.child.pid)))
        if name==target:
            if target in ('HardeningTestScreen','ToolsNetworkInfoScreen'):
                if report_identity[0] is None:report_identity[0]=args['paged_info']
                count=len(report_identity[0]);index=len(pages_seen)
                expected=index if index<count else count-2-(index-count)
                assert args['page_num']==expected,(index,args['page_num'],expected)
                pages_seen.append(args['page_num'])
                assert args['paged_info'] is report_identity[0]
                buttons.load((['KEY_UP'] if target=='ToolsNetworkInfoScreen' and len(pages_seen)>len(report_identity[0]) else ['KEY_DOWN'])*18+['KEY_PRESS'])
            else:buttons.load(['KEY_UP']*18+['KEY_PRESS'])
        elif name=='ButtonListScreen' or (name=='MainMenuScreen' and (('--network-fixture' in sys.argv) or ('--network-absent' in sys.argv))):raise StopFlowBasedTest()
        else:raise FlowBasedTestException('Unexpected info route '+name)
        return original_run(screen,args)
    runtime.run=run
    try:
        from seedsigner.controller import Controller,StopFlowBasedTest,FlowBasedTestException
        if '--small-ram' in sys.argv:
            from startup_policy import install as install_startup
            install_startup('/opt/src','/usr/lib/shieldsigner-camera/python')
        controller=Controller.get_instance()
        controller.boot_failover_cleared=True # Test must not touch boot-counter MMIO.
        assert controller.wipe_timer_thread.is_alive() and controller.rng_monitor_thread.is_alive()
        assert Renderer.get_instance().canvas is None and Renderer.get_instance().draw is None
        activity_before=hardware.buttons.last_input_time
        from seedsigner.views.settings_views import VersionView,SystemInfoView,MemoryInfoView,BatteryInfoView,HardeningTestView,DonateView
        from seedsigner.views.view import Destination
        if target=='VersionScreen':
            from seedsigner.helpers.version import VersionUtils
            from diagnostic_scope import attribute
            fixture=Path(temporary)/'version.json'
            fixture.write_text(json.dumps(dict(name='v0.0.0-lvgl-fixture',fork='public/fixture',short_commit_hash='1234567',timestamp='2026-10-30T00:00:00+00:00')))
            version_scope=attribute(VersionUtils,'_get_version_file_path',classmethod(lambda cls:str(fixture)));version_scope.__enter__()
        if '--battery-fixture' in sys.argv:
            from types import SimpleNamespace
            from seedsigner.hardware.battery_hat import BatteryHat
            from diagnostic_scope import attribute
            fixture=SimpleNamespace(is_enabled=lambda:True,detected=True,get_voltage=lambda:3.7,get_current=lambda:-250,get_power=lambda:0.925,get_percent=lambda:42.3,get_curve_label=lambda:'public fixture')
            battery_scope=attribute(BatteryHat,'get_instance',classmethod(lambda cls:fixture));battery_scope.__enter__()
        initial=BatteryInfoView if '--battery-fixture' in sys.argv or '--battery-not-detected' in sys.argv else (MemoryInfoView if '--memory-info' in sys.argv else (SystemInfoView if '--system-info' in sys.argv else VersionView))
        if '--donate' in sys.argv:initial=DonateView
        if '--hardening' in sys.argv:initial=HardeningTestView
        if '--network-fixture' in sys.argv or '--network-absent' in sys.argv:
            from seedsigner.views.tools_views import ToolsNetworkInfoView
            initial=ToolsNetworkInfoView
            if '--network-fixture' in sys.argv:
                from diagnostic_scope import attribute
                report='Iface   State   Address\n'+''.join('test%02d  UP      192.0.2.%d\n'%(i,i+1) for i in range(16))
                network_scope=attribute(ToolsNetworkInfoView,'_get_network_info',lambda self:report);network_scope.__enter__()
        controller.start(initial_destination=Destination(initial),skip_startup_interstitials=True)
        assert View._initialize is original_initialize
        if target in ('HardeningTestScreen','ToolsNetworkInfoScreen'):
            count=len(report_identity[0]);expected=list(range(count))
            if target=='ToolsNetworkInfoScreen':expected+=list(range(count-2,0,-1))
            assert pages_seen==expected,pages_seen
            assert seen==[target]*len(pages_seen)+(['MainMenuScreen'] if target=='ToolsNetworkInfoScreen' else ['ButtonListScreen']),seen
        else:assert seen==[target,'MainMenuScreen' if '--network-absent' in sys.argv else 'ButtonListScreen'],seen
        if target=='BatteryInfoScreen':assert runtime.battery_info_stats['samples']>=2
        if target=='MemoryInfoScreen':assert runtime.memory_info_stats['samples']>=3
        assert hardware.buttons.last_input_time>activity_before
        assert controller.storage.num_seeds()==0
        assert controller.storage2 is not None
        for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
            thread.join(3);assert not thread.is_alive()
        assert not Path(Settings.SETTINGS_FILENAME).exists()
        print(json.dumps(dict(passed=True,pagedReportPagesTraversed=len(pages_seen),pagedReportReused=bool(pages_seen),networkOutputInjected=('--network-fixture' in sys.argv),batterySensorInjected=('--battery-fixture' in sys.argv),batteryRefreshStats=getattr(runtime,'battery_info_stats',None),memoryRefreshStats=getattr(runtime,'memory_info_stats',None),versionMetadataPathInjected=(target=='VersionScreen'),originalController=True,originalViewInitialization=True,screenSequence=seen,nativeRendererNoPILCanvas=True,activityTimerUpdated=True,resourceSnapshots=snapshots,resourceComparison=False,mandatoryStoragesInitialized=True,wipeAndRngWorkersStartedAndStopped=True,startupInterstitialsSkipped=('--startup' not in sys.argv),smallRamPolicyEnabled=('--small-ram' in sys.argv),physicalDisplay=True,physicalButtons=False,persistentSettingsWritten=False)))
    finally:
        if controller is not None:
            for thread in (controller.wipe_timer_thread,controller.rng_monitor_thread):
                if thread is not None:thread.stop();thread.join(3)
        if network_scope is not None:network_scope.__exit__(None,None,None)
        if battery_scope is not None:battery_scope.__exit__(None,None,None)
        if version_scope is not None:version_scope.__exit__(None,None,None)
        restore_renderer();restore();runtime.close();hardware.close()

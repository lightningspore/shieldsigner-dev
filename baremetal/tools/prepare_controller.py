# SPDX-License-Identifier: MIT
"""Preserve original foreground Controller loop with explicit native OS boundaries."""

import pyformat  # noqa: F401  (formats generated Python on write)
import ast, hashlib, json, copy
from prepare_views import LazyPort, root, source, lock

path = source / 'src/seedsigner/controller.py'
raw = path.read_bytes()
tree = ast.parse(raw)
controller = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Controller')
methods = {n.name: n for n in controller.body if isinstance(n, ast.FunctionDef)}
configure = '''
@classmethod
def configure_instance(cls):
    if cls._instance:raise Exception('Instance already configured')
    from seedsigner_port.renderer import Renderer
    from seedsigner_port.scan_screen import NativeVideoStream
    from seedsigner_port.app_services import ScreensaverScreen
    import ui
    controller=object.__new__(cls)
    cls._instance=controller
    controller.settings=Settings.get_instance()
    controller._storage=SeedStorage()
    controller._storage2=EncryptedQRStorage()
    controller._camera=NativeVideoStream()
    Renderer.get_instance()
    controller.back_stack=BackStack()
    controller.screensaver_activation_ms=120000
    controller.screensaver=ScreensaverScreen()
    ui.overlays(0,controller.screensaver_activation_ms)
    return controller
'''
handle = '''
def handle_exception(self,e):
    from seedsigner.views.view import UnhandledExceptionView
    import machine
    location=machine.exception_location(e)
    line_info=''
    if location is not None:line_info='{}, {} in {}'.format(location[0],location[1],location[2])
    return Destination(UnhandledExceptionView,view_args={'error':[type(e).__name__,line_info,str(e)]},clear_history=True)
'''
service = '''
def service(self):
    from seedsigner_port import clock
    from seedsigner_port.hardware_buttons import HardwareButtons
    minutes=self.settings.get_value(SettingsConstants.SETTING__WIPE_TIMER)
    if minutes and minutes!=SettingsConstants.WIPE_TIMER__DISABLED:
        self.wipe_timer_ms=minutes*60000
        buttons=HardwareButtons.get_instance()
        if int(clock.time()*1000)-buttons.last_input_time>self.wipe_timer_ms:
            buttons.update_last_input_time()
            self.handle_wipe_timeout()
'''
replacements = {n.name: n for n in ast.parse(configure + handle + service).body}
replacements['camera'] = ast.parse('@property\ndef camera(self):return self._camera\n').body[0]
controller.body = [
    replacements.get(n.name, n) if isinstance(n, ast.FunctionDef) else n
    for n in controller.body
    if not (isinstance(n, ast.FunctionDef) and n.name == '_load_block_anchor')
]
controller.body.append(replacements['service'])
start = next(n for n in controller.body if isinstance(n, ast.FunctionDef) and n.name == 'start')
# Keep the complete actual foreground try/while/finally. Replace only OS startup.
main = next(n for n in start.body if isinstance(n, ast.Try))
prefix = ast.parse('''
from seedsigner.views import MainMenuView,BackStackView,RemoveMicroSDWarningView
from seedsigner.gui.toast import RemoveSDCardToastManagerThread
startup_error_destination=None
if not skip_startup_interstitials:
    try:
        from seedsigner_port.view_splash import OpeningSplashView
        from seedsigner_port.view_development import DeveloperOSWarningView
        OpeningSplashView().run()
        DeveloperOSWarningView().run()
    except Exception as e:
        startup_error_destination=self.handle_exception(e)
''').body
# Smartcard application is explicitly outside this task; retain Home cleanup.
for n in ast.walk(main):
    if isinstance(n, ast.If) and ast.unparse(n.test) == 'next_destination.View_cls == MainMenuView':
        if (
            n.orelse
            and isinstance(n.orelse[0], ast.If)
            and 'ToolsSmartcardMenuView' in ast.unparse(n.orelse[0].test)
        ):
            n.orelse = []
start.body = prefix + [main]
# Native foreground inactivity unwinds Python and camera finally blocks before Home.
wipe = next(
    n for n in controller.body if isinstance(n, ast.FunctionDef) and n.name == 'handle_wipe_timeout'
)
wipe.body[-1] = ast.parse('raise NativeIdleWipe()').body[0]
reset = next(
    n
    for n in controller.body
    if isinstance(n, ast.FunctionDef) and n.name == 'reset_screensaver_timeout'
)
reset.body += ast.parse('import ui\nui.overlays(3)').body
bindings = {
    'time': ('seedsigner_port.clock', None),
    'BackStack': ('seedsigner_port.navigation', 'BackStack'),
}
port = LazyPort(tree, 'seedsigner.controller', bindings=bindings)
controller = port.visit(controller)
start = next(n for n in controller.body if isinstance(n, ast.FunctionDef) and n.name == 'start')
for n in ast.walk(start):
    if isinstance(n, ast.Try) and any(
        any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == 'handle_exception'
            for body in h.body
            for call in ast.walk(body)
        )
        for h in n.handlers
    ):
        n.handlers = [
            h
            for h in n.handlers
            if not (isinstance(h.type, ast.Name) and h.type.id == 'FeatureUnavailable')
        ]
    if isinstance(n, ast.Try) and any(
        isinstance(h.type, ast.Name) and h.type.id == 'BaseException' for h in n.handlers
    ):
        n.handlers = [
            h
            for h in n.handlers
            if not (isinstance(h.type, ast.Name) and h.type.id == 'FeatureUnavailable')
        ]
        index = next(
            i
            for i, h in enumerate(n.handlers)
            if isinstance(h.type, ast.Name) and h.type.id == 'BaseException'
        )
        n.handlers.insert(
            index,
            ast.ExceptHandler(
                type=ast.Name(id='NativeIdleWipe', ctx=ast.Load()),
                name=None,
                body=ast.parse(
                    "next_destination=Destination(_dependency('seedsigner.views','MainMenuView'),clear_history=True)"
                ).body,
            ),
        )
classes = [
    port.visit(copy.deepcopy(n))
    for n in tree.body
    if isinstance(n, ast.ClassDef) and n.name in ('StopFlowBasedTest', 'FlowBasedTestException')
]
out = root / 'app/seedsigner_port/controller.py'
header = '# Copyright2021 SeedSigner; MIT, see ../LICENSE.SeedSigner\n# Original foreground Controller; reviewed native setup/error/service boundaries.\nfrom seedsigner_port.decode_platform import dependency as _dependency,FeatureUnavailable\nfrom seedsigner_port.navigation import Destination\nfrom seedsigner_port.app_services import NativeIdleWipe\n'
out.write_text(
    header
    + ast.unparse(
        ast.fix_missing_locations(ast.Module(body=classes + [controller], type_ignores=[]))
    )
    + '\n'
)
(root / 'app/controller-provenance.json').write_text(
    json.dumps(
        {
            'application': lock,
            'sourceSha256': hashlib.sha256(raw).hexdigest(),
            'outputSha256': hashlib.sha256(out.read_bytes()).hexdigest(),
            'boundaries': [
                'Synchronous real native services/storage instead of OS/background import/RNG threads',
                'Camera owned persistent native stream',
                'Actual original splash/development warning via native screens',
                'Original foreground dispatch/history/error cleanup loop retained; smartcard menu branch omitted per scope',
                'Cooperative actual inactivity timer; original wipe cleanup then NativeIdleWipe unwind',
                'Native actual exception metadata replaces CPython traceback formatting without console output',
                'No file-based block anchor refresh; original built-in advisory constants retained',
            ],
        },
        indent=2,
    )
    + '\n'
)

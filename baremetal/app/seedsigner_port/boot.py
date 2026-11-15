# SPDX-License-Identifier: MIT
"""Foreground app entry and USB-interrupt cleanup; no OS or storage startup."""
running=False
starts=0
last_exit='never'
last_screen=None

def run():
    global running,starts,last_exit,last_screen
    if running:raise RuntimeError('App already running')
    from seedsigner_port.controller import Controller
    from seedsigner_port.renderer import Renderer
    controller=Controller.get_instance()
    renderer=Renderer.get_instance()
    running=True;starts+=1;last_exit='running';last_screen=None
    try:
        try:controller.start()
        finally:
            last_screen=renderer.session.current
            try:controller.camera.stop_video_stream_mode()
            finally:renderer.display_blank_screen()
    except BaseException as error:
        # Retain only a type name, never exception text or payload references.
        last_exit=type(error).__name__
        raise
    else:last_exit='returned'
    finally:running=False

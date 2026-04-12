import asyncio
import sys

from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop

from config import HEAD_BASE_ADDR, PAR_BASE_ADDR, STROBE_BASE_ADDR
from dmx import DmxController
from fixture import MovingHead, ParGroup, StrobeLight
from link_sync import LinkSync
from show_engine import ShowEngine
from ui.main_window import MainWindow

FPS = 30


async def run(window: MainWindow, engine: ShowEngine):
    link = LinkSync()
    controller = DmxController()
    head = MovingHead(HEAD_BASE_ADDR)
    strobe = StrobeLight(STROBE_BASE_ADDR)
    pars = ParGroup(PAR_BASE_ADDR)
    head.lamp_on()
    head.dimmer = 255

    window.set_head(head)
    window.set_strobe(strobe)
    window.set_pars(pars)

    engine.advance()

    while True:
        info = link.read()

        if link.poll_song_changed():
            engine.advance()

        engine.tick(head, strobe, pars, info.beat, info.tempo)

        controller.update(head)
        controller.update(strobe)
        controller.update(pars)
        await controller.send()

        window.beat_panel.update_display(info)

        await asyncio.sleep(1 / FPS)


def main():
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    engine = ShowEngine()
    window = MainWindow(engine)
    window.show()

    loop.create_task(run(window, engine))

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()

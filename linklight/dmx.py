import asyncio

import requests

from config import DMX_UNIVERSE, OLA_HOST, OLA_PORT


class DmxController:
    def __init__(
        self,
        universe: int = DMX_UNIVERSE,
        ola_host: str = OLA_HOST,
        ola_port: int = OLA_PORT,
    ):
        self.universe = universe
        self._url = f"http://{ola_host}:{ola_port}/set_dmx"
        self._data = [0] * 512

    def update(self, fixture):
        for addr, value in fixture.get_channel_values().items():
            self._data[addr - 1] = value

    async def send(self):
        await asyncio.to_thread(self._send_sync)

    def _send_sync(self):
        try:
            resp = requests.post(self._url, data={
                "u": self.universe,
                "d": ",".join(str(v) for v in self._data),
            }, timeout=2)
            if resp.status_code != 200:
                print(f"[dmx] OLA error {resp.status_code}: {resp.text}")
        except requests.ConnectionError as e:
            print(f"[dmx] OLA connection failed: {e}")

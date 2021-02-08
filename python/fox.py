import vim

import asyncio as aio
import threading
import janus

from client import Client


class Plugin(threading.Thread):
    def __init__(self, vimbuf, *args, **kws):
        super().__init__(*args, **kws)

        self.vimbuf = vimbuf
        self._sock_addr = '/tmp/foxdot.sock'

    def run(self):
        self.loop = loop = aio.new_event_loop()
        aio.set_event_loop(loop)

        aio.run(self._main())

    async def _main(self):
        self._q = janus.Queue()
        r, w = await self._connect_backend()
        self.r, self.w = r, w

        # welcome
        self.vimbuf[0] = 'FoxDot initialized 𝄞'
        self.vimbuf.append('')

        tasks = [
            self._vim_socket(),
            self._socket_vim(),
        ]

        await aio.wait(tasks)

    async def _connect_backend(self):
        while True:
            try:
                r, w = await aio.open_unix_connection(self._sock_addr)
            except:
                await aio.sleep(1)
            else:
                return r, w

    async def _vim_socket(self):
        while True:
            code = await self._q.async_q.get()
            code = code.strip('\n') + '\n\n'
            self.w.write(code.encode())
            await self.w.drain()
            self._q.async_q.task_done()

    async def _socket_vim(self):
        while True:
            code = (await getblock(self.r)).decode()
            if not code:
                return

            code = code.strip('\n') + '\n'
            lines = [f'... {l}' if l else l for l in code.split('\n')]
            lines[0].replace('... ', '>>>')
            self.vimbuf.append(lines)

    def sendcode(self, code):
        self._q.sync_q.put(code)


async def getblock(stream):
    lines = []
    while (line := await stream.readline()):
        lines.append(line)
        if line == b'\n':
            return b''.join(lines)

    return b''


plug = None

def start():
    global plug

    # launch backend
    backend = threading.Thread(
        target=lambda: aio.run(Client().main()),
        daemon=True
    )
    backend.start()

    # create new window on the right
    vim.command('rightbelow vertical new')
    buf = vim.current.window.buffer
    vim.command('wincmd p')

    # launch plugin
    plug = Plugin(buf, daemon=True)
    plug.start()

def sendcode():
    buf = vim.current.window.buffer
    lineno, col = vim.current.window.cursor
    top = bot = lineno - 1

    while top > -1 and buf[top]:
        top -= 1
    while bot < len(buf) and buf[bot]:
        bot += 1

    code = '\n'.join(buf[top:bot])
    plug.sendcode(code)

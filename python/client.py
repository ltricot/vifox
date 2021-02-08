import socketio

from asyncio import subprocess as sp
import asyncio as aio


async def getblock(stream):
    lines = []
    while (line := await stream.readline()):
        lines.append(line)
        if line == b'\n':
            return b''.join(lines)

    return b''

class Client:
    def __init__(self):
        # for documentation purposes
        self.sc = None
        self.fd = None
        self.r, self.w = None, None

    async def sclang(self):
        self.sc = proc = await sp.create_subprocess_shell(
            'sclang',
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )

        # start foxdot sc extension (udp server)
        proc.stdin.write(b'Quarks.install("FoxDot");\n\x0c')
        proc.stdin.write(b'FoxDot.start();\n\x0c')
        await proc.stdin.drain()

        async def _(stream):  # rid the world of garbage
            while (bts := await stream.readline()):
                ...

        aio.create_task(_(proc.stdout))
        aio.create_task(_(proc.stderr))

    async def foxdot(self):
        # provides no stdout
        self.fd = proc = await sp.create_subprocess_shell(
            'python -m FoxDot --pipe',
            stdin=sp.PIPE,
            stderr=sp.PIPE,
        )

        async def _():  # rid the world of garbage
            while (bts := await proc.stderr.readline()):
                ...

        aio.create_task(_())

    async def sock2ws(self, sio):
        while True:
            code = (await getblock(self.r)).decode()
            if not code:
                return

            code = code.rstrip('\n') + 2 * '\n'
            await sio.emit('code', {'code': code})

    async def ws2sock(self, sio):
        @sio.on('code')
        async def _(msg):
            code = msg['code'].rstrip('\n') + 2 * '\n'
            self.w.write(code.encode())
            self.fd.stdin.write(code.encode())
            await self.w.drain()
            await self.fd.stdin.drain()

    async def serve(self, reader, writer):
        self.r, self.w = reader, writer

        # connect to remote synth authority
        uri = 'wss://wsfoxdot-nm5dxx2vwq-ey.a.run.app'
        sio = socketio.AsyncClient()
        await sio.connect(uri)

        tasks = [
            aio.create_task(self.sock2ws(sio)),
            aio.create_task(self.ws2sock(sio)),  # do it for the symmetry
        ]

        await aio.wait(tasks)

    async def main(self):
        # start synth interpreter
        await self.sclang()
        await aio.sleep(5)  # give sc a bit of time
        await self.foxdot()

        # launch local server for vim plugin
        await aio.start_unix_server(self.serve, path='/tmp/foxdot.sock')

        try:
            while True:
                await aio.sleep(3600)
        finally:
            return


if __name__ == '__main__':
    aio.run(Client().main())

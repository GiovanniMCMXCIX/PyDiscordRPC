import asyncio
import json
import os
import struct
import sys
import time
import uuid


class DiscordRPC:
    def __init__(self):
        if sys.platform == 'linux' or sys.platform == 'darwin':
            env_vars = ['XDG_RUNTIME_DIR', 'TMPDIR', 'TMP', 'TEMP']
            path = next((os.environ.get(path, None) for path in env_vars if path in os.environ), '/tmp')
            self.ipc_path = f'{path}/discord-ipc-0'
            self.loop = asyncio.get_event_loop()
        elif sys.platform == 'win32':
            self.ipc_path = r'\\?\pipe\discord-ipc-0'
            self.loop = asyncio.ProactorEventLoop()

        self.sock_reader: asyncio.StreamReader = None
        self.sock_writer: asyncio.StreamWriter = None

    async def read_output(self):
        while True:
            data = await self.sock_reader.read(1024)
            if data == b'':
                self.sock_writer.close()
                exit(0)
            try:
                code, length = struct.unpack('<ii', data[:8])
                print(f'OP Code: {code}; Length: {length}\nResponse:\n{json.loads(data[8:].decode("utf-8"))}\n')
            except struct.error:
                print(f'Something happened\n{data}')

    def send_data(self, op: int, payload: dict):
        payload = json.dumps(payload)
        self.sock_writer.write(struct.pack('<ii', op, len(payload)) + payload.encode('utf-8'))

    async def handshake(self):
        if sys.platform == 'linux' or sys.platform == 'darwin':
            self.sock_reader, self.sock_writer = await asyncio.open_unix_connection(self.ipc_path, loop=self.loop)
        elif sys.platform == 'win32':
            self.sock_reader = asyncio.StreamReader(loop=self.loop)
            reader_protocol = asyncio.StreamReaderProtocol(self.sock_reader, loop=self.loop)
            self.sock_writer, _ = await self.loop.create_pipe_connection(lambda: reader_protocol, self.ipc_path)

        self.send_data(0, {'v': 1, 'client_id': '352253827933667338'})
        data = await self.sock_reader.read(1024)
        code, length = struct.unpack('<ii', data[:8])
        print(f'OP Code: {code}; Length: {length}\nResponse:\n{json.loads(data[8:].decode("utf-8"))}\n')

    def send_rich_presence(self):
        current_time = time.time()
        payload = {
            'cmd': 'SET_ACTIVITY',
            'args': {
                'activity': {
                    'state': 'am sad',
                    'details': ':(',
                    'timestamps': {
                        'start': int(current_time),
                        'end': int(current_time) + (5 * 60)
                    },
                    'assets': {
                        'large_text': '>tfw no gf',
                        'large_image': 'feels',
                        'small_text': 'that\'s me',
                        'small_image': 'gio'
                    },
                    'party': {
                        'id': '4chan',
                        'size': [21, 42]  # [Minimum, Maximum]
                    },
                    'secrets': {
                        'match': 'install_gentoo',
                        'join': 'communism_is_bad',
                        'spectate': 'b0nzybuddy',
                    },
                    'instance': True
                },
                'pid': os.getpid()
            },
            'nonce': str(uuid.uuid4())
        }
        self.send_data(1, payload)

    async def run(self):
        await self.handshake()
        self.send_rich_presence()
        await self.read_output()

    def close(self):
        self.sock_writer.close()
        self.loop.close()
        exit(0)


if __name__ == '__main__':
    rpc = DiscordRPC()
    try:
        rpc.loop.run_until_complete(rpc.run())
    except KeyboardInterrupt:
        rpc.close()

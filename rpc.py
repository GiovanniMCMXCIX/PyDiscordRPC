import asyncio
import json
import os
import struct
import time


class DiscordRPC:
    def __init__(self):
        ipc_path = os.environ.get('XDG_RUNTIME_DIR', None) or os.environ.get('TMPDIR', None) or os.environ.get('TMP', None) or os.environ.get('TEMP', None) or '/tmp'
        self.ipc_path = f'{ipc_path}/discord-ipc-0'
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
        self.sock_reader: asyncio.StreamReader = None
        self.sock_writer: asyncio.StreamWriter = None

    async def read_output(self):
        while True:
            data = await self.sock_reader.read(1024)
            code, length = struct.unpack('<ii', data[:8])
            print(f'OP Code: {code}; Length: {length}\nResponse:\n{json.loads(data[8:].decode("utf-8"))}\n')
            await asyncio.sleep(1)

    def send_data(self, op: int, payload: dict):
        payload = json.dumps(payload)
        self.sock_writer.write(struct.pack('<ii', op, len(payload)) + payload.encode('utf-8'))

    async def handshake(self):
        self.sock_reader, self.sock_writer = await asyncio.open_unix_connection(self.ipc_path, loop=self.loop)
        self.send_data(0, {'v': 1, 'client_id': '352253827933667338'})
        data = await self.sock_reader.read(1024)
        code, length = struct.unpack('ii', data[:8])
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
            'nonce': f'{current_time:.20f}'
        }
        self.send_data(1, payload)

    def close(self):
        self.sock_writer.close()
        self.loop.close()


if __name__ == '__main__':
    discord_rpc = DiscordRPC()
    try:
        discord_rpc.loop.run_until_complete(discord_rpc.handshake())
        discord_rpc.send_rich_presence()
        discord_rpc.loop.run_until_complete(discord_rpc.read_output())
    except KeyboardInterrupt:
        discord_rpc.close()

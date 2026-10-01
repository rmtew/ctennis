"""Small stdlib client for the installed Copperline test/control bridge."""
import json
import queue
import subprocess
import threading


class CopperlineSession:
    def __init__(self, executable, cwd):
        self.process = subprocess.Popen([str(executable), '--mcp'], cwd=cwd,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, text=True, encoding='utf-8')
        self.messages = queue.Queue()
        self.identifier = 0
        self.launched = False
        self.stderr = []
        threading.Thread(target=self._read, daemon=True).start()
        threading.Thread(target=self._errors, daemon=True).start()
        self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                    'clientInfo': {'name': 'champion-tennis-tests', 'version': '1'}})
        self._send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def _read(self):
        for line in self.process.stdout:
            try:
                self.messages.put(json.loads(line))
            except ValueError:
                self.messages.put({'error': f'Invalid bridge response: {line[:200]}'})
        self.messages.put({'error': 'Bridge stdout closed'})

    def _errors(self):
        self.stderr.extend(self.process.stderr)

    def _send(self, message):
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()

    def request(self, method, params, timeout=60):
        self.identifier += 1
        identifier = self.identifier
        self._send({'jsonrpc': '2.0', 'id': identifier, 'method': method, 'params': params})
        while True:
            try:
                message = self.messages.get(timeout=timeout)
            except queue.Empty:
                if self.process.poll() is not None:
                    raise RuntimeError('Bridge exited while a request was pending')
                # An observation timeout is not completion. Keep the same request alive.
                print(f'Waiting for Copperline request {identifier} ({method})', flush=True)
                continue
            if message.get('id') != identifier:
                if 'id' not in message and 'error' in message:
                    raise RuntimeError(message['error'])
                continue
            if 'error' in message:
                raise RuntimeError(message['error'])
            return message['result']

    def call(self, name, arguments=None, timeout=60):
        result = self.request('tools/call', {'name': name, 'arguments': arguments or {}}, timeout)
        if result.get('isError'):
            raise RuntimeError(result)
        if name == 'session_launch':
            self.launched = True
        return result

    def inspect(self, name, arguments=None, timeout=60):
        result = self.call(name, arguments, timeout)
        return json.loads(next(block['text'] for block in result['content'] if block['type'] == 'text'))

    def close(self):
        # session_close only shuts down the emulator this bridge launched.
        if self.launched:
            self.call('session_close')
            self.launched = False
        self.process.stdin.close()
        self.process.wait(timeout=10)
        if self.process.returncode:
            raise RuntimeError(''.join(self.stderr))

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class NativeControlSession:
    """Direct CCP transport for installations without the optional ctl binary.

    Used by bounded native title/control checks; the existing MCP client is unchanged.
    Protocol: Copperline v1.0.0-rc.1 docs/debugger/control.md.
    """
    def __init__(self, directory):
        from pathlib import Path
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.process = None
        self.identifier = 0
        self.notification_handler = None

    def __enter__(self):
        return self

    def inspect(self, method, arguments=None):
        import socket, time
        arguments = dict(arguments or {})
        arguments.pop('wait_ms', None)
        if method == 'session_launch':
            info = self.directory / 'control.json'
            info.unlink(missing_ok=True)
            self.log = self.directory / 'emulator.log'
            self.output = self.log.open('w')
            command = [arguments['binary'], '--control', '127.0.0.1:0', '--control-info', str(info),
                       '--factory', '--model', 'A500']
            if arguments.get('run'):
                command += ['--run',arguments['run']]
            command += arguments['args']
            self.process = subprocess.Popen(command, stdout=self.output, stderr=self.output)
            deadline = time.monotonic() + 30
            while not info.exists():
                if self.process.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError(f'Control startup failed; see {self.log}')
                time.sleep(.05)
            endpoint = json.loads(info.read_text())
            host, port = endpoint['listen'].rsplit(':', 1)
            self.socket = socket.create_connection((host, int(port)), timeout=60)
            self.stream = self.socket.makefile('rwb')
            self.inspect('hello', {'token': endpoint['token']})
            return {'log': str(self.log)}
        methods = {'mem_read': 'mem.read', 'capture_screenshot': 'capture.screenshot',
                   'input_key': 'input.key', 'input_joy': 'input.joy',
                   'input_set_port': 'input.set_port', 'break_add': 'break.add',
                   'break_remove': 'break.remove', 'regs_get': 'regs.get',
                   'custom_dump': 'custom.dump'}
        identifier = self.send_async(methods.get(method, method), arguments)
        while True:
            line = self.stream.readline()
            if not line: raise RuntimeError('Control server disconnected')
            reply = json.loads(line)
            if reply.get('id') != identifier:
                if self.notification_handler is not None:
                    self.notification_handler(reply)
                continue
            if 'error' in reply: raise RuntimeError(reply['error'])
            return reply['result']

    def send_async(self, method, arguments=None):
        """Send an input while run_until is pending, without stopping the guest.

        Its eventual reply is delivered to notification_handler. Keep the pending
        synchronous request's identifier local: a handler may send more inputs.
        """
        self.identifier += 1
        identifier = self.identifier
        self.stream.write((json.dumps({'jsonrpc': '2.0', 'id': identifier,
                                     'method': method, 'params': arguments or {}})+'\n').encode())
        self.stream.flush()
        return identifier

    def __exit__(self, *_):
        try:
            if hasattr(self, 'stream'):
                self.inspect('shutdown')
                self.stream.close()
                self.socket.close()
        finally:
            if self.process:
                try: self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                self.output.close()
            (self.directory / 'control.json').unlink(missing_ok=True)

"""Control the pinned Copperline test session with the Python standard library."""
import json
import subprocess


class NativeControlSession:
    """Direct CCP transport for finite native target checks.

    Supports physical inputs and non-stopping bus observation.
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

    def __exit__(self, exc_type, exc_value, traceback):
        # Preserve the first test failure: buffered notifications received while
        # shutting down must not replace it with a later secondary assertion.
        if exc_type is not None:self.notification_handler=None
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

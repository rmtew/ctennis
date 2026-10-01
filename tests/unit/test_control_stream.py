"""The ordinary timing observer must preserve a pending run across live inputs."""
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from copperline_test_session import NativeControlSession


class Duplex:
    def __init__(self, replies):
        self.incoming = io.BytesIO(b''.join((json.dumps(r)+'\n').encode() for r in replies))
        self.outgoing = io.BytesIO()

    def write(self, data): self.outgoing.write(data)
    def flush(self): pass
    def readline(self): return self.incoming.readline()


class PendingRun(unittest.TestCase):
    def test_live_input_does_not_replace_pending_run_identifier(self):
        s = NativeControlSession('/tmp/ctennis-stream-unit')
        s.stream = Duplex([
            {'method':'event.mmio','params':{'value':1}},
            {'id':2,'result':{'applied_at_seconds':1}},
            {'id':1,'result':{'reason':'pause'}}])
        observed = []
        def handler(message):
            observed.append(message)
            if 'method' in message:
                self.assertEqual(s.send_async('input.joy', {'port':2,'red':True}),2)
        s.notification_handler = handler
        self.assertEqual(s.inspect('run_until', {'seconds':1000}), {'reason':'pause'})
        sent = [json.loads(line) for line in s.stream.outgoing.getvalue().splitlines()]
        self.assertEqual([r['id'] for r in sent],[1,2])
        self.assertEqual([r['method'] for r in sent],['run_until','input.joy'])
        self.assertEqual(observed[-1]['id'],2)

    def test_existing_non_streaming_reader_skips_notifications(self):
        s = NativeControlSession('/tmp/ctennis-stream-unit')
        s.stream = Duplex([{'method':'event.mmio','params':{}},{'id':1,'result':{'data':'00'}}])
        self.assertEqual(s.inspect('mem_read', {'addr':4,'len':1}), {'data':'00'})


if __name__ == '__main__': unittest.main()

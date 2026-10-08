"""Finite native acceptance with explicit planning and durable campaign ownership.

No arguments runs and monitors a detached controller to its final exit result.
A chat/session disconnect can end the monitor without ending that controller.
"""
import sys
from acceptance_campaign import main as campaign_main


def main():
    args = sys.argv[1:]
    if '--worker' in args:
        raise ValueError('Worker launch is internal to the campaign controller')
    if not any(flag in args for flag in ('--plan', '--start', '--monitor')):
        # --campaign alone monitors existing work. --resume explicitly launches
        # a new controller only after exclusive ownership has been established.
        args += ['--monitor' if '--campaign' in args and '--resume' not in args else '--run']
    sys.argv = [sys.argv[0], *args]
    return campaign_main()


if __name__ == '__main__':
    raise SystemExit(main())

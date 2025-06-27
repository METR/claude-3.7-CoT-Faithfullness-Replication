import builtins
import time
import types
import pytest
from unittest import mock

import main


def test_main_retries_and_succeeds(monkeypatch):
    # Simulate run_once failing twice, then succeeding
    call_count = {'count': 0}
    def fake_run_once():
        if call_count['count'] < 2:
            call_count['count'] += 1
            raise RuntimeError('fail')
        call_count['count'] += 1
        return None

    monkeypatch.setattr(main, 'run_once', fake_run_once)
    monkeypatch.setattr(time, 'sleep', lambda s: None)

    # Patch print to capture output
    printed = []
    monkeypatch.setattr(builtins, 'print', lambda *args, **kwargs: printed.append(args))

    main.main()
    # Should have retried twice, then succeeded
    assert call_count['count'] == 3
    retry_msgs = [msg for msg in printed if any('Restarting' in str(a) for a in msg)]
    assert len(retry_msgs) == 2


def test_main_gives_up_after_hour(monkeypatch):
    # Simulate run_once always failing
    def always_fail():
        raise RuntimeError('fail')

    monkeypatch.setattr(main, 'run_once', always_fail)
    monkeypatch.setattr(time, 'sleep', lambda s: None)

    # Patch time.time to simulate time passing
    times = [0]
    def fake_time():
        # Each call advances by 1800 seconds (30 min)
        times[0] += 1800
        return times[0]
    monkeypatch.setattr(time, 'time', fake_time)

    # Patch print to capture output
    printed = []
    monkeypatch.setattr(builtins, 'print', lambda *args, **kwargs: printed.append(args))

    with pytest.raises(RuntimeError):
        main.main()
    # Should have retried at least twice, then given up after >1 hour
    retry_msgs = [msg for msg in printed if any('Restarting' in str(a) for a in msg)]
    fatal_msgs = [msg for msg in printed if any('FATAL' in str(a) for a in msg)]
    assert len(retry_msgs) >= 2
    assert any('Giving up' in str(a) for msg in fatal_msgs for a in msg) 
from answer.ans1 import parse_log, MonitorLog, failure_info, InterfaceState, Status
from datetime import datetime
from ipaddress import IPv4Interface
import pytest

@pytest.mark.parametrize('line, date, interface, time', [
    ('20201019133124,10.20.30.1/16,2', datetime(2020, 10, 19, 13, 31, 24), IPv4Interface('10.20.30.1/16'), 2),
    ('20201019133324,10.20.30.1/16,-', datetime(2020, 10, 19, 13, 33, 24), IPv4Interface('10.20.30.1/16'), None),
])
def test_parse_log(line, date, interface, time):
    actual = parse_log(line)
    desired = MonitorLog(date, interface, time)
    assert actual == desired


@pytest.mark.parametrize('lines, value', [
    # sorted order
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING, datetime(2020, 10, 19, 13, 31, 25), datetime(2020, 10, 19, 13, 31, 27))
    ),
    # NOT order by date
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133127,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
     ],
     InterfaceState(Status.RUNNING, datetime(2020, 10, 19, 13, 31, 25), datetime(2020, 10, 19, 13, 31, 27))
    ),
    # failure date < running date
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     InterfaceState(Status.FAILURE, datetime(2020, 10, 19, 13, 31, 25), datetime(2020, 10, 19, 13, 31, 24))
    ),
    # initially failure
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING, datetime(2020, 10, 19, 13, 31, 24), datetime(2020, 10, 19, 13, 31, 27))
    ),
    # parmanently failure
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     InterfaceState(Status.FAILURE, datetime(2020, 10, 19, 13, 31, 24), None)
    ),
    # parmanently running
    ([
        '20201019133124,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,1',
        '20201019133126,10.20.30.1/16,1',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING, None, datetime(2020, 10, 19, 13, 31, 24))
    ),
])
def test_failure_info(lines, value):
    logs = [parse_log(line) for line in lines]
    actual = failure_info(logs)
    desired = {
        IPv4Interface('10.20.30.1/16'): value
    }
    assert actual == desired


@pytest.mark.parametrize('lines, desired', [
    # sorted order
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,1',
     ],
     [('10.20.30.1/16', '2')]
    ),
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133127,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', '2')]
    ),
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', 'inf')]
    ),
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', 'inf')]
    ),
    ([
        '20201019133124,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,1',
        '20201019133126,10.20.30.1/16,1',
        '20201019133127,10.20.30.1/16,1',
     ],
     [('10.20.30.1/16', '-')]
    ),
])
def test_failute_info(lines, desired):
    logs = [parse_log(line) for line in lines]
    actual = [(str(k), v.interval()) for k,v in failure_info(logs).items()]
    assert actual == desired

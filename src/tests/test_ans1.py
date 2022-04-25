from answer.ans1 import parse_log, MonitorLog, failure_states, InterfaceState, Status, solve_as_text, transitState
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


def test_interface_state():
    state = InterfaceState(Status.IDLE, [], None)
    fail_start = datetime(2021, 12, 31)
    fail_end = datetime(2022, 1, 1)

    state.start(fail_start)
    assert state.periods == []
    assert state.fail_start == fail_start

    state.end(datetime(2022, 1, 1))
    assert state.periods == [(fail_start, fail_end)]
    assert state.fail_start is None



@pytest.mark.parametrize('state, line, desired', [
    (InterfaceState(Status.RUNNING, [], None),
     '20220101000000,1.1.1.1/16,-',
     InterfaceState(Status.FAILURE, [], datetime(2022, 1, 1))),

    (InterfaceState(Status.FAILURE, [], datetime(2021, 12, 31)),
     '20220101000000,1.1.1.1/16,1',
     InterfaceState(Status.RUNNING, [(datetime(2021, 12, 31),datetime(2022, 1, 1))], None)),
])
def test_transition(state, line, desired):
    log = parse_log(line)
    assert log.date is not None
    assert transitState(log, state) == desired



@pytest.mark.parametrize('lines, value', [
    # sorted order
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING,
                    [(datetime(2020, 10, 19, 13, 31, 25), datetime(2020, 10, 19, 13, 31, 27))],
                    None)
    ),
    # NOT order by date
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133127,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
     ],
     InterfaceState(Status.RUNNING,
                    [(datetime(2020, 10, 19, 13, 31, 25), datetime(2020, 10, 19, 13, 31, 27))],
                    None)
    ),
    # failure date < running date
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     InterfaceState(Status.FAILURE,
                    [],
                    datetime(2020, 10, 19, 13, 31, 25))
    ),
    # initially failure
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING,
                    [(datetime(2020, 10, 19, 13, 31, 24), datetime(2020, 10, 19, 13, 31, 27))],
                    None)
    ),
    # parmanently failure
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     InterfaceState(Status.FAILURE, [], datetime(2020, 10, 19, 13, 31, 24))
    ),
    # parmanently running
    ([
        '20201019133124,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,1',
        '20201019133126,10.20.30.1/16,1',
        '20201019133127,10.20.30.1/16,1',
     ],
     InterfaceState(Status.RUNNING, [], None)
    ),
])
def test_failure_states(lines, value):
    logs = [parse_log(line) for line in lines]
    actual = failure_states(logs)
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
     [('10.20.30.1/16', ['2020-10-19 13:31:25 - 2020-10-19 13:31:27'])]
    ),
    # unsorted order
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133127,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', ['2020-10-19 13:31:25 - 2020-10-19 13:31:27'])]
    ),
    # failure continued
    ([
        '20201019133124,10.20.30.1/16,2',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', ['2020-10-19 13:31:25 -'])]
    ),
    # failure initially
    ([
        '20201019133124,10.20.30.1/16,-',
        '20201019133125,10.20.30.1/16,-',
        '20201019133126,10.20.30.1/16,-',
        '20201019133127,10.20.30.1/16,-',
     ],
     [('10.20.30.1/16', ['2020-10-19 13:31:24 -'])]
    ),
    # no failure
    ([
        '20201019133124,10.20.30.1/16,1',
        '20201019133125,10.20.30.1/16,1',
        '20201019133126,10.20.30.1/16,1',
        '20201019133127,10.20.30.1/16,1',
     ],
     [('10.20.30.1/16', [])]
    ),
])
def test_failute_states(lines, desired):
    logs = [parse_log(line) for line in lines]
    states = failure_states(logs)
    actual = [(str(k), v.format()) for k,v in states.items()]
    assert actual == desired


def test_solve_as_text(datadir):
    actual = solve_as_text(datadir / 'in1.txt')
    desired = (datadir / 'out1.txt').read_text().rstrip()
    assert actual == desired


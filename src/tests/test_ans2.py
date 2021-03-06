from answer.ans2 import InterfaceState, Status, update_state, parse_log, solve_as_text, FailState
import pytest
from datetime import datetime


@pytest.mark.parametrize('state, log_str, threshould, desired',[
    # failure started
    (InterfaceState(Status.RUNNING, FailState([], None, datetime(2021, 12, 31), 2)),
     '20220101000000,1.1.1.1/30,-', 3,
     InterfaceState(Status.FAILURE, FailState([], datetime(2021, 12, 31), None, 3))),
    # timeout_count < threshould
    (InterfaceState(Status.RUNNING, FailState([], None, datetime(2021, 12, 31), 2)),
     '20220101000000,1.1.1.1/30,-', 4,
     InterfaceState(Status.RUNNING, FailState([], None, datetime(2021, 12, 31), 3))),
    # timeout stopped before failure
    (InterfaceState(Status.RUNNING, FailState([], None, datetime(2021, 12, 31), 2)),
     '20220101000000,1.1.1.1/30,1', 4,
     InterfaceState(Status.RUNNING, FailState([], None, None, 0))),
    # revive interface
    (InterfaceState(Status.FAILURE, FailState([], datetime(2021, 12, 31), None, 2)),
     '20220101000000,1.1.1.1/30,1', 3,
     InterfaceState(Status.RUNNING, FailState([(datetime(2021, 12, 31), datetime(2022, 1, 1))], None, None, 0))),
    # failure continued
    (InterfaceState(Status.FAILURE, FailState([], datetime(2021, 12, 31), None, 3)),
     '20220101000000,1.1.1.1/30,-', 3,
     InterfaceState(Status.FAILURE, FailState([], datetime(2021, 12, 31), None, 4))),
])
def test_transition(state, log_str, threshould, desired):
    log = parse_log(log_str)
    update_state(log, state, threshould)
    assert state.status == desired.status
    assert state.fail_state == desired.fail_state


def test_solve_as_text(datadir):
    actual = solve_as_text(datadir / 'in1.txt', 3) + '\n'
    desired = (datadir / 'out1.txt').read_text()
    assert actual == desired

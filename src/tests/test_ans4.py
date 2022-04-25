from ipaddress import IPv4Interface
from answer.ans4 import Status, FailState, OverloadState, InterfaceState, RingBuffer, NetworkState, update_state_net
from datetime import datetime

def test_transition():
    states = []
    state_net = NetworkState([], None, dict())

    addrs = ['192.168.1.1/24', '192.168.1.2/24', '192.168.1.3/24', '192.168.1.4/24']
    statuses = [Status.RUNNING, Status.FAILURE, Status.FAILURE, Status.FAILURE]
    for addr, status in zip(addrs, statuses):
        interface = IPv4Interface(addr)
        state = InterfaceState(status,
                               FailState([], None, None, 0),
                               OverloadState([], None, RingBuffer(100)))
        states.append(state)
        state_net.states[interface] = state

    assert [state.status for _, state in state_net.states.items()] == statuses

    update_state_net(datetime(2022, 1, 1), state_net)
    assert state_net.fail_start is None

    states[0].status = Status.FAILURE
    update_state_net(datetime(2022, 1, 1), state_net)
    assert state_net.fail_start == datetime(2022, 1, 1)

    states[1].status = Status.RUNNING
    update_state_net(datetime(2022, 1, 2), state_net)
    assert state_net.fail_start is None
    assert state_net.periods == [(datetime(2022, 1, 1), datetime(2022, 1, 2))]

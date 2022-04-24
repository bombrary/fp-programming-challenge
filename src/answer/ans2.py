from datetime import datetime
from dataclasses import dataclass
from ipaddress import IPv4Interface
from typing import Optional
from enum import Enum, auto
import argparse


@dataclass
class MonitorLog:
    date: datetime
    addr: IPv4Interface
    time: Optional[int]


def parse_time(time_str) -> Optional[int]:
    try:
        return int(time_str)
    except ValueError:
        return None
    

def parse_log(line: str) -> MonitorLog:
    [date_str, addr_str, time_str] = line.split(',')
    date = datetime.strptime(date_str, '%Y%m%d%H%M%S')
    addr = IPv4Interface(addr_str)
    time = parse_time(time_str)

    return MonitorLog(date, addr, time)


class Status(Enum):
    RUNNING = auto()
    TIMEOUT = auto()
    FAILURE = auto()
    IDLE = auto()


@dataclass
class InterfaceState:
    status: Status
    fail_start: Optional[datetime]
    fail_end: Optional[datetime]
    timeout_start: Optional[datetime]
    timeout_count: int

    def interval(self) -> str:
        if self.status == Status.FAILURE:
            return 'inf'
        elif self.status == Status.RUNNING:
            if self.fail_start is not None and self.fail_end is not None:
                return str((self.fail_end - self.fail_start).seconds)
            else:
                return '-'
        else:
            return '-'


def transitState(log: MonitorLog, state: InterfaceState, threshould: int) -> InterfaceState:
    if is_timeout(log):
        timeout_count = state.timeout_count + 1
        if timeout_count == 1:
            timeout_start = log.date
        else:
            timeout_start = state.timeout_start
    else:
        timeout_count = 0
        timeout_start = None

    if timeout_count >= threshould:
        # failure
        if state.status == Status.FAILURE:
            # failure continued
            return InterfaceState(Status.FAILURE, state.fail_start, state.fail_end, timeout_start, timeout_count)
        else:
            # failure start
            return InterfaceState(Status.FAILURE, timeout_start, None, timeout_start, timeout_count)
    else:
        # running
        if state.status == Status.RUNNING:
            # running continued
            return InterfaceState(Status.RUNNING, state.fail_start, state.fail_end, timeout_start, timeout_count)
        else:
            # revive interface
            return InterfaceState(Status.RUNNING, state.fail_start, log.date, timeout_start, timeout_count)
    

def is_timeout(log) -> bool:
    return log.time is None


def failure_states(logs: list[MonitorLog], threshould: int) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE, None, None, None, 0)

        states[log.addr] = transitState(log, states[log.addr], threshould)

    return states


def parse_logs_from_file(path) -> list[MonitorLog]:
    with open(path, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        return logs
        

def format_failure_states(states) -> list[str]:
    return [ f'{addr}: {state.interval()}' for addr, state in states.items() ]


def solve_as_text(src, threshould: int):
    logs = parse_logs_from_file(src)
    states = failure_states(logs, threshould)
    return '\n'.join(format_failure_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    parser.add_argument('N', type=int, help='threshould for timeout')
    args = parser.parse_args()

    print(solve_as_text(args.src, int(args.N)))

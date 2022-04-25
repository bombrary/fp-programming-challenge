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


def parse_time(time_str: str) -> Optional[int]:
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
    FAILURE = auto()
    IDLE = auto()


@dataclass
class InterfaceState:
    status: Status
    fail_start: Optional[datetime]
    fail_end: Optional[datetime]

    def interval(self) -> str:
        if self.fail_start is not None and self.fail_end is not None:
            return str((self.fail_end - self.fail_start).seconds)
        elif self.fail_start is not None:
            # running is not shown -> permanently failure
            return 'inf'
        elif self.fail_end is not None:
            # illegal condition
            return 'n/a'
        else:
            # failure is not shown -> permanently running
            return '-'


def transitState(log: MonitorLog, state: InterfaceState) -> InterfaceState:
    if is_timeout(log):
        # failure
        match state.status:
            case Status.RUNNING:
                return InterfaceState(Status.FAILURE, log.date, None)

            case Status.FAILURE:
                return state

            case _:
                return InterfaceState(Status.FAILURE, log.date, None)
    else:
        # running
        match state.status:
            case Status.RUNNING:
                return state
            case Status.FAILURE:
                return InterfaceState(Status.RUNNING, state.fail_start, log.date)
            case _:
                return InterfaceState(Status.RUNNING, None, state.fail_end)
    


def is_timeout(log: MonitorLog) -> bool:
    return log.time is None


def failure_states(logs: list[MonitorLog]) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE, None, None)

        states[log.addr] = transitState(log, states[log.addr])

    return states


def parse_logs_from_file(path: str) -> list[MonitorLog]:
    with open(path, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        return logs
        

def format_failure_states(states: dict[IPv4Interface, InterfaceState]) -> list[str]:
    return [ f'{addr}: {state.interval()}' for addr, state in states.items() ]


def solve_as_text(src: str):
    logs = parse_logs_from_file(src)
    states = failure_states(logs)
    return '\n'.join(format_failure_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    args = parser.parse_args()

    print(solve_as_text(args.src))

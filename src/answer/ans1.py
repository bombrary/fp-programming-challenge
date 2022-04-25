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
    periods: list[tuple[datetime, datetime]]
    fail_start: Optional[datetime]

    def start(self, fail_start: datetime):
        self.fail_start = fail_start

    def end(self, fail_end: datetime):
        if self.fail_start is not None:
            self.periods.append((self.fail_start, fail_end))
            self.fail_start = None

    def format(self) -> list[str]:
        format_list = [ f'{period[0]} - {period[1]}' for period in self.periods]
        if self.fail_start is not None:
            format_list.append(f'{self.fail_start} -')
        return format_list


def transitState(log: MonitorLog, state: InterfaceState) -> InterfaceState:
    if is_timeout(log):
        # failure
        status = Status.FAILURE
        match state.status:
            case Status.FAILURE:
                return state

            case _:
                state.start(log.date)
                return InterfaceState(status, state.periods, state.fail_start)
    else:
        # running
        status = Status.RUNNING
        match state.status:
            case Status.RUNNING:
                return state
            case Status.FAILURE:
                state.end(log.date)
                return InterfaceState(status, state.periods, state.fail_start)
            case _:
                return InterfaceState(status, state.periods, state.fail_start)
    


def is_timeout(log: MonitorLog) -> bool:
    return log.time is None


def failure_states(logs: list[MonitorLog]) -> dict[IPv4Interface, InterfaceState]:
    states = dict()
    for log in sorted(logs, key=lambda log: log.date):
        if log.addr not in states:
            states[log.addr] = InterfaceState(Status.IDLE, [], None)

        states[log.addr] = transitState(log, states[log.addr])

    return states


def parse_logs_from_file(path: str) -> list[MonitorLog]:
    with open(path, 'r') as f:
        logs = [parse_log(line) for line in f.readlines()]
        return logs
        

def format_states(states: dict[IPv4Interface, InterfaceState]) -> list[str]:
    format_list = []
    for addr, state in states.items():
        state_format = '\n  '.join(state.format())
        format_list.append(f'{addr}:\n  {state_format}')

    return format_list


def solve_as_text(src: str):
    logs = parse_logs_from_file(src)
    states = failure_states(logs)
    return '\n'.join(format_states(states))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('src', help='input log file')
    args = parser.parse_args()

    print(solve_as_text(args.src))

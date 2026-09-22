#!/usr/bin/env python3
import argparse
import os
import time

GAME_BINARY = b"RSDragonwildsServer-Linux-Shipping"


def compact_cpus(cpus):
    values = sorted(cpus)
    if not values:
        return "none"
    ranges = []
    start = previous = values[0]
    for cpu in values[1:]:
        if cpu == previous + 1:
            previous = cpu
            continue
        ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = cpu
    ranges.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ",".join(ranges)


def find_game_pid():
    for name in os.listdir("/proc"):
        if not name.isdigit() or int(name) == os.getpid():
            continue
        try:
            with open(f"/proc/{name}/cmdline", "rb") as stream:
                cmdline = stream.read()
            with open(f"/proc/{name}/comm", "rb") as stream:
                comm = stream.read().strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if GAME_BINARY in cmdline or comm.startswith(b"RSDragonwildsSe"):
            return int(name)
    raise SystemExit("The Dragonwilds server process is not running in this container.")


def stat_fields(pid, tid):
    with open(f"/proc/{pid}/task/{tid}/stat") as stream:
        fields = stream.read().rsplit(")", 1)[1].split()
    return int(fields[11]) + int(fields[12]), int(fields[36])


def thread_snapshot(pid):
    result = {}
    for tid in os.listdir(f"/proc/{pid}/task"):
        try:
            ticks, processor = stat_fields(pid, tid)
            with open(f"/proc/{pid}/task/{tid}/comm") as stream:
                name = stream.read().strip()
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        result[int(tid)] = (ticks, processor, name)
    return result


def cgroup_limit():
    try:
        with open("/sys/fs/cgroup/cpu.max") as stream:
            quota, period = stream.read().split()
        return "unlimited" if quota == "max" else f"{int(quota) / int(period):.2f} CPUs"
    except FileNotFoundError:
        pass
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as stream:
            quota = int(stream.read())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as stream:
            period = int(stream.read())
        return "unlimited" if quota < 0 else f"{quota / period:.2f} CPUs"
    except (FileNotFoundError, ValueError):
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Report Dragonwilds CPU affinity and per-thread CPU usage.")
    parser.add_argument("--seconds", type=int, default=10)
    parser.add_argument("--pid", type=int)
    args = parser.parse_args()
    if args.seconds < 1:
        parser.error("--seconds must be at least 1")

    pid = args.pid or find_game_pid()
    affinity = os.sched_getaffinity(pid)
    first = thread_snapshot(pid)
    print(f"game_pid={pid}")
    print(f"affinity={compact_cpus(affinity)} ({len(affinity)} CPUs)")
    print(f"cgroup_cpu_limit={cgroup_limit()}")
    print(f"threads={len(first)}")
    print(f"sampling_seconds={args.seconds}")
    time.sleep(args.seconds)
    second = thread_snapshot(pid)
    ticks_per_second = os.sysconf("SC_CLK_TCK")

    rows = []
    for tid, (ticks, processor, name) in second.items():
        if tid not in first:
            continue
        elapsed = (ticks - first[tid][0]) / ticks_per_second
        rows.append((elapsed * 100 / args.seconds, processor, tid, name))
    rows.sort(reverse=True)
    for percent, processor, tid, name in rows:
        if percent >= 0.1:
            print(f"tid={tid} cpu={percent:5.1f}% core={processor} name={name}")
    total = sum(row[0] for row in rows)
    print(f"total_cpu={total:.1f}% of one core; host_capacity={len(affinity) * 100:.0f}%")
    if len(affinity) > 1 and rows and rows[0][0] >= 80 and total < len(affinity) * 100 * 0.6:
        print("assessment=multithreaded process, but one game thread is currently dominant")
    elif len(affinity) <= 1:
        print("assessment=process affinity allows only one CPU")


if __name__ == "__main__":
    main()

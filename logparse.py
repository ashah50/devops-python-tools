import argparse
import re
from collections import Counter, defaultdict

def find_lines(logfile, level):
    matches = []
    with open(logfile) as f:
        for line in f:
            line = line.strip()
            parts = line.split(maxsplit=3)
            if parts[2] == level:
                matches.append(line)
    return matches  

def count_levels(logfile):
    counts = Counter()
    with open(logfile) as f:
        for line in f:
            parts = line.split(maxsplit=3)
            counts[parts[2]] += 1
    return counts

def top_messages(logfile, n):
    messages = []
    with open(logfile) as f:
        for line in f:
            parts = line.split(maxsplit=3)
            messages.append(parts[3].strip())
    return Counter(messages).most_common(n)


def find_ips(logfile):
    counts = Counter()
    with open(logfile, "r") as f:
        for line in f:
            for ip in re.findall(r"\d+\.\d+\.\d+\.\d+", line):
                counts[ip] += 1
    return counts

def loud_levels(counts):
    return {k: v for k, v in counts.items() if v >= 2}

def group_by_level(logfile):
    groups = defaultdict(list)
    with open(logfile) as f:
        for line in f:
            parts = line.split(maxsplit=3)
            groups[parts[2]].append(parts[3].strip())
    return groups

def unique_levels(logfile):
    levels = set()
    with open(logfile) as f:
        for line in f:
            parts = line.split(maxsplit=3)
            levels.add(parts[2])
    return levels

def main():
    parser = argparse.ArgumentParser(description="Parse a log file")
    parser.add_argument("logfile", help="path to the log file")
    parser.add_argument("--level", help="only show lines of this level")
    parser.add_argument("--top", type=int, help="show the N most common messages")
    parser.add_argument("--loud", action="store_true", help="show only levels appearing 2+ times")
    parser.add_argument("--group", action="store_true", help="group messages by level")
    parser.add_argument("--rank", type=int, help="show the N most common levels")
    parser.add_argument("--unique", action="store_true", help="show the distinct levels")
    parser.add_argument("--ips", action="store_true", help="count IP addresses in the log")
    args = parser.parse_args()


    if args.level:
        for line in find_lines(args.logfile, args.level):
            print(line)
    elif args.top:
        for message, count in top_messages(args.logfile, args.top):
            print(f"{count:3}   {message}")
    elif args.loud:
        print(loud_levels(count_levels(args.logfile)))
    elif args.group:
        groups = group_by_level(args.logfile)
        for level, messages in groups.items():
            print(f"{level} ({len(messages)}):")
            for m in messages:
                print(f"  {m}")
    elif args.rank:
        for level, count in count_levels(args.logfile).most_common(args.rank):
            print(f"{count:3}   {level}")
    elif args.unique:
        levels = unique_levels(args.logfile)
        print(f"{len(levels)} unique levels: {levels}")
    elif args.ips:
        counts = find_ips(args.logfile)
        for ip, count in counts.most_common():
            print(f"{ip}: {count}")
    else:
        print(count_levels(args.logfile).most_common())


if __name__ == "__main__":
    main()
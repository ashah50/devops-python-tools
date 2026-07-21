import argparse
from pathlib import Path
from collections import Counter, defaultdict

def human_size(n):
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    else:
        return f"{n / (1024 * 1024):.1f} MB"
    
def count_by_ext(folder):
    counts = Counter()
    for p in Path(folder).rglob("*"):
        if p.is_file():
            counts[p.suffix] += 1
    return counts

def size_by_ext(folder):
    sizes = defaultdict(int)
    for p in Path(folder).rglob("*"):
        if p.is_file():
            sizes[p.suffix] += p.stat().st_size
    return sizes

def biggest_files(folder, n):
    files = []
    for p in Path(folder).rglob("*"):
        if p.is_file():
            files.append((p.name, p.stat().st_size))
    return sorted(files, key=lambda item: item[1], reverse=True)[:n]

def unique_exts(folder):
    exts = set()
    for p in Path(folder).rglob("*"):
        if p.is_file():
            exts.add(p.suffix)            
    return exts

def main():
    parser = argparse.ArgumentParser(description="Report disk usage of a folder")
    parser.add_argument("folder", help="path to the folder to scan")
    parser.add_argument("--count", action="store_true", help="count file by extension")
    parser.add_argument("--size", action="store_true", help="total bytes by extension")
    parser.add_argument("--top", type=int, help="show the N biggest files")
    parser.add_argument("--unique", action="store_true", help="show distinct extensions")
    args = parser.parse_args()

    if args.count:
        print(count_by_ext(args.folder))
    elif args.size:
        for ext, total in size_by_ext(args.folder).items():
            print(f"{human_size(total):>10}   {ext}")
    elif args.top:
        for name, size in biggest_files(args.folder, args.top):
            print(f"{human_size(size):>10}   {name}")
    elif args.unique:
        print(unique_exts(args.folder))
    else:
        print(count_by_ext(args.folder))

if __name__ == "__main__":
    main()



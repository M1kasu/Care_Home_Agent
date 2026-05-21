import sys
import zipfile
from pathlib import Path


def usage() -> int:
    sys.stderr.write("usage: unzip [-Z1|-l|-p] archive [entry]\n")
    return 2


def main() -> int:
    if len(sys.argv) < 3:
        return usage()
    mode = sys.argv[1]
    archive = Path(sys.argv[2])
    if not archive.exists():
        sys.stderr.write(f"missing archive: {archive}\n")
        return 1
    with zipfile.ZipFile(archive) as zf:
        infos = zf.infolist()
        if mode == "-Z1":
            for info in infos:
                print(info.filename)
            return 0
        if mode == "-l":
            print("  Length      Date    Time    Name")
            print("---------  ---------- -----   ----")
            total = 0
            for info in infos:
                total += info.file_size
                y, m, d, hh, mm, _ = info.date_time
                print(f"{info.file_size:9d}  {m:02d}-{d:02d}-{y:04d} {hh:02d}:{mm:02d}   {info.filename}")
            print("---------                     -------")
            print(f"{total:9d}                     {len(infos)} files")
            return 0
        if mode == "-p":
            if len(sys.argv) < 4:
                return usage()
            sys.stdout.buffer.write(zf.read(sys.argv[3]))
            return 0
    return usage()


if __name__ == "__main__":
    raise SystemExit(main())

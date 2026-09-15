"""Relocate paths in a separate working copy; never rewrite the archived record."""
from pathlib import Path
import argparse, re, shutil

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('destination',type=Path,help='A NEW folder, preferably T-MATS/Trunk/TMATSGPT')
    args=parser.parse_args()
    source=Path(__file__).resolve().parents[1]/'study'
    target=args.destination.resolve()
    if target.exists(): parser.error('Destination must not exist; original folders are never overwritten.')
    if source==target or source in target.parents: parser.error('Destination must be outside the archived project.')
    shutil.copytree(source,target)
    count=0
    for path in target.rglob('*'):
        if not path.is_file() or path.suffix.lower() not in {'.json','.txt','.m','.py'}: continue
        original=path.read_text(encoding='utf-8',errors='strict')
        text=original
        # JSON paths may contain doubled separators. Restrict replacements to the recorded TMATSGPT prefix.
        text=re.sub(r'C:(?:\\\\|\\|/)[^\r\n"\']*?TMATSGPT',lambda _:target.as_posix(),text)
        if text!=original:
            path.write_text(text,encoding='utf-8');count+=1
    (target/'tmp/dob').mkdir(parents=True,exist_ok=True)
    print(f'Created {target}; relocated paths in {count} text files. Binary MAT/ZIP provenance remains unchanged.')
if __name__=='__main__': main()

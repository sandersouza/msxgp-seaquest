"""Package qualified native alternatives without touching the original release."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from source_identity import verify as verify_source

ROOT=Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence',type=Path,default=ROOT/'references/compact-delivery/native.json')
    args=parser.parse_args()
    if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():
        raise ValueError('commit the reviewed source and evidence before release packaging')
    build=ROOT/'outputs/disk'
    built=json.loads((build/'manifest.json').read_text())
    if not built.get('source_revision'):
        raise ValueError('release build must record a clean source revision; rebuild from committed sources')
    verify_source(ROOT,built['source_identity'])
    source=built['source_revision']
    evidence=json.loads(args.evidence.read_text())
    if evidence.get('verdict')!='pass':
        raise ValueError('native qualification is not complete')
    if evidence.get('build_source_sha256')!=built['source_identity']['sha256']:
        raise ValueError('qualification is not linked to this build source identity')
    files={name:(build/name).read_bytes() for name in ('SEAQUEST.COM','SEAQUEST32.ROM')}
    identities={name:dict(bytes=len(data),sha256=digest(data)) for name,data in files.items()}
    if identities!=evidence['artifacts']:
        raise ValueError('qualified identities differ from the files being packaged')
    if identities['SEAQUEST32.ROM']['bytes']!=32768:
        raise ValueError('plain cartridge exceeds its fixed 32 KiB contract')
    manifest=dict(release='1.0.0',source_revision=source,source_sha256=built['source_identity']['sha256'],artifacts=identities,
                  ram_kib=64,vram_kib=16,cpu='standard Z80',
                  disk_environment='MSX-DOS 1; no cartridge; machine reset to exit',
                  plain_mapper='Normal, fixed 4000..BFFF; no bank switching',
                  qualification_sha256=digest(args.evidence.read_bytes()),physical_hardware=False,
                  original_asset=dict(name='seaquest.rom',bytes=131072,
                      sha256='41ec3b92e7a570f3661bbd186c8761ca5a39fe654d5b0a3eb8b6a18b727e9be8',unchanged=True))
    manifest_bytes=(json.dumps(manifest,indent=2)+'\n').encode()
    readme='''SEAQUEST - NATIVE MSX1 ALTERNATIVES FOR RELEASE 1.0.0

Requires original 64 KB RAM, 16 KB VRAM, standard Z80/VDP/PSG.

DISK: boot your normal MSX-DOS 1 system disk, copy SEAQUEST.COM to it,
then type SEAQUEST at the A> prompt. No cartridge or RAM expansion.
F1 resets the game. Reset/power-cycle the MACHINE to leave the program.
No DOS or BIOS files are included. The game does not write the disk.

CARTRIDGE: SEAQUEST32.ROM is a complete ordinary 32768-byte cartridge.
Select Normal in openMSX, or program a compatible fixed 32 KB cartridge.
openmsx -machine C-BIOS_MSX1 -cart SEAQUEST32.ROM -romtype Normal

CONTROLS: arrows/Space, joystick1/button1, joystick2/button1;
F1 start/reset, F2 one/two players, F3/F4 difficulty toggles.

Automated PAL/NTSC emulator qualification is recorded in the repository.
Human playtesting, subjective listening and physical hardware tests remain
pending. The original 128 KB ASCII16 seaquest.rom asset is unchanged.

Full instructions and source:
https://github.com/sandersouza/msxgp-seaquest/blob/main/docs/native-delivery.md
'''
    files.update({'MANIFEST.JSON':manifest_bytes,'README.TXT':readme.replace('\n','\r\n').encode(),
                  'ZX0-LICENSE.TXT':(ROOT/'src/third_party/zx0/LICENSE').read_bytes()})
    files['SHA256SUMS']=(''.join(f'{digest(data)}  {name}\n' for name,data in sorted(files.items()))).encode()
    target=build/'release'
    target.mkdir(exist_ok=True)
    archive=target/'seaquest-1.0.0-native-msx1.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as bundle:
        for name,data in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.external_attr=0o100644<<16
            bundle.writestr(info,data)
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() or any(bundle.read(name)!=data for name,data in files.items()):
            raise ValueError('native release archive failed validation')
    for name in ('SEAQUEST.COM','SEAQUEST32.ROM'):
        (target/name).write_bytes(files[name])
    (target/'seaquest-1.0.0-native-manifest.json').write_bytes(manifest_bytes)
    assets=('SEAQUEST.COM','SEAQUEST32.ROM','seaquest-1.0.0-native-manifest.json',archive.name)
    checks=''.join(f'{digest((target/name).read_bytes())}  {name}\n' for name in sorted(assets))
    (target/'seaquest-1.0.0-native-SHA256SUMS').write_text(checks)
    print(checks,end='')


if __name__=='__main__':
    main()

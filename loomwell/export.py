#!/usr/bin/env python3
"""Export Loomwell's editable website and social layouts using DesignCraft.

Standard library only. Supply --cli to use this pack independently of Atlas.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

PACK = Path(__file__).resolve().parent
REPO = PACK.parent
CATALOG = json.loads((PACK / 'pack.json').read_text())['templates']
BRAND = json.loads((PACK / 'brand.json').read_text())
DEFAULT = json.loads((PACK / 'content.json').read_text())


def cli_path(explicit):
    if explicit:
        path=Path(explicit)
        if not path.is_file() or not os.access(path,os.X_OK):
            raise ValueError('--cli must name an executable DesignCraft CLI.')
        return str(path.resolve())
    candidates = [explicit, os.environ.get('DESIGNCRAFT_CLI'),
                  str(REPO / 'target/release/designcraft-cli'), shutil.which('designcraft-cli')]
    # A convenience for the Loomwell local checkout; no dependency on Atlas at runtime.
    for parent in REPO.parents:
        candidates.append(str(parent / '.atlas/tools/storytold/build/designcraft/release/designcraft-cli'))
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate).resolve())
    raise ValueError('Build designcraft-cli, set DESIGNCRAFT_CLI, or pass --cli /path/to/designcraft-cli.')


def content(path):
    values = DEFAULT.copy()
    if path:
        if path.stat().st_size > 16384:
            raise ValueError('Content JSON exceeds 16 KiB.')
        overrides = json.loads(path.read_text())
        if not isinstance(overrides, dict) or set(overrides) - set(DEFAULT):
            raise ValueError('Content must be an object using the keys in loomwell/content.json.')
        for key, value in overrides.items():
            if not isinstance(value, str) or not value.strip() or len(value) > 600:
                raise ValueError(f'{key} must be a nonempty string of at most 600 characters.')
        values.update(overrides)
    return values


class Layout:
    def __init__(self, name):
        size = CATALOG[name]
        self.steps = []
        self.add('file.new', {'width': size['width'], 'height': size['height'], 'pages': 1,
                              'facingPages': False, 'margins': 0, 'intent': 'web',
                              'title': f'Loomwell {name} template'})
        for key, value in BRAND['colors'].items():
            self.add('swatch.create', {'name': 'Loomwell ' + key.title(), 'color': value})

    def add(self, command, params):
        index = len(self.steps)
        self.steps.append((command, params))
        return index

    def rect(self, x, y, w, h, color):
        i = self.add('frame.create', {'rect': [x, y, x+w, y+h], 'content': 'unassigned'})
        self.add('object.fill', {'swatch': 'Loomwell '+color.title(), 'ids': [f'${i}.id']})
        self.add('object.stroke', {'swatch': '[None]', 'ids': [f'${i}.id']})

    def text(self, x, y, w, h, value, size=20, color='forest', display=False):
        i = self.add('frame.create', {'rect': [x, y, x+w, y+h], 'content': 'text',
                                      'text': value.replace('$','$$'), 'caret': False})
        self.add('object.fill', {'swatch': '[None]', 'ids': [f'${i}.id']})
        self.add('object.stroke', {'swatch': '[None]', 'ids': [f'${i}.id']})
        self.add('selection.set', {'ids': [f'${i}.id']})
        self.add('type.char', {'attrs': {'fontFamily': BRAND['fonts']['display' if display else 'body'],
                                        'size': size, 'fill': 'Loomwell '+color.title(),
                                        'leading': {'kind':'points','value':size*1.18}}})

    def weave(self, x, y, pitch):
        width = pitch*.62
        for i in range(7):
            self.rect(x+i*pitch, y, width, 7*pitch, 'forest')
        for j in range(7):
            self.rect(x, y+j*pitch, 7*pitch, width, 'terracotta' if j==3 else 'sage')
        for i in range(7):
            for j in range(7):
                if (i+j)%2==0:
                    self.rect(x+i*pitch,y+j*pitch,width,width,'forest')

    def script(self):
        return '# Original Loomwell layout. No customer data.\n' + '\n'.join(
            command+' '+json.dumps(params,ensure_ascii=False,separators=(',',':'))
            for command,params in self.steps) + '\n'


def make(name, c):
    a = Layout(name)
    width, height = CATALOG[name]['width'], CATALOG[name]['height']
    a.rect(0,0,width,height,'paper' if name in ('website','brief') else 'forest')
    if name == 'website':
        a.text(72,48,800,70,c['brand'],38,display=True)
        a.text(72,158,800,30,c['eyebrow'],14)
        a.text(66,220,890,260,c['headline'],90,display=True)
        a.text(72,525,790,115,c['subheadline'],27)
        a.rect(72,681,285,66,'forest')
        a.text(98,697,240,42,c['action'],22,'paper')
        a.weave(1020,235,54)
        a.text(1015,660,510,40,'CONTEXT / CORRECTION / OUTCOME',13)
        a.rect(72,804,1456,1,'forest')
        a.text(72,830,1456,38,c['footer'],13)
    elif name == 'social':
        a.text(48,36,690,65,c['brand'],34,'paper',True)
        a.text(48,124,700,30,c['eyebrow'],13,'sage')
        a.text(43,190,750,190,c['headline'],66,'paper',True)
        a.text(48,415,700,90,c['subheadline'],22,'paper')
        a.rect(842,143,310,350,'paper')
        a.weave(858,179,40)
        a.rect(48,551,1104,1,'sage')
        a.text(48,577,1104,32,c['footer'],12,'sage')
    elif name == 'square':
        a.text(64,50,920,80,c['brand'],42,'paper',True)
        a.text(64,165,920,36,c['eyebrow'],17,'sage')
        a.text(56,243,950,245,c['headline'],84,'paper',True)
        a.text(64,532,910,110,c['subheadline'],29,'paper')
        a.rect(706,671,287,287,'paper')
        a.weave(724,689,36)
        a.text(64,738,530,55,c['action'],33,'sage',True)
        a.text(64,817,520,90,'Request. Policy. Action.\nHuman correction. Outcome.',23,'paper')
        a.rect(64,989,952,1,'sage')
        a.text(64,1017,952,36,c['footer'],13,'sage')
    else:
        a.text(44,30,524,50,c['brand'],28,display=True)
        a.text(44,91,524,26,'WEBSITE / CREATIVE BRIEF',10)
        a.text(42,134,530,100,c['brief_title'],34,display=True)
        for i,(label,key) in enumerate([('01 / AUDIENCE','audience'),('02 / PRIMARY GOAL','objective'),
                                        ('03 / REQUIRED ASSETS','deliverables'),('04 / EVIDENCE AND SCOPE','proof')]):
            y=255+i*103
            a.rect(44,y-8,524,1,'sage')
            a.text(44,y,524,23,label,10)
            a.text(44,y+28,524,63,c[key],13)
        a.text(44,690,524,50,c['guardrail'],10)
        a.text(44,755,524,21,'WORKING TEMPLATE / CONTENT TO REVIEW BEFORE PUBLICATION',8)
    return a


def export(cli, name, output, values):
    output.mkdir(parents=True,exist_ok=True)
    script=output/(name+'.dcs')
    native=output/(name+'.designcraft')
    script.write_text(make(name,values).script())
    result=subprocess.run([cli,'script',str(script),'--save',str(native)],text=True,capture_output=True,check=True)
    parsed=json.loads(result.stdout)
    if parsed.get('error'):
        raise ValueError(name+': '+str(parsed['error']))
    inspection=subprocess.check_output([cli,'run','--in',str(native),'--cmd','document.inspect'],text=True)
    inspect=json.loads(inspection)
    overflow=[s for s in inspect['stories'] if s.get('overset')]
    if overflow:
        raise ValueError(name+': text does not fit; shorten the content. No raster/PDF exported.')
    subprocess.run([cli,'run','--in',str(native),'--scale','1','--export',str(output/(name+'.png')),
                    '--export',str(output/(name+'.pdf'))],text=True,capture_output=True,check=True)
    png=(output/(name+'.png')).read_bytes()
    dimensions=list(struct.unpack('>II',png[16:24]))
    expected=[CATALOG[name]['width'],CATALOG[name]['height']]
    if dimensions!=expected:
        raise ValueError(f'{name}: expected {expected}, got {dimensions}')
    files={}
    for suffix in ('dcs','designcraft','png','pdf'):
        path=output/(name+'.'+suffix)
        files[path.name]={'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    return {'dimensions':dimensions,'overset_stories':0,'files':files}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('list')
    p=sub.add_parser('export')
    p.add_argument('template',choices=[*CATALOG,'all'])
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--cli')
    p.add_argument('--content',type=Path)
    args=parser.parse_args()
    if args.action=='list':
        for name,item in CATALOG.items():
            print(f"{name:9} {item['width']}x{item['height']} {item['purpose']}")
        return
    executable=cli_path(args.cli)
    output=args.output.resolve()
    if output==PACK or output==REPO:
        parser.error('Choose a dedicated output directory, not the pack or repository root.')
    values=content(args.content)
    selected=list(CATALOG) if args.template=='all' else [args.template]
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.loomwell-designcraft-',dir=output.parent) as temporary:
        staging=Path(temporary)
        results={name:export(executable,name,staging,values) for name in selected}
        manifest={'tool':'designcraft','renderer':subprocess.check_output([executable,'--version'],text=True).strip(),
                  'brand':BRAND,'content':values,'templates':results,'publication_status':'design draft; review before publication'}
        manifest['files']={filename:record for item in results.values() for filename,record in item['files'].items()}
        (staging/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        output.mkdir(parents=True,exist_ok=True)
        for path in staging.iterdir():
            path.replace(output/path.name)
    print(f'Exported {len(selected)} Loomwell template(s) to {output}')


if __name__=='__main__':
    try:
        main()
    except (ValueError,OSError,json.JSONDecodeError,subprocess.CalledProcessError) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(1)

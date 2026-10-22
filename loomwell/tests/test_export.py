"""Real-engine checks for the portable Loomwell layout pack."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PACK = Path(__file__).resolve().parents[1]
CLI = os.environ.get('DESIGNCRAFT_CLI')


@unittest.skipUnless(CLI and Path(CLI).is_file(), 'set DESIGNCRAFT_CLI to the built source CLI')
class ExportTests(unittest.TestCase):
    def invoke(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(PACK/'export.py'), 'export', *map(str,args),
                               '--cli',CLI], cwd=cwd, text=True, capture_output=True)

    def test_all_templates_have_correct_dimensions_and_native_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'exports'
            result=self.invoke('all','--output',out,cwd=tmp)
            self.assertEqual(result.returncode,0,result.stderr)
            manifest=json.loads((out/'manifest.json').read_text())
            for name, expected in {'website':[1600,900],'social':[1200,630],
                                   'square':[1080,1080],'brief':[612,792]}.items():
                item=manifest['templates'][name]
                self.assertEqual(item['dimensions'],expected)
                self.assertEqual(item['overset_stories'],0)
                for filename,record in item['files'].items():
                    self.assertEqual(hashlib.sha256((out/filename).read_bytes()).hexdigest(),record['sha256'])
                self.assertTrue((out/(name+'.pdf')).read_bytes().startswith(b'%PDF-'))
                reloaded=Path(tmp)/(name+'-reloaded.png')
                subprocess.run([CLI,'run','--in',str(out/(name+'.designcraft')),'--scale','1',
                                '--export',str(reloaded)],check=True,capture_output=True)
                self.assertEqual(reloaded.read_bytes(),(out/(name+'.png')).read_bytes())

    def test_common_content_override_is_rendered_from_arbitrary_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);out=tmp/'exports';custom=tmp/'content.json'
            custom.write_text(json.dumps({'headline':'See the $5 exception.\nKeep ${0.index} context.',
                                         'subheadline':'A fictional example for an evaluation discussion.',
                                         'eyebrow':'SYNTHETIC FORMAT EXAMPLE','footer':'EARLY PILOT'}))
            result=self.invoke('social','--output',out,'--content',custom,cwd=tmp)
            self.assertEqual(result.returncode,0,result.stderr)
            script=(out/'social.dcs').read_text()
            self.assertIn('See the $$5 exception.',script)
            self.assertIn('SYNTHETIC FORMAT EXAMPLE',script)
            inspection=json.loads(subprocess.check_output([CLI,'run','--in',str(out/'social.designcraft'),
                                                          '--cmd','document.inspect'],text=True))
            previews='\n'.join(item.get('preview','') for item in inspection['stories'])
            self.assertIn('See the $5 exception.',previews)
            self.assertIn('Keep ${0.index} context.',previews)

    def test_overflow_fails_without_replacing_existing_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp);out=tmp/'exports';custom=tmp/'content.json'
            result=self.invoke('social','--output',out)
            self.assertEqual(result.returncode,0,result.stderr)
            before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
            custom.write_text(json.dumps({'headline':'Word '*119}))
            result=self.invoke('social','--output',out,'--content',custom)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('text does not fit',result.stderr)
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()})


if __name__=='__main__':
    unittest.main()

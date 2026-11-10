"""Snapshot only task sources, never environment values or credentials."""
import hashlib,json,os,pathlib,shutil,sys
root=pathlib.Path(__file__).resolve().parent
out=pathlib.Path(sys.argv[1]);dst=out/'source';dst.mkdir(parents=True,exist_ok=True)
files=[p for p in root.iterdir() if p.is_file() and p.suffix in ('.py','.sh','.json','.md')]
for p in files:shutil.copy2(p,dst/p.name)
config={'label_variant':os.environ.get('LABEL_VARIANT','attack'),'seed':1,'object_jitter':0,
        'control_hz':20,'max_steps':2000,'camera_size':[640,360],
        'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(out/'run_config.json').write_text(json.dumps(config,indent=2)+'\n')
print('Run configuration saved; label variant:',config['label_variant'])

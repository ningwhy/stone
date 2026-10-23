#!/usr/bin/env python3
"""Serial generation using the user-supplied local-image-studio skill.

The zip is intentionally not installed globally. Extract it into .local-tools first.
Every successful source and its parameter record are retained; existing jobs skip.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--only', nargs='+', help='IDs from art/generation-plan.json')
args = parser.parse_args()
plan = json.loads((ROOT/'art/generation-plan.json').read_text())
skill = ROOT/'.local-tools/local-image-studio/scripts/image_studio.py'
if not skill.is_file():
    raise SystemExit('Extract the user-supplied local-image-studio.zip into .local-tools/')
output = ROOT/'art/source'
output.mkdir(parents=True, exist_ok=True)
for job in plan['jobs']:
    if args.only and job['id'] not in args.only:
        continue
    name = f"{job['id']}_s{job['seed']}"
    if (output/f'{name}-01.png').is_file():
        print(f'SKIP existing source: {name}', flush=True)
        continue
    prompt = plan['style']+'\n'+job['prompt']
    waited = 0
    while True:
        with urlopen(plan['server']+'/queue', timeout=15) as response:
            queue = json.load(response)
        depth = len(queue.get('queue_running', []))+len(queue.get('queue_pending', []))
        if not depth:
            break
        if waited % 30 == 0:
            print(f'Waiting for existing ComfyUI work: {depth} queued/running; no generation submitted.', flush=True)
        if waited >= 1800:
            raise SystemExit('ComfyUI remained busy for 30 minutes; rerun to resume.')
        time.sleep(5)
        waited += 5
    subprocess.run([sys.executable, '-u', str(skill), 'generate', '--server', plan['server'],
        '--model', 'zimage', '--ckpt', plan['model'], '--prompt', prompt,
        '--preset', job['size'], '--seed', str(job['seed']), '--name', name,
        '--prefix', f"rongguo/{name}", '--out', str(output), '--keep-old',
        '--max-queue-depth', '0', '--poll-timeout', '900'], check=True)

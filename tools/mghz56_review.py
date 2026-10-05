"""Render a local review board from previously approved MGHZ art and emulator PNGs.

Run with a Pillow-enabled Python after mghz56_fullgame.py --png. Input pixels
remain in ignored build/. This is a review recap, not a new approval or POC import.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/mghz56-review'


def main():
    data=json.loads((ROOT/'build/mghz-approval/preview-input.json').read_text())
    subject=data['subjects']['86']
    approved=json.loads((ROOT/'data/rom-cache/mghz/art-approval.json').read_text())['subjects']['0x56']
    runtime=json.loads((ROOT/'data/rom-cache/mghz/boss-56-runtime.json').read_text())
    reachable={v['frame'] for v in runtime['static']['art']['frames'] if v['frame']}
    frames=[f for f in subject['frames'] if f['frame'] in reachable]
    assert len(frames)==11
    font=ImageFont.load_default(size=13)
    board=Image.new('RGB',(1024,850),(34,41,50));draw=ImageDraw.Draw(board)
    draw.text((12,8),'MGHZ3 $56 / $57 / $58: approved canonical frames + original 256 px harness',font=font,fill='white')
    draw.text((12,29),'Art approved 2026-10-04; hashes reverified. No forced mirror. Cross = gameplay anchor.',font=font,fill='white')
    for n,f in enumerate(frames):
        im=f['images'][0]
        assert im['composed_index_sha256']==approved['frame_hashes'][str(f['frame'])][0]
        tile=Image.new('RGBA',(80,80),(63,73,84,255))
        for p in reversed(im['pieces']):
            pi=Image.new('RGBA',(8,len(p['pixels'])))
            pi.putdata([tuple(subject['palette'][c]) if c else (0,0,0,0) for row in p['pixels'] for c in row])
            tile.alpha_composite(pi,(40+p['x']+1,40+p['y']+18))
        td=ImageDraw.Draw(tile);td.line((37,40,43,40),fill='magenta');td.line((40,37,40,43),fill='magenta')
        x=2+n%6*170;y=62+n//6*184
        board.paste(tile.resize((160,160),Image.Resampling.NEAREST).convert('RGB'),(x,y))
        draw.text((x+2,y+161),f"frame {f['frame']:02d} | ext {f['extent_x_y']}",font=font,fill='white')
    y=442
    draw.text((12,y),'Original game snapshots: approximate VDP/IRQ; update-aligned synthetic fight driver',font=font,fill='white')
    for i,state in enumerate((6,9)):
        im=Image.open(OUT/f'original-state-{state:02x}.png').convert('RGB')
        board.paste(im,(i*512,y+23))
    OUT.mkdir(exist_ok=True)
    path=OUT/'boss-56-review-board.png';board.save(path)
    print(json.dumps(dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),approved_frames=len(frames))))


if __name__=='__main__':main()

#!/usr/bin/env python3
"""Import user's named Rien voice/weapon files into Fabric sound resources.
Usage: python tools/import_rien_sfx.py '/path/to/模组所需音效，用途见命名.zip'
Requires system ffmpeg for MP3 decoding; outputs OGG Vorbis (not merely renamed MP3).
"""
from __future__ import annotations
import json, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'src/main/resources/assets/oraclearsenal'
DEST=RES/'sounds'
# Only 25 approved clips are imported; the accidentally included 034 file is intentionally skipped.
MAP={
    '武器变化时的水墨声.mp3':'weapon/change_1',
    '武器变化时的水墨2.mp3':'weapon/change_2',
    '武器变化时的水墨3.mp3':'weapon/change_3',
    '打击武器音效1.mp3':'combat/impact_1',
    '打击武器音效2.mp3':'combat/impact_2',
    '挥动鞭子.mp3':'combat/whip',
    '揭下面具后的流血燃烧伤疤音效.mp3':'character/scars',
    '斩击武器金铁交鸣声.mp3':'combat/metal_clash',
    '斩击武器音效.mp3':'combat/slash_1',
    '斩击武器音效2.mp3':'combat/slash_2',
    '斩击武器音效3.mp3':'combat/slash_3',
    '斩击武器音效·4.mp3':'combat/slash_4',
    '斩击武器音效5.mp3':'combat/slash_5',
    '穿刺武器音效1.mp3':'combat/pierce_1',
    '穿刺武器音效2.mp3':'combat/pierce_2',
    '穿刺武器音效3.mp3':'combat/pierce_3',
    '被招架时的金铁打击声（应该用不到.mp3':'combat/parry',
    '里恩发力声.mp3':'character/effort_1',
    '里恩发力声2.ogg':'character/effort_2',
    '里恩发力声3.ogg':'character/effort_3',
    '里恩轻笑.ogg':'character/laugh',
    '镰刀音效.mp3':'combat/scythe_1',
    '镰刀2.mp3':'combat/scythe_2',
    '镰刀最后一击.mp3':'combat/scythe_final',
    '面具落地音效.mp3':'character/mask_drop',
}
IGNORED = {'034_Indexfather_sq2_1.ogg.mp3'}
EVENTS={
    'weapon_change':['weapon/change_1','weapon/change_2','weapon/change_3'],
    'strike_slash':['combat/slash_'+str(i) for i in range(1,6)],
    'strike_impact':['combat/impact_1','combat/impact_2'],
    'strike_pierce':['combat/pierce_'+str(i) for i in range(1,4)],
    'strike_whip':['combat/whip'],
    'strike_scythe':['combat/scythe_1','combat/scythe_2'],
    'strike_scythe_final':['combat/scythe_final'],
    'metal_clash':['combat/metal_clash'],
    'parry':['combat/parry'],
    'rien_effort':['character/effort_'+str(i) for i in range(1,4)],
    'rien_laugh':['character/laugh'],
    'mask_drop':['character/mask_drop'],
    'mask_scars':['character/scars'],
}

def main(src:Path):
    if not src.is_file():raise SystemExit('Missing user ZIP: '+str(src))
    with zipfile.ZipFile(src) as z:
        names=[n for n in z.namelist() if not n.endswith('/') and not n.startswith('__MACOSX/')]
        missing=set(MAP)-{Path(n).name for n in names}
        extra={Path(n).name for n in names}-set(MAP)-IGNORED
        if missing or extra: raise SystemExit(f'Unrecognized SFX archive! Missing: {missing}; additional: {extra}')
        DEST.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory() as folder:
            for name in names:
                short=Path(name).name
                if short in IGNORED:
                    print('Skipping accidental sound:',short)
                    continue
                with z.open(name) as f:
                    source=Path(folder)/short
                    source.write_bytes(f.read())
                target=DEST/(MAP[short]+'.ogg')
                target.parent.mkdir(parents=True,exist_ok=True)
                run=subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(source),'-vn',
                     '-c:a','libvorbis','-q:a','4','-ar','44100',str(target)],capture_output=True,text=True)
                if run.returncode:raise RuntimeError(short+': '+run.stderr)
                print(short,'=>',target.relative_to(ROOT))
    # Never leave an obsolete clip behind when rerunning the importer.
    obsolete = DEST/'cinematic/sq2_1.ogg'
    if obsolete.is_file():
        obsolete.unlink()
    sounds={
       event:{'subtitle':'subtitles.oraclearsenal.'+event,
              'sounds':[{'name':'oraclearsenal:'+s,'type':'file'} for s in items]}
       for event,items in EVENTS.items()
    }
    (RES/'sounds.json').write_text(json.dumps(sounds,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # compact source mapping for user-facing review
    documentation=['# 里恩模组 V0.10.6 音效映射表',
        '', '原始压缩包中只有 25 个有效音效需要转换，误加入的 034 文件不打包。',
        '注意：文件 `034_Indexfather_sq2_1.ogg.mp3` 没有中文用途说明，暂作为 V 键 CA 起手演出声。',
        '声音不再从 Wiki 下载，完全使用用户提供的文件。',
        '', '| 原文件 | 游戏资源路径 |', '|---|---|']
    documentation[2]=f'原始压缩包中 {len(MAP)} 个文件全部转换为真正的 OGG Vorbis 并打包。'
    for file,out in MAP.items(): documentation.append(f'| {file} | `sounds/{out}.ogg` |')
    documentation += ['', '## 触发规则',
        '- 普通右键瞬移+随机武器变化：仅在成功变形后播一次 `weapon_change`，无瞬移音效。',
        '- Replica / V 键 CA：每一式变形播一次 `weapon_change`；接触判定独立播放当前武器对应的打击声。',
        '- NPC：瞬移本身无音效，`morph` 时播放一次 `weapon_change`。',
        '- 普通近战与技能按照九式分类：1斩击、2穿刺、3斩击、4穿刺、5打击、6斩击、7穿刺、8长鞭、9镰刀。',
        '- 镰刀终结播 `strike_scythe_final`。长枪三刺按命中次数播放 `strike_pierce`。',
        '- 测试性格挡、金铁交鸣按格挡/护甲情况播放。',
        '- NPC半血摘面具：伤疤音；面具落地：落地音；NPC战斗有少量发力声，时不时轻笑。',
        '- 指令传呼机使用原版音符盒提示音。',
        '- V 键 CA 不再使用误加入的 `034_Indexfather_sq2_1.ogg.mp3`。']
    (ROOT/'SFX_MAPPING_V0106.md').write_text('\n'.join(documentation)+'\n',encoding='utf8')
    assert sum(1 for _ in DEST.rglob('*.ogg'))==len(MAP)
    print('Converted',len(MAP),'unique sound clips in',len(EVENTS),'sound events')

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('Usage: python tools/import_rien_sfx.py <source ZIP>')
    main(Path(sys.argv[1]))

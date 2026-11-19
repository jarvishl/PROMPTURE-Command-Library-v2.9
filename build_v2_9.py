#!/usr/bin/env python3
"""Build PROMPTURE Command Library v2.9 from v2.8 index.html.

Moves '🧵 Fabric Realism & Material Physics' (200 commands):
- From: STUDIO (old #2161-#2360)
- To: Outfit (renumbered to #401-#600)
- STUDIO count: 2960 -> 2760 (remaining studio commands renumbered 2161..2760)
- Outfit count: 400 -> 600
- Adds Favorites migration v5 -> v6
"""
import json
import re
import shutil

SRC = 'index.html'
BACKUP = 'index.html.v2_8_bak'

def main():
    shutil.copy2(SRC, BACKUP)
    html = open(SRC, encoding='utf-8').read()
    m = re.search(r'<script>\n(.*?)\n</script>', html, re.S)
    assert m, 'script block not found'
    js = m.group(1)

    # 1. Parse existing COMMANDS
    old_cmds = json.loads(re.search(r'COMMANDS = (\[.*?\]);\nconst CAT_ORDER', js, re.S).group(1))
    assert len(old_cmds) == 4626, f'Expected baseline 4626, got {len(old_cmds)}'
    assert old_cmds[2180]['category'] == '🔧 Fix, Repair & Inpaint'
    assert old_cmds[2380]['category'] == '🧵 Fabric Realism & Material Physics' and old_cmds[2380]['num'] == 2161
    assert old_cmds[2579]['category'] == '🧵 Fabric Realism & Material Physics' and old_cmds[2579]['num'] == 2360
    assert old_cmds[2580]['category'] == '📸 Flash, Film & Modern Camera Aesthetics' and old_cmds[2580]['num'] == 2361
    assert old_cmds[3179]['category'] == '🖼️ Output Format, Layout & Commercial Shots' and old_cmds[3179]['num'] == 2960
    assert old_cmds[3180]['collection'] == 'outfit' and old_cmds[3180]['num'] == 1
    assert old_cmds[3579]['collection'] == 'outfit' and old_cmds[3579]['num'] == 400

    # 2. Slice and transform
    prefix = old_cmds[:2380] # prompture (220) + studio 1..1960 + Fix (200) -> 2380 items
    fabric_cmds = old_cmds[2380:2580] # 200 items to move to Outfit
    rest_studio = old_cmds[2580:3180] # Flash, Prop, Output (600 items)
    outfit_cmds = old_cmds[3180:3580] # Original outfit 1..400 (400 items)
    suffix = old_cmds[3580:] # mobile, generator, kpstudio, spec, flat, blueprint (1046 items)

    # Renumber fabric_cmds to Outfit #401-#600
    for c in fabric_cmds:
        c['collection'] = 'outfit'
        c['num'] = c['num'] - 1760 # 2161 - 1760 = 401, 2360 - 1760 = 600

    # Renumber remaining Studio commands to fill the gap (#2161-#2760)
    for c in rest_studio:
        c['num'] = c['num'] - 200 # 2361 - 200 = 2161, 2960 - 200 = 2760

    new_cmds = prefix + rest_studio + outfit_cmds + fabric_cmds + suffix
    assert len(new_cmds) == 4626, f'Expected 4626, got {len(new_cmds)}'
    print('[OK] Sliced, renumbered and moved 200 Fabric commands to Outfit')

    # Replace COMMANDS in JS
    start = js.find('COMMANDS = [')
    end_marker = '];\nconst CAT_ORDER'
    end = js.find(end_marker, start)
    assert start >= 0 and end > start
    new_json = 'COMMANDS = [' + ', '.join(json.dumps(e, ensure_ascii=False) for e in new_cmds)
    js = js[:start] + new_json + js[end:]

    # 3. Update CAT_ORDER
    co_start = js.find('const CAT_ORDER = ')
    co_end_marker = ';\nconst COLL_NAME'
    co_end = js.find(co_end_marker, co_start)
    assert co_start >= 0 and co_end > co_start
    co = json.loads(js[co_start + len('const CAT_ORDER = '):co_end])
    
    # Remove from studio
    cat_name = '🧵 Fabric Realism & Material Physics'
    assert cat_name in co['studio']
    co['studio'].remove(cat_name)
    assert len(co['studio']) == 18

    # Insert into outfit right after '🧵 Fabric — Type, Weight, Texture, Sheen'
    assert cat_name not in co['outfit']
    orig_idx = co['outfit'].index('🧵 Fabric — Type, Weight, Texture, Sheen')
    co['outfit'].insert(orig_idx + 1, cat_name)
    assert len(co['outfit']) == 18

    js = js[:co_start] + 'const CAT_ORDER = ' + json.dumps(co, ensure_ascii=False) + js[co_end:]
    print('[OK] Updated CAT_ORDER (Studio: 18 cats, Outfit: 18 cats)')

    # 4. Add migrateFavsV6 and update favorites migration
    mig_v6 = (
        'function migrateFavsV6(old){ const out=[]; old.forEach(i=>{ '
        'let ni; if(i<2380) ni=i; else if(i<2580) ni=i+1000; else if(i<3580) ni=i-200; else ni=i; '
        'if(ni>=0&&ni<4626&&out.indexOf(ni)<0) out.push(ni); }); return out; }\n'
    )
    anchor = 'function migrateFavsV5(old)'
    assert anchor in js, 'migrateFavsV5 anchor not found'
    js = js.replace(anchor, mig_v6 + anchor, 1)

    old_load = (
        "let favs=[]; try{ const v5=localStorage.getItem('prompture_cmd_favs_v5');\n"
        "  if(v5!==null){ favs=JSON.parse(v5); }\n"
        "  else { const v4=localStorage.getItem('prompture_cmd_favs_v4');\n"
        "    if(v4!==null){ favs=migrateFavsV5(JSON.parse(v4)); }\n"
        "    else { const v3=localStorage.getItem('prompture_cmd_favs_v3');\n"
        "      if(v3!==null){ favs=migrateFavsV5(migrateFavsV4(JSON.parse(v3))); }\n"
        "      else { favs=migrateFavsV5(migrateFavsV4(migrateFavs(JSON.parse(localStorage.getItem('prompture_cmd_favs_v2')||'[]')))); } }\n"
        "    try{ localStorage.setItem('prompture_cmd_favs_v5', JSON.stringify(favs)); }catch(e){} }\n"
        "}catch(e){ favs=[]; }"
    )
    new_load = (
        "let favs=[]; try{ const v6=localStorage.getItem('prompture_cmd_favs_v6');\n"
        "  if(v6!==null){ favs=JSON.parse(v6); }\n"
        "  else { const v5=localStorage.getItem('prompture_cmd_favs_v5');\n"
        "    if(v5!==null){ favs=migrateFavsV6(JSON.parse(v5)); }\n"
        "    else { const v4=localStorage.getItem('prompture_cmd_favs_v4');\n"
        "      if(v4!==null){ favs=migrateFavsV6(migrateFavsV5(JSON.parse(v4))); }\n"
        "      else { const v3=localStorage.getItem('prompture_cmd_favs_v3');\n"
        "        if(v3!==null){ favs=migrateFavsV6(migrateFavsV5(migrateFavsV4(JSON.parse(v3)))); }\n"
        "        else { favs=migrateFavsV6(migrateFavsV5(migrateFavsV4(migrateFavs(JSON.parse(localStorage.getItem('prompture_cmd_favs_v2')||'[]'))))); } } }\n"
        "    try{ localStorage.setItem('prompture_cmd_favs_v6', JSON.stringify(favs)); }catch(e){} }\n"
        "}catch(e){ favs=[]; }"
    )
    assert old_load in js, 'old load block not found'
    js = js.replace(old_load, new_load, 1)

    old_save = "function saveFavs(){ localStorage.setItem('prompture_cmd_favs_v5'"
    assert old_save in js, 'old saveFavs not found'
    js = js.replace(old_save, "function saveFavs(){ localStorage.setItem('prompture_cmd_favs_v6'", 1)
    print('[OK] Added Favorites v5 -> v6 migration')

    # 5. Update UI counts in JS
    assert "🎨 STUDIO (2960)</button>'" in js
    js = js.replace("🎨 STUDIO (2960)</button>'", "🎨 STUDIO (2760)</button>'", 1)
    assert "👗 Outfit (400)</button>'" in js
    js = js.replace("👗 Outfit (400)</button>'", "👗 Outfit (600)</button>'", 1)

    html = html[:m.start(1)] + js + html[m.end(1):]

    # 6. Update static HTML & version labels
    assert '🎨 STUDIO (2960)' in html
    html = html.replace('🎨 STUDIO (2960)', '🎨 STUDIO (2760)', 1)
    assert '👗 Outfit (400)' in html
    html = html.replace('👗 Outfit (400)', '👗 Outfit (600)', 1)
    assert 'PROMPTURE Command Library v2.8 · 4626 commands' in html
    html = html.replace(
        'PROMPTURE Command Library v2.8 · 4626 commands',
        'PROMPTURE Command Library v2.9 · 4626 commands',
        1
    )

    open(SRC, 'w', encoding='utf-8').write(html)
    print(f'[SUCCESS] Built v2.9 successfully! ({SRC} updated, backup saved at {BACKUP})')

if __name__ == '__main__':
    main()
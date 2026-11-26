#!/usr/bin/env python3
"""Build the Life Valley content review page and push it to GitHub Pages.

  publish_board.py           build site/ and push
  publish_board.py --build   build site/ only

Repo: AsifMulani1/lifevalley-content-board -> https://asifmulani1.github.io/lifevalley-content-board/
Content: content/*.md with front matter. The page is encrypted; reviewers get the key from the Sheet after login.
"""
import glob, json, os, re, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'site')
CFG = os.path.join(ROOT, 'data', 'review-config.json')
REPO = 'AsifMulani1/lifevalley-content-board'
TOOL_FILES = ['tool/board.html', 'tool/Code.gs', 'tool/SETUP.md', 'tool/publish_board.py', 'tool/reviews.py']
SECTIONS = [
    {'slug': 'start', 'name': 'Start here', 'tag': 'The content plan for the school to agree', 'colour': '#243D62'},
    {'slug': 'pages-update', 'name': 'Website pages: updates', 'tag': 'Changes to pages already on lifevalley.in', 'colour': '#008080'},
    {'slug': 'pages-new', 'name': 'Website pages: new', 'tag': 'Pages the website is missing', 'colour': '#3f7d20'},
    {'slug': 'guides', 'name': 'Guides for parents', 'tag': 'Blog articles, two a month', 'colour': '#9a6a00'},
]
FIELDS = ['id', 'section', 'month', 'publish_date', 'url', 'keyword', 'seo_title', 'meta_description', 'h1',
          'image_notes', 'web_notes', 'revision_note']


def front(text):
    m = re.match(r'^---\n(.*?)\n---\n(.*)$', text, flags=re.S)
    if not m:
        sys.exit('missing front matter')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def load_posts():
    posts = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content', '*.md'))):
        meta, body = front(open(path, encoding='utf-8').read())
        missing = [k for k in ('id', 'section', 'month', 'h1') if not meta.get(k)]
        if missing or meta['section'] not in {s['slug'] for s in SECTIONS}:
            sys.exit(f'{os.path.basename(path)}: bad front matter {missing or meta["section"]}')
        if '—' in body + str(meta) or '–' in body + str(meta):
            sys.exit(f'{os.path.basename(path)}: contains an em or en dash')
        post = {k: meta.get(k, '') for k in FIELDS}
        post.update(title=meta['h1'], body=body,
                    updated=time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(os.path.getmtime(path))) + 'Z')
        posts.append(post)
    ids = [p['id'] for p in posts]
    if len(ids) != len(set(ids)):
        sys.exit('duplicate post id')
    return posts


def config():
    # content_key locks the content; api_secret lets reviews.py read the Sheet. Neither is pushed to GitHub.
    cfg = json.load(open(CFG)) if os.path.exists(CFG) else {}
    for k, n in (('content_key', 32), ('api_secret', 24)):
        cfg.setdefault(k, os.urandom(n).hex())
    json.dump(cfg, open(CFG, 'w'), indent=1)
    return cfg


def encrypt(text, key_hex):
    # AES-256-CBC via openssl; the page decrypts it with WebCrypto after login
    iv = os.urandom(16).hex()
    out = subprocess.run(['openssl', 'enc', '-aes-256-cbc', '-K', key_hex, '-iv', iv, '-base64', '-A'],
                         input=text.encode('utf-8'), capture_output=True, check=True).stdout.decode().strip()
    return {'iv': iv, 'data': out}


def build():
    posts, cfg = load_posts(), config()
    data = {'updated': time.strftime('%d %b %Y, %H:%M'), 'sections': SECTIONS, 'posts': posts}
    html = open(os.path.join(ROOT, 'tool', 'board.html'), encoding='utf-8').read()
    html = html.replace('/*ENC*/null', json.dumps(encrypt(json.dumps(data, ensure_ascii=False), cfg['content_key'])))
    html = html.replace("/*REVIEW_URL*/''", json.dumps(cfg.get('review_url', '')))
    os.makedirs(os.path.join(SITE, 'tool'), exist_ok=True)
    open(os.path.join(SITE, 'index.html'), 'w', encoding='utf-8').write(html)
    open(os.path.join(SITE, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
    open(os.path.join(SITE, '.nojekyll'), 'w').write('')
    for src in TOOL_FILES:   # the tool's own code, no content
        shutil.copy(os.path.join(ROOT, src), os.path.join(SITE, 'tool', os.path.basename(src)))
    print(f'built site/index.html with {len(posts)} items')


def sh(*cmd):
    return subprocess.run(cmd, cwd=SITE, check=True, capture_output=True, text=True).stdout


def push():
    if not os.path.isdir(os.path.join(SITE, '.git')):
        sh('git', 'init', '-b', 'main')
        sh('git', 'remote', 'add', 'origin', f'https://github.com/{REPO}.git')
    sh('git', 'add', '-A')
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=SITE).returncode == 0:
        print('no changes'); return
    sh('git', 'commit', '-m', f'Board update {time.strftime("%Y-%m-%d %H:%M")}')
    sh('git', 'push', '-u', 'origin', 'main')
    print(f'pushed -> https://github.com/{REPO}')


def init_sheet():
    # hand the content key and API secret to the review Sheet once (it refuses to change them afterwards)
    cfg = config()
    if not cfg.get('review_url'):
        print('review_url not set in data/review-config.json: the page will say "not connected yet"'); return
    body = json.dumps({'op': 'init', 'key': cfg['content_key'], 'secret': cfg['api_secret']})
    raw = subprocess.run(['curl', '-sL', '-H', 'Content-Type: text/plain', '-d', body, cfg['review_url']],
                         capture_output=True, text=True).stdout
    try:
        r = json.loads(raw)
    except ValueError:
        print('review Sheet: no answer (check the Apps Script deployment)'); return
    print('review Sheet keys:', 'ok' if r.get('ok') else r.get('error'))


if __name__ == '__main__':
    build()
    if '--build' not in sys.argv:
        push()
        init_sheet()

"""Stage public updater metadata after uploading the matching release assets."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse, unquote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-dir', type=Path, required=True)
    parser.add_argument('--assets-published', action='store_true', required=True,
                        help='Confirm the installer and signature are already publicly available.')
    args = parser.parse_args()
    release = args.release_dir.resolve()
    site = Path(__file__).resolve().parents[1]
    manifest = json.loads((release / 'latest.json').read_text(encoding='utf-8-sig'))
    announcement = json.loads((release / 'announcement.json').read_text(encoding='utf-8-sig'))
    version = manifest.get('version', '')
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Expected a version such as 0.2.0.')
    platform = manifest['platforms']['windows-x86_64']
    parsed = urlparse(platform['url'])
    if (parsed.scheme != 'https' or parsed.netloc != 'github.com'
            or parsed.query or parsed.fragment
            or not parsed.path.startswith(f'/bpodol/landing/releases/download/v{version}/')):
        raise ValueError('The installer URL must point to this version in bpodol/landing GitHub Releases.')
    filename = unquote(parsed.path.rsplit('/', 1)[1])
    if filename != f'PLO-RangeLab_{version}_x64-setup.exe':
        raise ValueError('Unexpected installer filename.')
    if not (release / filename).is_file():
        raise ValueError('The release directory must contain the referenced installer.')
    signature = (release / f'{filename}.sig').read_text(encoding='utf-8-sig').strip()
    if not signature or signature != platform['signature']:
        raise ValueError('The manifest must use the exact contents of the installer .sig file.')
    expected = {'version': version, 'download': platform['url'], 'messages': manifest.get('notes', '')}
    if announcement != expected or not isinstance(expected['messages'], str):
        raise ValueError('The announcement and manifest do not describe the same release.')
    index_path = site / 'index.html'
    index = index_path.read_text(encoding='utf-8-sig')
    index, changes = re.subn(r'(<a class="download" href=")[^"]+(">)[^<]*(</a>)',
        lambda m: m[1] + platform['url'] + m[2] + f'Download desktop app {version}' + m[3], index)
    if changes != 1:
        raise ValueError('Could not identify the website download button.')
    updates = site / 'updates'
    updates.mkdir(exist_ok=True)
    # The two manifests are deployed together by the subsequent Git commit.
    for name, contents in [('latest.json', manifest), ('announcement.json', announcement)]:
        (updates / name).write_text(json.dumps(contents, indent=2) + '\n', encoding='utf-8')
    index_path.write_text(index, encoding='utf-8')
    print(f'Staged website metadata for {version}. Commit and push the three public files when ready.')


if __name__ == '__main__':
    main()

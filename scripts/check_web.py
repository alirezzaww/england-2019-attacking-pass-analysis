"""Check static assets and their saved-evidence mirror using only the standard library."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

class Assets(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name not in {'src', 'href'} or not value:
                continue
            url = urlsplit(value)
            if url.scheme or url.netloc or not url.path:
                continue
            target = WEB / unquote(url.path)
            assert target.is_file(), f'Missing website asset: {value}'

def main():
    Assets().feed((WEB / 'index.html').read_text(encoding='utf-8'))
    site = read(WEB / 'research.json')
    baseline = read(ROOT / 'data/11_tournament_passes_evidence.json')
    thresholds = read(ROOT / 'data/14_threshold_sensitivity_evidence.json')
    model = read(ROOT / 'data/18_first_xg_model_evidence.json')
    assert site['zone_rates'] == baseline['zone_rates_per_game'], 'Heatmap mirror differs'
    assert site['players'] == thresholds['players'], 'Player mirror differs'
    for key, total in site['totals'].items():
        assert total == len(thresholds['selected_passes'][key]), f'Total differs: {key}'
    for key, value in site['model'].items():
        assert value == model[key], f'Model mirror differs: {key}'
    for public, original in {
        'thresholds.png': 'figures/17_england_xg_threshold_sensitivity.png',
        'kirby.png': 'figures/18_kirby_passes_before_shots_profile.png',
        'xg-model.png': 'figures/21_first_xg_distance_model.png',
        'statsbomb-logo.png': 'assets/statsbomb-logo.png',
    }.items():
        assert (WEB / 'assets' / public).read_bytes() == (ROOT / original).read_bytes(), public
    print('Website assets and research mirror reconcile.')

if __name__ == '__main__':
    main()

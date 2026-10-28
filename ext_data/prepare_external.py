"""Download NSO/DOPA public elderly population; retain 2024 and latest-year context.
Run from project root. Uses only requests and pandas; never changes MongoDB.
"""
from pathlib import Path
import json
import hashlib
import requests
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'ext_data'
URL = 'https://catalogapi.nso.go.th/api/index?table=OS_0405_01_0008_01&format=json'

def main():
    DEST.mkdir(exist_ok=True)
    response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'}, timeout=90)
    response.raise_for_status()
    rows = json.loads(response.content.decode('utf-8-sig'))
    (DEST / 'nso_elderly_raw.json').write_bytes(response.content)
    raw = pd.DataFrame(rows)
    raw['YEAR'] = pd.to_numeric(raw['YEAR']).astype(int)
    raw['VALUE'] = pd.to_numeric(raw['VALUE']).astype(int)
    raw['province_name'] = raw['PROVINCE'].str.replace('จังหวัด', '', regex=False).str.strip()
    mapping = pd.read_csv(ROOT / 'provinces.csv', dtype=str).drop_duplicates('province_code')
    # Join only the seven provinces actually represented in the supplied dataset.
    combined = mapping[['province_code', 'province_name_th']].copy()
    latest = int(raw.YEAR.max())
    for year, col in [(2567, 'elderly_2024'), (latest, 'elderly_latest')]:
        part = raw[(raw.YEAR == year) & (raw.SEX == 'รวม')][['province_name', 'VALUE']]
        assert not part.province_name.duplicated().any()
        combined = combined.merge(part, left_on='province_name_th', right_on='province_name', how='left', validate='one_to_one').drop(columns='province_name').rename(columns={'VALUE': col})
    assert combined[['elderly_2024', 'elderly_latest']].notna().all().all()
    combined['year'] = 2024
    combined['latest_year'] = latest - 543
    combined['source_url'] = URL
    combined['accessed'] = '2026-10-28'
    combined.to_csv(DEST / 'province_elderly.csv', index=False, encoding='utf-8-sig')
    meta = {
        'publisher': 'National Statistical Office (NSO); source: Department of Provincial Administration (DOPA)',
        'dataset': 'Registered population aged 60+ by sex and province, OS_0405_01_0008_01',
        'catalog_url': 'https://gdcatalog.go.th/dataset/gdpublish-605',
        'download_url': URL, 'accessed': '2026-10-28',
        'reference_year': 2024, 'latest_year_available_in_download': latest - 543,
        'selection_reason': '2024 aligns with the synthetic snapshot year; 2025 retained as latest context. Annual registration date differs from June snapshot.',
        'license_as_catalogued': 'Creative Commons Attributions',
        'raw_rows': len(raw), 'clean_rows': len(combined),
        'sha256_raw': hashlib.sha256(response.content).hexdigest(),
        'warning': 'Synthetic MSO counts cannot measure real provincial coverage, prevalence or entitlement.'
    }
    (DEST / 'source_metadata.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    print(combined[['province_code', 'elderly_2024', 'elderly_latest']].to_string(index=False))

if __name__ == '__main__':
    main()

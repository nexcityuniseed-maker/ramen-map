#!/usr/bin/env python3
"""
ラーメン店舗マップ データ更新スクリプト
実行: python3 update_data.py
→ places_cache.json を生成し、ramen_map.html に埋め込む
→ 月1回実行すればOK
"""
import urllib.request, urllib.parse, json, math, time, re

API_KEY = "AIzaSyCnK1j8iAoBggsdjUkXRzLrR6ok32bNA9w"

# 店舗リスト (num, name, lat, lng) - geocode済み
STORES = [
    (1, "二兎", 35.1744006, 136.8842928),
    (2, "おダシと銀しゃり中華そば 雲雀", 35.1060517, 138.8985897),
    (3, "中華そばおにぎり 番い", 34.9526478, 137.1672608),
    (4, "中華そば 雷杏", 35.1699539, 136.878134),
    (5, "中華そば 朧月", 35.148377, 136.903674),
    (6, "肉玉中華そば 轟", 35.1676177, 136.8882241),
    (7, "ダシと麺 くじら", 35.1695562, 136.9134012),
    (8, "穂稀", 35.2300511, 136.9688237),
    ("8b", "豚ラーメン 一歩前へ", 35.2300511, 136.9688237),
    (9, "中華そば 一閃", 35.2320351, 136.8678516),
    (10, "中華そばおにぎり ◯△", 34.9905491, 135.8164081),
    (11, "中華そば レンゲ", 35.1252566, 136.9116164),
    (12, "連獅子", 35.6974081, 139.7767998),
    (13, "福岡 とら松", 33.5377911, 130.434672),
    (14, "中華そば 那由多", 34.7212531, 135.4832744),
    (15, "中華そば 麒麟", 35.7323655, 139.7076904),
    (16, "中華そば たけ虎", 34.7808728, 135.4145247),
    (17, "中華そば 三ノル", 34.5988016, 135.5119067),
    (18, "らぁ麺 ほたる", 34.9998645, 136.9653231),
    (19, "中華そば 桜花", 35.0457559, 137.0621605),
    (20, "らぁ麺 ひよこ", 35.8151365, 139.4225543),
    (21, "おダシと銀しゃり 中華そば 虹空", 34.7650519, 135.6243251),
    (22, "中華そば らんたん", 35.0096159, 135.7706801),
    (23, "おダシと銀しゃり 中華そば 無作", 35.7187038, 139.9282429),
    (24, "おダシと銀しゃり 中華そば 上々", 34.7504978, 135.5345553),
    (25, "おダシと銀しゃり 中華そば 蒼し", 34.5235228, 135.7431407),
    (26, "中華そば 樹々 kiki", 35.7055817, 139.5437062),
    (27, "つけ麺・鶏そば 鯔背ヤ", 33.8851829, 130.8783304),
    (28, "おダシと銀しゃり 中華そば 新た", 35.3286862, 139.3478065),
    (29, "背脂醤油 ラーメン庄兵衛", 34.6957799, 135.5113661),
    (30, "おダシと銀しゃり 中華そば 花道", 35.8073507, 139.7194131),
    (31, "放課後いつもの場所で", 35.1699539, 136.878134),
    (32, "中華そば・つけ麺 日はまた昇る", 35.1792178, 137.0311737),
    (33, "ラーメン・つけめん 藤虎", 35.16970800000001, 136.9010848),
    (34, "夢にカケハシ 響けハレノヒ", 37.9151804, 139.0612324),
    (35, "豚ラーメン おはよう世界", 35.15857400000001, 136.9179354),
    (36, "濃厚豚骨ラーメン 豚と小麦", 35.689769, 139.7711682),
    (37, "豚ラーメン サブロー", 35.12239880000001, 136.770016),
    (38, "ラーメン・つけめん 刻々", 34.7377076, 135.3460067),
    (40, "麺屋 啜る", 35.0148419, 135.7424284),
    (41, "麺屋 華山", 35.1661279, 136.904524),
    (42, "熊猫商店", 35.1430865, 136.9022947),
    (43, "豚大学 ラーメン学部", 35.696159, 139.7588711),
    (44, "中華そば・つけ麺 ひばり食堂", 34.7955512, 137.7611162),
    (45, "中華そば よつ葉", 35.1632508, 136.9644882),
    (46, "麺屋 才門-SIMON-", 35.1704809, 136.9016248),
]


def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlmb/2)**2
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))


def fetch(url):
    """日本語エンコーディング対応のHTTPリクエスト"""
    parsed = urllib.parse.urlparse(url)
    encoded_path = urllib.parse.quote(parsed.path)
    encoded_query = urllib.parse.quote(parsed.query, safe='=&')
    encoded_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}?{encoded_query}"
    with urllib.request.urlopen(encoded_url, timeout=15) as r:
        return json.loads(r.read())


def get_self(name, lat, lng):
    """店舗自身のGoogle Places情報を取得 (★, レビュー数)"""
    # Find Place From Text で place_id 検索
    query = f"{name} {lat},{lng}"
    url = (f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
           f"?input={query}&inputtype=textquery"
           f"&fields=place_id,name,rating,user_ratings_total,formatted_address"
           f"&locationbias=point:{lat},{lng}"
           f"&language=ja&key={API_KEY}")
    d = fetch(url)
    if d.get('status') == 'OK' and d.get('candidates'):
        c = d['candidates'][0]
        return {
            'place_id': c.get('place_id', ''),
            'google_name': c.get('name', ''),
            'rating': c.get('rating'),
            'reviews': c.get('user_ratings_total'),
            'address': c.get('formatted_address', '')
        }
    return None


def get_station(lat, lng):
    url = (f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
           f"?location={lat},{lng}&rankby=distance&type=train_station"
           f"&language=ja&key={API_KEY}")
    d = fetch(url)
    if d.get('status') == 'OK' and d.get('results'):
        s = d['results'][0]
        slat = s['geometry']['location']['lat']
        slng = s['geometry']['location']['lng']
        dist = haversine(lat, lng, slat, slng)
        return {
            'name': s['name'],
            'distance': dist,
            'walkMin': math.ceil(dist / 80),
            'lat': slat, 'lng': slng
        }
    return None


def get_ramen(lat, lng, exclude_name):
    url = (f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
           f"?location={lat},{lng}&radius=500&keyword=ラーメン&type=restaurant"
           f"&language=ja&key={API_KEY}")
    d = fetch(url)
    if d.get('status') != 'OK':
        return []
    results = []
    # 自店除外 (名前の一部一致)
    words = [w for w in exclude_name.split(' ') if len(w) >= 2]
    # ラーメン店判定キーワード (名前に含まれる必要あり)
    ramen_kws = ['ラーメン', 'らーめん', 'ラァメン', 'らぁ麺', 'らー麺',
                 '拉麺', '拉めん', '担々麺', '担担麺', '坦々麺',
                 '中華そば', '中華蕎麦', '中華ソバ',
                 '麺屋', '麺処', '麺や', '麺家', 'めん屋', 'めん処',
                 'つけ麺', 'つけめん', 'ツケメン', '油そば',
                 '家系', '二郎', '幸楽苑', '日高屋', '天下一品', '一蘭', '一風堂',
                 'Ramen', 'ramen', 'noodle', 'Noodle', 'NOODLE']

    for p in d.get('results', []):
        name = p.get('name', '')
        # 自店舗除外
        if any(w in name for w in words):
            continue
        # ラーメン店のみ (名前判定)
        if not any(kw in name for kw in ramen_kws):
            continue

        plat = p['geometry']['location']['lat']
        plng = p['geometry']['location']['lng']
        dist = haversine(lat, lng, plat, plng)
        results.append({
            'name': name,
            'distance': dist,
            'rating': p.get('rating'),
            'reviews': p.get('user_ratings_total'),
            'vicinity': p.get('vicinity', ''),
            'lat': plat, 'lng': plng,
            'place_id': p.get('place_id', '')
        })
    results.sort(key=lambda x: x['distance'])
    return results


def main():
    cache = {}
    total = len(STORES)
    for i, (num, name, lat, lng) in enumerate(STORES, 1):
        key = str(num)
        print(f"[{i}/{total}] No.{num} {name}...")
        try:
            self_info = get_self(name, lat, lng)
            time.sleep(0.2)
            station = get_station(lat, lng)
            time.sleep(0.2)
            ramen = get_ramen(lat, lng, name)
            time.sleep(0.2)
            cache[key] = {
                'self': self_info,
                'station': station,
                'ramen': ramen
            }
            rating = f"★{self_info['rating']}({self_info['reviews']}件)" if self_info and self_info.get('rating') else '-'
            st = f"{station['name']} ({station['distance']}m)" if station else 'N/A'
            print(f"  評価: {rating} / 駅: {st} / 競合: {len(ramen)}店")
        except Exception as e:
            print(f"  ERROR: {e}")
            cache[key] = {'self': None, 'station': None, 'ramen': []}

    # Save cache
    cache['_updated'] = time.strftime('%Y-%m-%d %H:%M:%S')
    with open('places_cache.json', 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"\n✓ Saved: places_cache.json (updated: {cache['_updated']})")

    # Embed into HTML
    embed_into_html(cache)
    print("✓ Updated: ramen_map.html with cached data")
    print("\n次のステップ:")
    print("  cp ramen_map.html index.html && git add index.html && git commit -m 'データ更新' && git push")


def embed_into_html(cache):
    """HTMLにキャッシュデータを埋め込む"""
    with open('ramen_map.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Build JS const
    js_data = "const PLACES_CACHE = " + json.dumps(cache, ensure_ascii=False) + ";\n"

    # Replace existing PLACES_CACHE block or insert before MESH_POP
    pattern = re.compile(r'const PLACES_CACHE = \{[\s\S]*?\};\n', re.MULTILINE)
    if pattern.search(html):
        html = pattern.sub(js_data, html)
    else:
        # Insert before MESH_POP definition
        html = html.replace('// 500mメッシュ統合データ', js_data + '\n// 500mメッシュ統合データ')

    with open('ramen_map.html', 'w', encoding='utf-8') as f:
        f.write(html)


if __name__ == '__main__':
    main()

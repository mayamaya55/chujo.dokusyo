# Force redeploy to refresh data (triggered by user request)
# Force redeploy to refresh data
import os
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# データの前処理
def load_data():
    # Googleスプレッドシートから直接CSVデータを読み込む
    sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSQmkSAmQg0URmn5u2cTIG5Vd6L0m64KtuPuWN99ITIzGFs9ELeiPUKOFRdwD0knvN5HWGNQLRBfMug/pub?gid=293316096&single=true&output=csv"
    df = pd.read_csv(sheet_url)

    # データを整形する
    records = []
    for _, row in df.iterrows():
        grade = 0
        class_name = ''
        # "担当したクラス [X年]" の列をチェックして学年を特定
        for i in range(1, 7):
            grade_col = f'担当したクラス [{i}年]'
            if grade_col in df.columns and pd.notna(row[grade_col]):
                grade = i
                class_name = row[grade_col]
                break
        
        if grade == 0:
            continue

        # 3冊分の本を処理
        for i in ['➀', '②', '③']:
            title_col = f'{i}読み聞かせした本　タイトル'
            author_col = f'{i}作家・絵・編集者など'
            # 目安時間の列名揺れに対応
            time_col_v1 = f'{i}目安（1冊あたりの時間）'
            time_col_v2 = f'{i}目安　（1冊あたりの時間）'
            time_col = None
            if time_col_v1 in df.columns:
                time_col = time_col_v1
            elif time_col_v2 in df.columns:
                time_col = time_col_v2

            if title_col in df.columns and pd.notna(row[title_col]):
                # 年度計算ロジック
                school_year_str = ''
                try:
                    # 日付をパース
                    read_date = pd.to_datetime(row['読み聞かせ日'])
                    # 4月以降ならその年、1-3月なら前年を年度とする
                    school_year = read_date.year if read_date.month >= 4 else read_date.year - 1
                    school_year_str = f'{school_year}年度'
                except (ValueError, TypeError):
                    # パース失敗時は元の日付をそのまま使う
                    school_year_str = row['読み聞かせ日']

                # --- 表示整形ロジック ---
                # クラス名に「組」がなければ追加
                class_val = str(class_name) if pd.notna(class_name) else ''
                if '組' not in class_val and class_val:
                    class_val += '組'

                # 時間に「分」がなければ追加
                raw_time_val = row.get(time_col, None) # Noneをデフォルト値として取得
                time_val = ''
                if pd.notna(raw_time_val): # NaNでないことを確認
                    time_val = str(raw_time_val)
                    if '分' not in time_val and time_val:
                        time_val += '分'
                # --- ここまで ---

                # 作家情報がない場合やNaNの場合を考慮
                author_val = row.get(author_col, None)
                if pd.isna(author_val):
                    author_val = ''

                records.append({
                    'school_year': school_year_str,
                    'grade': grade,
                    'class': class_val,
                    'title': row[title_col],
                    'author': author_val, # NaNを考慮した値
                    'time': time_val
                })
    return records

records = load_data()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query_grade = request.args.get('grade', type=int)
    
    if not query_grade:
        return jsonify([])

    results = [record for record in records if record['grade'] == query_grade]
    
    # 読み聞かせ年度でソート（新しい順）
    # '2025年度' -> 2025 のように数値に変換してソート
    def get_year_from_school_year(school_year_str):
        try:
            return int(school_year_str.replace('年度', ''))
        except ValueError:
            return 0 # パースできない場合は0として扱うか、適切なデフォルト値

    results.sort(key=lambda x: get_year_from_school_year(x.get('school_year', '')), reverse=True)

    return jsonify(results)

# --- 自動リロード用エンドポイント ---
# Renderの環境変数に `RELOAD_SECRET` を設定することを推奨
RELOAD_SECRET = os.environ.get('RELOAD_SECRET', 'changeme_to_a_long_random_string')

@app.route('/reload-data')
def reload_data():
    secret = request.args.get('secret')
    if secret != RELOAD_SECRET:
        return "Unauthorized", 401

    global records
    try:
        records = load_data()
        print("Data reloaded successfully!")
        return "Data reloaded successfully!", 200
    except Exception as e:
        print(f"Error reloading data: {e}")
        return f"Error reloading data: {e}", 500

if __name__ == '__main__':
    # ポート5001で実行し、外部からのアクセスを許可
    app.run(host='0.0.0.0', port=5001, debug=True)

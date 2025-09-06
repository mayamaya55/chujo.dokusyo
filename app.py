
import os
import pandas as pd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# データの前処理
def load_data():
    # CSVファイルを読み込む
    df = pd.read_csv('data.csv')

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
            
            if title_col in df.columns and pd.notna(row[title_col]):
                records.append({
                    'date': row['読み聞かせ日'],
                    'grade': grade,
                    'class': class_name,
                    'title': row[title_col],
                    'author': row.get(author_col, '') # 作家情報がない場合も考慮
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
    return jsonify(results)

if __name__ == '__main__':
    # ポート5001で実行し、外部からのアクセスを許可
    app.run(host='0.0.0.0', port=5001, debug=True)

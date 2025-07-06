import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, g

app = Flask(__name__)
app.config['DATABASE'] = 'database.db' # SQLiteデータベースファイル名

# --- データベース関連のヘルパー関数 ---
def get_db():
    """データベース接続を取得する"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row # カラム名でアクセスできるようにする
    return db

@app.teardown_appcontext
def close_connection(exception):
    """リクエスト終了時にデータベース接続を閉じる"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    """データベースを初期化する（テーブル作成など）"""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

# --- アプリケーションのルーティング ---

@app.route('/', methods=['GET', 'POST'])
def index():
    db = get_db()
    messages = []
    
    # 投稿処理
    if request.method == 'POST':
        message_content = request.form['message']
        username = request.form['name']
        seed = request.form['seed'] # シード値は現時点では表示のみ

        # コマンドの簡易的な処理
        if message_content.startswith('/'):
            command_parts = message_content.split(' ')
            command = command_parts[0]
            
            # /del コマンドの処理 (簡易版: 誰でも削除可能)
            # 本来は権限チェックが必要です
            if command == '/del':
                try:
                    post_ids_to_delete = [int(p) for p in command_parts[1:] if p.isdigit()]
                    if post_ids_to_delete:
                        cursor = db.cursor()
                        placeholders = ','.join('?' for _ in post_ids_to_delete)
                        cursor.execute(f"DELETE FROM messages WHERE id IN ({placeholders})", post_ids_to_delete)
                        db.commit()
                        print(f"Deleted messages with IDs: {post_ids_to_delete}")
                except Exception as e:
                    print(f"Error processing /del command: {e}")
                return redirect(url_for('index')) # コマンド処理後はリダイレクト

            # その他のコマンドはここでは未実装（必要に応じて追加）
            # 例: /NG, /speaker などはここに追加ロジックが必要です
            # コマンドとして処理された場合は、メッセージとしては保存しない
            # return redirect(url_for('index')) # コマンドが処理されたらリダイレクト
            
        # 通常メッセージの保存
        if message_content and username:
            db.execute('INSERT INTO messages (username, message_content, seed) VALUES (?, ?, ?)',
                       (username, message_content, seed))
            db.commit()
        return redirect(url_for('index')) # 投稿後はGETリクエストにリダイレクト

    # メッセージの取得
    cursor = db.execute('SELECT id, username, message_content, seed, timestamp FROM messages ORDER BY timestamp DESC')
    messages = cursor.fetchall()
    
    # 仮のトピックと格言（本来はDBから取得）
    current_topic = "岡山アンチの投稿を永遠に規制中"
    okayama_maxim = "岡山は最高です。"

    return render_template('index.html', 
                           messages=messages, 
                           current_topic=current_topic,
                           okayama_maxim=okayama_maxim)

@app.route('/bbs/how')
def how_to_use():
    return "<h1>使い方ページ（準備中）</h1><p>ここに掲示板の使い方が記載されます。</p><a href='/'>掲示板に戻る</a>"

if __name__ == '__main__':
    # データベースファイルが存在しない場合のみ初期化
    if not os.path.exists(app.config['DATABASE']):
        print("Initializing database...")
        init_db()
    app.run(debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime
import hashlib # hashlibモジュールをインポート

app = Flask(__name__)

# --- データベース設定 ---
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    print(f"PostgreSQLに接続を試みています: {app.config['SQLALCHEMY_DATABASE_URI']}")
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    sqlite_db_path = os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + sqlite_db_path
    print(f"SQLiteデータベースに接続を試みています: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- データベースモデルの定義 ---
class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    seed = db.Column(db.String(120), nullable=True) # SHA-256ハッシュの最初の70文字を格納するのに十分な長さ
    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Message {self.id}: {self.username}>'

# --- アプリケーションのルーティング ---

@app.route('/', methods=['GET'])
def index():
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).all()
    except Exception as e:
        print(f"エラー: データベースからメッセージの取得中に問題が発生しました。テーブルが存在しないか、接続に問題がある可能性があります。詳細: {e}")
        messages = []
            
    current_topic = "岡山アンチの投稿を永遠に規制中"
    
    last_name = request.args.get('last_name', '')
    last_seed = request.args.get('last_seed', '')

    return render_template('index.html', 
                           messages=messages, 
                           current_topic=current_topic,
                           last_name=last_name,
                           last_seed=last_seed)

@app.route('/post', methods=['POST'])
def post_message():
    if request.method == 'POST': 
        message_content = request.form['message']
        username = request.form['name']
        raw_seed = request.form.get('seed', '') # 生のシード値を取得

        hashed_seed = None
        if raw_seed:
            # シード値をSHA-256でハッシュ化し、最初の70文字を取得
            hashed_seed = hashlib.sha256(raw_seed.encode('utf-8')).hexdigest()[:70]
            print(f"ログ: シード値をハッシュ化しました。元のシード: '{raw_seed}' -> ハッシュ化後のシード (最初の70文字): '{hashed_seed}'") # デバッグ用ログ

        # コマンドの簡易的な処理
        if message_content.startswith('/'):
            command_parts = message_content.split(' ')
            command = command_parts[0]
            
            if command == '/del':
                try:
                    post_ids_to_delete = [int(p) for p in command_parts[1:] if p.isdigit()]
                    if post_ids_to_delete:
                        Message.query.filter(Message.id.in_(post_ids_to_delete)).delete(synchronize_session=False)
                        db.session.commit()
                        print(f"ログ: ID {post_ids_to_delete} のメッセージを削除しました。")
                except Exception as e:
                    print(f"エラー: /del コマンドの処理中に問題が発生しました。指定されたIDが見つからないか、データベース操作に失敗しました。詳細: {e}")
                return redirect(url_for('index'))
            
        # 通常メッセージの保存
        if message_content and username:
            try:
                # ハッシュ化されたシード値を使用
                new_message = Message(username=username, message_content=message_content, seed=hashed_seed)
                db.session.add(new_message)
                db.session.commit()
                print(f"ログ: 新しいメッセージが正常に投稿されました。ユーザー名: {username}")
            except Exception as e:
                print(f"エラー: メッセージのデータベースへの保存中に問題が発生しました。データベース接続やテーブル構造を確認してください。詳細: {e}")
        
        # 投稿後、名前と生のシード値をURLパラメータとして渡してリダイレクト（入力フィールドに再表示するため）
        return redirect(url_for('index', last_name=username, last_seed=raw_seed))

@app.route('/bbs/how')
def how_to_use():
    return "<h1>使い方ページ（準備中）</h1><p>ここに掲示板の使い方が記載されます。</p><a href='/'>掲示板に戻る</a>"

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all() # テーブル作成
            print("ログ: データベーステーブルの作成を試みました。")
        except Exception as e:
            print(f"エラー: データベーステーブルの作成中に問題が発生しました。データベースの接続設定や権限を確認してください。詳細: {e}")

    app.run(debug=True)

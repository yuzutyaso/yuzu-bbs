import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # text() for raw SQL in SQLAlchemy
from datetime import datetime # datetimeモジュールをインポート

app = Flask(__name__)

# --- データベース設定 ---
# RenderではDATABASE_URL環境変数が自動的に設定される
# ローカル開発ではSQLiteを使用する
if os.environ.get('DATABASE_URL'):
    # PostgreSQL接続の場合
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    print(f"Connecting to PostgreSQL: {app.config['SQLALCHEMY_DATABASE_URI']}") # ログ出力で確認
else:
    # ローカル開発用のSQLite設定
    basedir = os.path.abspath(os.path.dirname(__file__))
    sqlite_db_path = os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + sqlite_db_path
    print(f"Connecting to SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}") # ログ出力で確認

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # シグナル追跡を無効化（推奨）

db = SQLAlchemy(app)

# --- データベースモデルの定義 ---
class Message(db.Model):
    __tablename__ = 'message' # テーブル名を明示的に 'message' に設定

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    seed = db.Column(db.String(120), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Message {self.id}: {self.username}>'

# --- アプリケーションのルーティング ---

@app.route('/', methods=['GET'])
def index():
    # ホームページの表示ロジック
    # GETリクエストのみを処理します
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).all()
    except Exception as e:
        print(f"Database query error: {e}")
        # エラー発生時は空のリストを返すなど、フォールバック処理を検討
        messages = []
        # または、エラーテンプレートを表示することも可能
        # return render_template('error.html', error_message=str(e)), 500
            
    current_topic = "岡山アンチの投稿を永遠に規制中"

    return render_template('index.html', 
                           messages=messages, 
                           current_topic=current_topic)

# ここが「Method Not Allowed」エラーを解決するための主要な部分です
# /post ルートはPOSTメソッドを許可するように明示的に設定されています。
@app.route('/post', methods=['POST'])
def post_message():
    # 投稿処理ロジック
    # POSTリクエストのみを処理します
    if request.method == 'POST': 
        message_content = request.form['message']
        username = request.form['name']
        seed = request.form.get('seed', '')

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
                        print(f"Deleted messages with IDs: {post_ids_to_delete}")
                except Exception as e:
                    print(f"Error processing /del command: {e}")
                return redirect(url_for('index'))
            
        # 通常メッセージの保存
        if message_content and username:
            try:
                new_message = Message(username=username, message_content=message_content, seed=seed)
                db.session.add(new_message)
                db.session.commit()
            except Exception as e:
                print(f"Database insert error: {e}")
                # エラーメッセージをユーザーに表示するなどの処理を追加することも可能
        return redirect(url_for('index'))

@app.route('/bbs/how')
def how_to_use():
    return "<h1>使い方ページ（準備中）</h1><p>ここに掲示板の使い方が記載されます。</p><a href='/'>掲示板に戻る</a>"

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # テーブル作成

        # --- 初期データ挿入 ---
        kalpas_message_content = "ｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽｶﾙﾊﾟｽ"
        kalpas_exists = Message.query.filter_by(username="カルパス財団", message_content=kalpas_message_content).first()

        if not kalpas_exists:
            print("Inserting initial 'カルパス財団' message.")
            initial_message = Message(
                username="カルパス財団",
                message_content=kalpas_message_content,
                timestamp=datetime(2025, 7, 5, 0, 0, 0) # 過去の日付を指定することで、リストの最後に来るようにする
            )
            db.session.add(initial_message)
            db.session.commit()
        else:
            print("'カルパス財団' message already exists.")
        # --- 初期データ挿入ここまで ---

    app.run(debug=True)

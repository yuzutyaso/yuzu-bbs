import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # text() for raw SQL in SQLAlchemy

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
    # メッセージの取得
    # ここでデータベースエラーが発生している可能性が高いです
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).all()
    except Exception as e:
        print(f"Database query error: {e}")
        # エラー発生時は空のリストを返すなど、フォールバック処理を検討
        messages = []
        # または、エラーテンプレートを表示することも可能
        # return render_template('error.html', error_message=str(e)), 500
        
    current_topic = "岡山アンチの投稿を永遠に規制中"
    okayama_maxim = "岡山は最高です。"

    return render_template('index.html', 
                           messages=messages, 
                           current_topic=current_topic,
                           okayama_maxim=okayama_maxim)

@app.route('/post', methods=['POST'])
def post_message():
    if request.method == 'POST': # このif文は厳密には不要ですが、明示的に残しても問題ありません
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
        # ローカル（SQLite）の場合、database.dbが存在しない時にテーブルを作成
        # Render（PostgreSQL）の場合、DATABASE_URLが設定されていれば、テーブルを作成
        # このdb.create_all()は、初回デプロイ時にPostgreSQLにテーブルを作成するために重要です。
        # すでにテーブルが存在する場合は何もしません。
        db.create_all()

    app.run(debug=True)

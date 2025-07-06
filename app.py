import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from datetime import datetime

app = Flask(__name__)

# --- データベース設定 ---
# RenderではDATABASE_URL環境変数が自動的に設定される
# ローカル開発ではSQLiteを使用する
if os.environ.get('DATABASE_URL'):
    # PostgreSQL接続の場合
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    print(f"Connecting to PostgreSQL: {app.config['SQLALCHEMY_DATABASE_URI']}")
else:
    # ローカル開発用のSQLite設定
    basedir = os.path.abspath(os.path.dirname(__file__))
    sqlite_db_path = os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + sqlite_db_path
    print(f"Connecting to SQLite: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- データベースモデルの定義 ---
class Message(db.Model):
    __tablename__ = 'message'

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
    try:
        messages = Message.query.order_by(Message.timestamp.desc()).all()
    except Exception as e:
        print(f"Database query error: {e}")
        messages = [] # エラー時は空のリストを返す
            
    current_topic = "岡山アンチの投稿を永遠に規制中"
    
    # 名前とシード値の保持のためにURLパラメータから取得
    last_name = request.args.get('last_name', '')
    last_seed = request.args.get('last_seed', '')

    return render_template('index.html', 
                           messages=messages, 
                           current_topic=current_topic,
                           last_name=last_name, # HTMLに渡す
                           last_seed=last_seed) # HTMLに渡す

@app.route('/post', methods=['POST'])
def post_message():
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
                # エラー発生時はメッセージをログに出力
                # この場合はリダイレクトしつつ、ユーザーには成功したかのように見えてしまう
                # より良いエラーハンドリングが必要な場合は、ここでエラーメッセージを表示するテンプレートを返すなど
        
        # 投稿後、名前とシードをURLパラメータとして渡してリダイレクト
        # これにより、GETリクエストでlast_nameとlast_seedとして受け取れる
        return redirect(url_for('index', last_name=username, last_seed=seed))

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
                # 過去の日付を指定することで、リストの最後に表示されるようにする
                timestamp=datetime(2025, 7, 5, 0, 0, 0)
            )
            db.session.add(initial_message)
            db.session.commit()
        else:
            print("'カルパス財団' message already exists.")

    app.run(debug=True)

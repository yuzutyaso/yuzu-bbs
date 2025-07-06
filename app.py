import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text # text() for raw SQL in SQLAlchemy

app = Flask(__name__)

# --- データベース設定 ---
# RenderではDATABASE_URL環境変数が自動的に設定される
# ローカル開発ではSQLiteを使用する
if os.environ.get('DATABASE_URL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
else:
    # ローカル開発用のSQLite設定
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # シグナル追跡を無効化（推奨）

db = SQLAlchemy(app)

# --- データベースモデルの定義 ---
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    message_content = db.Column(db.Text, nullable=False)
    seed = db.Column(db.String(120), nullable=True) # シード値は必須ではないかもしれないのでnullableをTrueに
    timestamp = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Message {self.id}: {self.username}>'

# --- アプリケーションのルーティング ---

@app.route('/', methods=['GET', 'POST'])
def index():
    # 投稿処理
    if request.method == 'POST':
        message_content = request.form['message']
        username = request.form['name']
        seed = request.form.get('seed', '') # シードは空でもOKにするためget()を使用

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
                        # SQLAlchemyを使って削除
                        Message.query.filter(Message.id.in_(post_ids_to_delete)).delete(synchronize_session=False)
                        db.session.commit()
                        print(f"Deleted messages with IDs: {post_ids_to_delete}")
                except Exception as e:
                    print(f"Error processing /del command: {e}")
                return redirect(url_for('index'))

            # その他のコマンドはここでは未実装
            # コマンドが処理された場合は、メッセージとしては保存しない
            # return redirect(url_for('index'))
            
        # 通常メッセージの保存
        if message_content and username:
            new_message = Message(username=username, message_content=message_content, seed=seed)
            db.session.add(new_message)
            db.session.commit()
        return redirect(url_for('index'))

    # メッセージの取得
    messages = Message.query.order_by(Message.timestamp.desc()).all()
    
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
    # アプリケーションコンテキスト内でデータベースを作成
    with app.app_context():
        # データベーステーブルが存在しない場合のみ作成
        # PostgreSQLの場合、初回デプロイ時にこの行を有効にしてテーブルを作成し、
        # その後はコメントアウトするか、マイグレーションツール（Alembicなど）を使うのが一般的です。
        # SQLiteの場合、database.dbが存在しない時にテーブルを作成します。
        db.create_all()
    app.run(debug=True)

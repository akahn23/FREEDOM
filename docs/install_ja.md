# FREEDOMインストールガイド
> **翻訳について:** 本ガイドの英語版は [install.md](install.md) です。
> 本ファイルを編集する際は、両者の内容が一致するよう同じ変更で [install.md](install.md) も更新してください（[CONTRIBUTING.md](../CONTRIBUTING.md#documentation-translations) を参照）。

本ガイドはローカル環境での基本的なインストール手順を示しています。必要に応じて環境に合わせて設定内容を変更してください。
また本ガイドはWindowsの例で説明しています。Mac / Linuxの場合はパス区切りを `/` に置き換え、コマンドも適宜読み替えてください（例: `.venv\Scripts\activate` → `source .venv/bin/activate`）。

## 1. 必要なソフトウェアのインストール
### 1.1. Python 3.13.3のインストール
FREEDOM の backend を起動するには、**Python 3.13.3** が必要です。
1. [Python.org](https://www.python.org/downloads/release/python-3133/) からインストーラをダウンロードします。
2. インストーラを実行します。
   - 項目は基本的にデフォルト設定で問題ありません。
3. ターミナルを開き、以下のコマンドを実行します。
   ```bash
   python --version
   ```
4. `Python 3.13.3` と表示されればインストール成功です。

### 1.2. Node.jsのインストール
FREEDOMのfrontend起動およびログイン機能のセットアップにはNode.jsが必要です。
本手順では、動作確認済みバージョンとして **v24.18.0** を使用します。
1. [Node.js](https://nodejs.org/ja/download) から **v24.18.0** のインストーラをダウンロードします。
2. インストーラを実行します。
   - 項目は基本的にデフォルト設定で問題ありません。
3. ターミナルを開き、以下のコマンドを実行します。
   ```bash
   node -v
   ```
4. `v24.18.0` と表示されればインストール成功です。

### 1.3. PostgreSQL 16以降のインストールと設定
1. [PostgreSQL: Downloads](https://www.postgresql.org/download/) からインストーラをダウンロードします。
2. インストーラを実行します。
   - 項目は基本的にデフォルト設定で問題ありません。
   - **Stack Builder** は不要です。
   - インストール時に設定したPostgreSQLのパスワードは、後続手順で使用するため必ず控えておいてください。
3. インストール後、同時に導入される **pgAdmin** を起動します。
4. 必要に応じてPostgreSQLサーバーへの接続設定を追加します。
5. 任意の名前でデータベースを作成します。
   このデータベース名は、後続手順で使用する `dsn` および `DATABASE_URL` に必要です。

## 2. FREEDOM の開発環境を構築する
以降の手順はターミナルで実行してください。

### 2.1. backendのセットアップ
1. `backend` ディレクトリへ移動します。
   ```bash
   C:\～任意のディレクトリ～\freedom> cd .\backend\
   ```
2. Pythonの仮想環境を作成します。
   ```bash
   C:\～任意のディレクトリ～\freedom\backend> python -m venv .venv
   ```
   - `backend` ディレクトリ内に `.venv` ディレクトリが作成されていれば成功です。
3. 仮想環境を有効化します。
   ```bash
   C:\～任意のディレクトリ～\freedom\backend> .venv\Scripts\activate
   ```
   - コマンドプロンプトの先頭に `(.venv)` と表示されていれば成功です。
4. 必要なライブラリをインストールします。
   ```bash
   (.venv) C:\～任意のディレクトリ～\freedom\backend> pip install -r requirements.txt
   ```

### 2.2. frontendのセットアップ
1. `frontend` ディレクトリへ移動します。
   ```bash
   (.venv) C:\～任意のディレクトリ～\freedom\backend> cd ..\frontend\
   ```
2. 必要なライブラリをインストールします。
   ```bash
   (.venv) C:\～任意のディレクトリ～\freedom\frontend> npm install
   ```
   - `frontend` ディレクトリ内に `node_modules` が作成されていれば成功です。
> **補足**
> インストールには時間がかかる場合があります。
> 1時間以上経過しても完了しない場合は、何らかの不具合が発生している可能性があります。

## 3. FREEDOMの構成設定を行う
### 3.1. backend設定ファイルを作成する
`freedom/backend/config` にあるテンプレートファイル `dummy.py` を複製して、任意の名前を付けます。

### 3.2. `main` の設定を変更する
作成した設定ファイル内の `main` の項目を、利用環境に合わせて変更してください。
```python
# freedom.main domain
main = freedom.main.Domain(
    interface = "PostgreSQL",    # Interface name
    dsn = "postgresql://postgres:password@localhost:5432/freedom_db",  # Database DSN
    schema = "public",  # schema name
    table = "freedom_main", # table name
    update_cycle = 10,  # Update cycle in seconds
)
```
#### `dsn` の書式
```text
postgresql://ユーザ名:パスワード@ホスト:ポート/データベース名
```
#### 例
```text
postgresql://postgres:password@localhost:5432/freedom_db
```
- PostgreSQL のデフォルトユーザ名は通常 `postgres` です。

### 3.3. `user_interface` の設定を変更する
同じ設定ファイル内の `user_interface` の項目を、利用環境に合わせて変更してください。
```python
# freedom.user_interface domain
user_interface = freedom.user_interface.Domain(
    ip = "localhost",  # IP address
    port = 8080,  # Port
    origin = ["http://localhost:3000", "http://172.16.0.1:3000"]  # Allowed origins for CORS
)
```
- `ip`、`port` には、backendのWeb APIを公開するIPアドレスとポートを指定してください。
- `origin` には、frontend（Web UI）を公開するURLを指定してください。
#### 設定例
- ローカル環境のみで利用する場合
   `http://localhost:3000`
- 別端末からアクセスする場合
   `http://<FREEDOMを起動するPCのIPアドレス>:3000`

## 4. ユーザ認証機能（Better Auth）の初期設定
### 4.1. backendを起動する
1. プロジェクトルートへ移動します。
2. 仮想環境を有効化します。
   ```bash
   C:\～任意のディレクトリ～\freedom> .\backend\.venv\Scripts\activate
   ```
3. backend を起動します。
   `ファイル名` には、手順 **3.1** で `backend/config` 配下に作成した設定ファイル名を指定してください。
   ※ `.py` は不要です。
   ```bash
   (.venv) C:\～任意のディレクトリ～\freedom> python .\backend\ ファイル名
   ```
   - `2026-02-27,17:22:25.740,src.freedom.log,INFO,"launch"...` のようなログが表示されれば起動成功です。
   - 初回起動時には、この後の手順で必要な schema や table の作成、seed 投入が自動で行われます。

### 4.2. frontend用 `.env` ファイルを作成する
1. `frontend` ディレクトリへ移動します。
   ```bash
   C:\～任意のディレクトリ～\freedom> cd .\frontend\
   ```
2. `.env.example` を複製して `.env` を作成します。
   `.env.example` には、以下のような内容が記載されています。
   ```env
   # Auth Secret(Cookie署名)
   BETTER_AUTH_SECRET=
   # Better Authが使うPostgreSQL
   DATABASE_URL=postgresql://user:password@host:port/dbname?options=-c%20search_path%3Dauth
   # Better Auth(Next.js側)
   BETTER_AUTH_URL=http://localhost:3000
   # Next.js BFF -> Backend (aiohttp)
   BACKEND_BASE_URL=http://localhost:8080
   # Frontend -> Next.js BFF
   NEXT_PUBLIC_API_URL=/api/bff
   ```

### 4.3. Auth Secret を生成する
`BETTER_AUTH_SECRET` に設定する文字列を生成します。
Windowsでは、以下のコマンドを実行してください。
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```
生成された文字列を控えておいてください。
> **補足**
> 以下の公式ドキュメント記載の方法でも生成可能です。
> https://better-auth.com/docs/installation#set-environment-variables

### 4.4. `.env` を設定する
作成した `.env` に、必要な値を設定します。
`npm run dev`、`npm run build`、`npm run start` のいずれを使用する場合も、 `.env` に設定した環境変数を使用します。
```env
BETTER_AUTH_SECRET=生成した文字列
DATABASE_URL=postgresql://user:password@host:port/dbname?options=-c%20search_path%3Dauth
BETTER_AUTH_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8080
NEXT_PUBLIC_API_URL=/api/bff
```
#### 設定例
```env
BETTER_AUTH_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DATABASE_URL=postgresql://postgres:password@localhost:5432/freedom_db?options=-c%20search_path%3Dauth
BETTER_AUTH_URL=http://localhost:3000
BACKEND_BASE_URL=http://localhost:8080
NEXT_PUBLIC_API_URL=/api/bff
```
#### 各項目の説明
- `BETTER_AUTH_SECRET`
   手順 **4.3** で生成した文字列を設定します。
- `DATABASE_URL`
   Better Authが利用するPostgreSQL接続文字列です。
   必ず `?options=-c%20search_path%3Dauth` を含めて設定してください。
- `BETTER_AUTH_URL`
   frontendの公開URLです。手順 **3.3** で `origin` に指定したURLと同じ値を入力します。
- `BACKEND_BASE_URL`
   Next.jsのBFFからbackendへ接続する接続先URLです。
   backendの`ip`と`port`を使用して設定してください。
   `http://localhost:8080` の部分は、手順 **3.3** で指定した `ip`、`port` と同じ値を入力します。
- `NEXT_PUBLIC_API_URL`
   frontendからNext.jsのBFFへ接続するURLです。
   通常は `/api/bff` のまま設定してください。

### 4.5. Better Authのmigrateを実行する
backendを起動したまま、**別のターミナル**を開いて以下を実行します。
1. `frontend` ディレクトリへ移動します。
   ```bash
   C:\～任意のディレクトリ～\freedom> cd .\frontend\
   ```
2. Better Auth の migrate を実行します。
   ```bash
   C:\～任意のディレクトリ～\freedom\frontend> npx auth@~1.7 migrate --config src/lib/auth.ts
   ```
   - Better Auth 用のテーブルは、このmigrateによって作成されます。
   - 以下のメッセージが表示された場合は、 `y` を入力してください。
      ```bash
      Need to install the following packages:
      auth@1.7.xx
      Ok to proceed? (y)
      ```
      ```bash
      🔑 The migration will affect the following:
      -> name, email, emailVerified, image, createdAt, updatedAt, username, displayUsername, role, banned, banReason, banExpires fields on user table.
      -> expiresAt, token, createdAt, updatedAt, ipAddress, userAgent, userId, impersonatedBy fields on session table.
      -> accountId, providerId, userId, accessToken, refreshToken, idToken, accessTokenExpiresAt, refreshTokenExpiresAt, scope, password, createdAt, updatedAt fields on account table.
      -> identifier, value, expiresAt, createdAt, updatedAt fields on verification table.
      √ Are you sure you want to run these migrations?
      ```
   - `🚀 migration was completed successfully!` というメッセージが表示されれば成功です。

### 4.6. 初期管理者ユーザを作成する
1. `frontend` ディレクトリで以下を実行します。
   ```bash
   C:\～任意のディレクトリ～\freedom\frontend> npx tsx scripts/seed-admin.ts
   ```
   - 以下のメッセージが表示された場合は、 `y` を入力してください。
      ```bash
      Need to install the following packages:
      tsx@4.23.1
      Ok to proceed? (y)
      ```
2. 実行後、初期管理者ユーザとして以下が作成されます。
   ```text
   username: admin
   password: admin123
   ```

## 5. FREEDOMを起動する
既に手順4でbackendを起動済みの場合は、手順5.1のbackend起動は不要です。
手順5.2に進んでfrontendを起動してください。

### 5.1. backendを起動する
1. プロジェクトルートへ移動します。
2. 仮想環境を有効化します。
   ```bash
   C:\～任意のディレクトリ～\freedom> .\backend\.venv\Scripts\activate
   ```
3. backend を起動します。
   `ファイル名` には、手順 **3.1** で `backend/config` 配下に作成した設定ファイル名を指定してください。
   ※ `.py` は不要です。
   ```bash
   (.venv) C:\～任意のディレクトリ～\freedom> python .\backend\ ファイル名
   ```
   - `2026-02-27,17:22:25.740,src.freedom.log,INFO,"launch"...` のようなログが表示されれば起動成功です。

### 5.2. frontendを起動する
frontendは、開発環境で起動する方法と、build後に起動する方法があります。

#### 開発環境で起動する場合
1. 必要に応じて別のターミナルを開きます。
2. `frontend` ディレクトリへ移動します。
   ```bash
   C:\～任意のディレクトリ～\freedom> cd .\frontend\
   ```
3. frontendを起動します。
   ```bash
   C:\～任意のディレクトリ～\freedom\frontend> npm run dev
   ```

#### buildして起動する場合
1. `frontend` ディレクトリへ移動します。
   ```bash
   C:\～任意のディレクトリ～\freedom> cd .\frontend\
   ```
2. frontendをbuildします。
   ```bash
   C:\～任意のディレクトリ～\freedom\frontend> npm run build
   ```
3. build完了後、frontendを起動します。
   ```bash
   C:\～任意のディレクトリ～\freedom\frontend> npm run start
   ```

- `npm run build` および `npm run start` を実行する前に、手順 **4.4** の `.env` に必要な環境変数を設定してください。
- `npm run build` はfrontendをbuildし、`npm run start` はbuild済みのfrontendを起動します。
- buildして起動する場合も、backendを起動した状態にしてください。

frontendのポート番号を変更する場合は、以下のように起動します。
```bash
C:\～任意のディレクトリ～\freedom\frontend> npm run dev -- -p 4000
```
buildして起動する場合は、以下のように起動します。
```bash
C:\～任意のディレクトリ～\freedom\frontend> npm run start -- -p 4000
```

ポート番号を変更する場合は、手順 **3.3** の `origin` および手順 **4.4** の `BETTER_AUTH_URL` にも、変更後のポート番号を指定してください。

起動後、手順 **3.3** の `origin` に指定したURLへアクセスできれば、
frontendの起動は成功です。

## 6. 動作確認を行う
### 6.1. FREEDOM画面の表示確認
1. ブラウザで、http://localhost:3000 もしくは手順 **3.3** の `origin` に指定したURLにアクセスします。
2. FREEDOMの地図画面が表示されれば成功です。
> **補足**
> frontend 起動後、ターミナルに表示される `Local` のURLを **Ctrl キーを押しながらクリック** することでも画面を開けます。

### 6.2. ログイン画面の確認
1. 手順 **3.3** の `origin` に指定したURLへアクセスします。
   URLの末尾に `/login` を追加してください。
   ```text
   http://localhost:3000/login
   ```
   ポートを4000番に変更した場合は、次のURLになります。
   ```text
   http://localhost:4000/login
   ```
2. 以下の認証情報でログインします。
   ```text
   ユーザ名: admin
   パスワード: admin123
   ```

### 6.3. ログイン成功後の確認ポイント
ログイン後、以下の項目を確認してください。
- アカウントアイコンをクリックした際にユーザ情報が表示される
- ヘッダーに管理者用設定の歯車アイコンが表示される
- 「閲覧権限設定」と「ユーザ設定」にアクセスできる
- 左側のナビゲーションバーに「設定」が表示される

### 6.4. 初期パスワードを変更する
セキュリティの観点から、初回ログイン後にパスワードを変更してください。
#### 変更手順
- 管理者用設定のユーザ管理にアクセスする
- 対象ユーザの **「パスワード変更」** から更新する
> **注意**
> 初期管理者の新しいパスワードは **1～128文字** の範囲で設定してください。

## 7. 注意事項
**初回セットアップ**は、必ず以下の順番で実施してください。
```text
backend起動
→ Better Auth migrate実行
→ 初期管理者ユーザ作成
→ frontend起動
```
- backendが初回起動していない状態では、ユーザ認証機能に必要なテーブルが存在せず、後続手順が失敗する可能性があります。
- backend起動時にimport errorなどが発生する場合は、ライブラリのインストール漏れがないか確認してください。
- frontendやmigrate実行時にエラーが発生する場合は、
  `.env` の `DATABASE_URL`、`BETTER_AUTH_SECRET`、
  `BETTER_AUTH_URL`、`BACKEND_BASE_URL`、
  `NEXT_PUBLIC_API_URL` の設定値を再確認してください。

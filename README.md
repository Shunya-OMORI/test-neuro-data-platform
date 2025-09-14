---

# Neuro Data Platform

`Neuro Data Platform`は、脳波（EEG）や慣性計測装置（IMU）、メディアデータ（画像・音声）など、多様な神経生理学的データを収集、処理、管理、エクスポートするための、スケーラブルなマイクロサービスベースのバックエンドプラットフォームです。

## 主な特徴

- **マイクロサービスアーキテクチャ**: 各機能（データ収集、永続化、リアルタイム解析など）が独立したサービスとして動作し、高いスケーラビリティと耐障害性を実現します。
- **非同期メッセージング**: `RabbitMQ`を介してサービス間を疎結合に連携させることで、大量のデータを安定して処理します。
- **スケーラブルなストレージ**: 生データ本体をオブジェクトストレージ`MinIO`に、メタデータを`PostgreSQL/TimescaleDB`に分離して保存する「DBオフローディング」パターンを採用し、データの増大に対応します。
- **標準化されたエクスポート**: 記録したデータを、神経科学研究の標準フォーマットである\*\*BIDS (Brain Imaging Data Structure)\*\*形式でエクスポートする機能を備えています。
- **リアルタイムフィードバック**: 収集したデータを準リアルタイムで解析し、スマートフォンアプリにフィードバックを提供します。

---

## 💻 開発環境の構築

新しい開発者がこのプロジェクトをローカルマシンで起動するための手順です。

### 1\. 前提条件

以下のソフトウェアがインストールされている必要があります。

- **Git**: [公式サイト](https://git-scm.com/)
- **Docker & Docker Compose**: [公式サイト](https://www.docker.com/products/docker-desktop/)
- **Node.js**: v20以降を推奨 [公式サイト](https://nodejs.org/)
- **pnpm**: Node.jsインストール後、以下のコマンドでインストールします。
  ```sh
  npm install -g pnpm
  ```

### 2\. リポジトリのクローン

```sh
git clone https://github.com/your-username/neuro-data-platform.git
cd neuro-data-platform
```

### 3\. 環境変数の設定

プロジェクトルートにある環境変数テンプレートをコピーして、実際の設定ファイルを作成します。

```sh
cp .env.example .env
```

通常、ローカルでのテストではこのファイルの中身を変更する必要はありません。もしお使いのPCで`8080`番ポートが他のプログラムによって使用されている場合のみ、`.env`ファイル内の`NGINX_PORT`の値を`8081`などに変更してください。

### 4\. 依存関係のインストール

プロジェクトルートで以下のコマンドを実行し、全てのTypeScriptサービスの依存関係をインストールします。

```sh
pnpm install
```

### 5\. MinIOの初回セットアップ（一度だけ実行）

データの保存場所である「バケット」を作成します。

1.  **インフラサービスのみを起動します。**
    ```sh
    docker-compose up -d db rabbitmq minio
    ```
2.  **MinIOコンソールにアクセスします。**
    Webブラウザで `http://localhost:9001` を開きます。
3.  **ログインします。**
    `.env`ファイルに記載されている以下の情報を使用します。
    - **Username**: `minioadmin`
    - **Password**: `minioadmin`
4.  **バケットを作成します。**
    左メニューの「Buckets」→ 右上の「Create Bucket」をクリックし、Bucket Nameに `neuro-data` と入力して作成します。
5.  **インフラを一旦停止します。**
    ```sh
    docker-compose down
    ```

### 6\. 全サービスのビルドと起動

以下のコマンドで、全てのサービスをビルドし、起動します。初回は各サービスのイメージ構築に数分かかることがあります。

```sh
docker-compose up --build
```

ターミナルに全サービスのログが表示され始めれば成功です。`Ctrl + C`で停止し、`docker-compose down`でコンテナを完全に削除できます。

### 7\. スマートフォンアプリとの接続

1.  **PCのローカルIPアドレスを調べます。**
    - **Windows**: コマンドプロンプトで `ipconfig` を実行し、「IPv4 アドレス」を探します。（例: `192.168.1.10`）
    - **Mac/Linux**: ターミナルで `ip a` または `ifconfig` を実行し、`127.0.0.1`ではないIPアドレスを探します。
2.  **スマートフォンとPCを同じWi-Fiに接続します。**
3.  **スマートフォンアプリの設定ファイルを変更します。**
    アプリ内の`.env`ファイル（またはそれに準ずる設定ファイル）を開き、`SERVER_IP`を先ほど調べたPCのIPアドレスに、`SERVER_PORT`を`.env`ファイルで設定した`NGINX_PORT`（デフォルトは`8080`）に設定します。
4.  **アプリをビルドして実行します。**
    これで、アプリからのリクエストがあなたのPC上で動作しているサーバー群に届くようになります。

### 便利な開発コマンド

- **全サービスのバックグラウンド起動**: `docker-compose up -d`
- **全サービスの停止と削除**: `docker-compose down`
- **特定のサービスのログを表示**: `docker-compose logs -f <サービス名>` (例: `docker-compose logs -f processor`)

---

## 📂 ディレクトリとファイルの責務

このリポジトリは`pnpm`ワークスペースを利用したモノレポ構成になっています。

### ルートディレクトリ

- `.github/workflows/`: GitHub ActionsによるCI（継続的インテグレーション）設定。
  - `ci-typescript.yml`: TypeScriptのコードがプッシュされると、Lint、型チェック、ビルドを自動実行します。
  - `ci-python.yml`: Pythonのコードがプッシュされると、RuffによるLintとフォーマットチェックを自動実行します。
- `.vscode/settings.json`: VS Codeエディタの推奨設定。ファイル保存時の自動フォーマットなどを定義します。
- `apps/`: 実行可能な各マイクロサービスを格納します。
- `db/`: データベース関連のファイルを格納します。
  - `init.sql`: `docker-compose`初回起動時にPostgreSQL内にテーブルを作成するためのSQLスキーマ定義です。
- `nginx/`: リバースプロキシサーバーの設定とDockerfileを格納します。
  - `nginx.conf`: 全てのAPIリクエストを受け付け、URLに応じて適切なバックエンドサービスに振り分けます。
  - `Dockerfile`: `nginx.conf`をコンテナにコピーします。
- `packages/`: 複数のTypeScriptサービス間で共有されるコードや設定を格納します。
- `.editorconfig`: エディタ間でコーディングスタイルを統一するための設定ファイルです。
- `.env.example`: `docker-compose`が利用する全環境変数のテンプレートです。
- `.gitignore`: Gitのバージョン管理から除外するファイルを指定します。
- `docker-compose.override.yml`: 開発時のみ適用される設定。ソースコードのホットリロードなどを有効にします。
- `docker-compose.yml`: 全てのサービスを定義し、連携させるためのメインファイルです。
- `Dockerfile.typescript`: 全てのTypeScriptサービスで共有される汎用的なDockerfileです。
- `eslint.config.mjs`: プロジェクト全体のTypeScriptコード品質を保つためのESLint設定です。
- `package.json`: pnpmワークスペースのルート定義、開発ツールの依存関係、全体で使うスクリプトを記述します。
- `pnpm-workspace.yaml`: `pnpm`にモノレポの構成を教えるためのファイルです。
- `prettier.config.cjs`: プロジェクト全体のコードフォーマッター(Prettier)の設定です。
- `pyproject.toml`: プロジェクト全体のPythonツール(Ruff)の設定です。

### `packages/` （共有パッケージ）

- `tsconfig-custom/`: TypeScriptのコンパイラ設定を共有します。
  - `base.json`: 全てのTSサービスが継承する基本の`tsconfig.json`です。
- `types/`: サービス間でやり取りされるデータの型定義を共有します。
  - `src/index.ts`: `Session`, `Experiment`, `RawDataObject`など、システム全体で使われるデータ構造の型をTypeScriptの`type`や`enum`として定義します。

### `apps/` （マイクロサービス群）

#### Collector (TypeScript)

- **責務**: スマートフォンアプリから送信される全てのデータ（センサー、メディア）を受け付ける唯一のAPIゲートウェイ。
- `src/routes.ts`: `/api/v1/data`と`/api/v1/media`のエンドポイントを定義。`multer`でファイルを受け付け、メタデータと共にRabbitMQに転送します。
- `src/rabbitmq.ts`: RabbitMQへの接続とメッセージ発行ロジックを管理します。
- `src/index.ts`: Expressサーバーを起動します。

#### Processor (Python)

- **責務**: センサーデータを永続化するワーカー。
- `src/main.py`: RabbitMQの`raw_data_exchange`からメッセージを購読するメインループ。
- `src/parser.py`: `parse_raw_data()`関数が、マイコンから送られてきた圧縮バイナリを解凍し、ヘッダー（`deviceId`）とペイロード（センサー値）に分離します。
- `src/storage.py`: `upload_to_minio()`で生データをそのままMinIOに保存し、`insert_raw_data_metadata_to_db()`でそのメタデータをPostgreSQLに記録します。

#### Media Processor (TypeScript)

- **責務**: メディアデータ（画像・音声）を永続化するワーカー。
- `src/index.ts`: RabbitMQの`media_processing_queue`を購読するメインループ。
- `src/processor.ts`: `processMediaMessage()`関数が、メッセージヘッダーのメタデータを検証し、圧縮されたままのデータ本体をMinIOに、タイムスタンプなどのメタデータをPostgreSQLに書き込みます。
- `src/services.ts`: MinIOとPostgreSQLへの接続クライアントを初期化します。

#### Session Manager (TypeScript)

- **責務**: 実験とセッションのライフサイクル（作成、終了）を管理するAPIサーバー。
- `src/routes.ts`: `/api/v1/sessions/end`エンドポイントでセッション終了通知（メタデータとイベントCSV）を受け付け、DBを更新し、`DataLinker`用のジョブをRabbitMQに投入します。
- `src/rabbitmq.ts`: `enqueueDataLinkJob()`関数で、`DataLinker`へのジョブ発行を行います。

#### DataLinker (TypeScript)

- **責務**: セッション終了後に非同期で実行され、データ間の関連付けを行うワーカー。
- `src/index.ts`: RabbitMQの`datalinker_jobs_queue`を購読するメインループ。
- `src/linker.ts`: `processLinkJob()`関数が中核ロジック。セッションの時間範囲とオーバーラップするセンサーデータオブジェクトを探し、`session_object_links`中間テーブルに関連レコードを作成します。また、メディアデータの`experiment_id`も更新します。

#### Realtime Analyzer (Python)

- **責務**: センサーデータをリアルタイムで解析し、結果をAPIで提供する。
- `src/main.py`: Flaskサーバーを起動し、バックグラウンドでコンシューマーと解析ワーカースレッドを開始します。`/api/v1/users/<user_id>/analysis`エンドポイントを提供します。
- `src/consumer.py`: RabbitMQから生データを受信し、ユーザーごとのデータバッファに格納します。
- `src/data_store.py`: `UserDataStore`クラスが、スレッドセーフな形でユーザーごとのデータバッファと最新の解析結果をメモリ上に保持します。
- `src/analyzer.py`: `analysis_worker_thread()`が定期的に各ユーザーのデータを取得し、`perform_analysis()`関数で`mne-python`を使いPSDやコヒーレンスを計算・プロットします。

#### BIDS Exporter (Python)

- **責務**: 指定された実験データをBIDS形式に変換・エクスポートするバッチ処理API。
- `src/main.py`: Flaskサーバーを起動し、エクスポートタスクの開始、状態確認、ダウンロード用のエンドポイントを提供します。
- `src/worker.py`: `run_bids_export_task()`が、バックグラウンドで実行される重い処理の本体です。PostgreSQLからメタデータを取得し、MinIOから多数のデータオブジェクトをダウンロード・結合・解析し、`mne-bids`ライブラリでBIDSデータセットを生成後、ZIP圧縮します。
- `src/storage.py`: PostgreSQLとMinIOから、エクスポートに必要な全ての情報を取得するための関数群を提供します。

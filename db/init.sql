-- 実験のメタデータを管理
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- セッションのメタデータを管理
CREATE TABLE IF NOT EXISTS sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    experiment_id UUID NOT NULL REFERENCES experiments(experiment_id) ON DELETE CASCADE,
    device_id VARCHAR(255),
    start_time TIMESTAMTz NOT NULL,
    end_time TIMESTAMPTZ,
    session_type VARCHAR(50),
    -- ★★★ 追加: DataLinkerのジョブ状態を追跡するカラム ★★★
    link_status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ★★★ 追加: セッションに紐づくイベント（トリガー）情報を管理 ★★★
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    onset_s DOUBLE PRECISION NOT NULL, -- セッション開始からの秒数
    duration_s DOUBLE PRECISION NOT NULL,
    description TEXT,
    value VARCHAR(255) -- 例: 'target', 'nontarget' など
);

-- MinIOに保存された生センサーデータ（EEG, IMU等）のメタデータを管理
CREATE TABLE IF NOT EXISTS raw_data_objects (
    object_id VARCHAR(512) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    data_type VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- セッションとデータオブジェクトのN対M関係を管理する中間テーブル
CREATE TABLE IF NOT EXISTS session_object_links (
    session_id VARCHAR(255) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    object_id VARCHAR(512) NOT NULL REFERENCES raw_data_objects(object_id) ON DELETE CASCADE,
    PRIMARY KEY (session_id, object_id)
);

-- MinIOに保存された画像のメタデータを管理
CREATE TABLE IF NOT EXISTS images (
    object_id VARCHAR(512) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255), 
    experiment_id UUID REFERENCES experiments(experiment_id) ON DELETE SET NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MinIOに保存された音声クリップのメタデータを管理
CREATE TABLE IF NOT EXISTS audio_clips (
    object_id VARCHAR(512) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    session_id VARCHAR(255),
    experiment_id UUID REFERENCES experiments(experiment_id) ON DELETE SET NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- インデックスを作成して検索パフォーマンスを向上
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id);
CREATE INDEX IF NOT EXISTS idx_raw_data_user_time ON raw_data_objects (user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_session_links_object ON session_object_links (object_id);
CREATE INDEX IF NOT EXISTS idx_images_session ON images (session_id);
CREATE INDEX IF NOT EXISTS idx_audio_clips_session ON audio_clips (session_id);


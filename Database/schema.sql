-- Create a small table to store confirmations/corrections   -- COMMENT: training data lives here
CREATE TABLE IF NOT EXISTS user_labels (
    id BIGSERIAL PRIMARY KEY, -- unique label id
    user_id INTEGER NOT NULL, -- who labeled (0 for seed)
    expense_id INTEGER REFERENCES expenses(id) ON DELETE CASCADE, --optional link to an expense
    vendor TEXT NOT NULL, -- vendor string trained on
    description TEXT NOT NULL,
    chosen_cat TEXT NOT NULL, -- category the user accepted/typed
    predicted TEXT,  -- model’s prediction (for analytics)
    source TEXT NOT NULL CHECK (source IN ('confirm','correction')), -- label origin
    created_at TIMESTAMPTZ NOT NULL DEFAULT now() -- when the label was recorded
);

-- Helpful indexes for training & analytics                   -- COMMENT: speeds up queries
CREATE INDEX IF NOT EXISTS idx_labels_user_time ON user_labels(user_id, created_at DESC); -- Times in decening order (DESC)
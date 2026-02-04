-- Migration: Add user_follows table for social features
-- Run this if user_follows table doesn't exist

CREATE TABLE IF NOT EXISTS user_follows (
    id SERIAL PRIMARY KEY,
    follower_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    following_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_user_follow UNIQUE (follower_id, following_id)
);

CREATE INDEX IF NOT EXISTS idx_user_follow_follower ON user_follows(follower_id);
CREATE INDEX IF NOT EXISTS idx_user_follow_following ON user_follows(following_id);

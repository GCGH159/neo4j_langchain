"""
速记相关数据模型
"""
from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Integer, Enum, Boolean
from datetime import datetime


class Event:
    """事件表模型"""
    __tablename__ = "events"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    event_type = Column(Enum('project', 'long_term_task', 'important_event', 'personality'), nullable=False)
    status = Column(Enum('pending', 'in_progress', 'completed', 'cancelled'), default='pending')
    priority = Column(Integer, default=0)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Note:
    """速记表模型"""
    __tablename__ = "notes"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    content = Column(Text, nullable=False)
    source = Column(Enum('text', 'audio', 'image'), default='text')
    audio_url = Column(String(500))
    status = Column(Enum('active', 'archived'), default='active')
    is_starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AudioRecording:
    """录音任务表模型"""
    __tablename__ = "audio_recordings"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    note_id = Column(BigInteger, ForeignKey("notes.id", ondelete="CASCADE"), nullable=False)
    audio_url = Column(String(500), nullable=False)
    audio_duration = Column(Integer, default=0, comment="秒")
    audio_size = Column(BigInteger, default=0, comment="字节")
    audio_format = Column(String(20), default='mp3')
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    status = Column(Enum('uploading', 'processing', 'completed', 'failed'), default='uploading')
    transcript_status = Column(Enum('pending', 'processing', 'completed', 'manual_review'), default='pending')
    transcript_text = Column(Text)
    transcript_confidence = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TranscriptSegment:
    """转录分段表模型"""
    __tablename__ = "transcript_segments"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    recording_id = Column(BigInteger, ForeignKey("audio_recordings.id", ondelete="CASCADE"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    start_time = Column(Integer, nullable=False, comment="秒")
    end_time = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    confidence = Column(Integer)
    speaker = Column(String(50), comment="说话人识别")
    created_at = Column(DateTime, default=datetime.utcnow)

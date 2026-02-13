"""
录音转文字服务
"""
from typing import Optional, List, Dict
import uuid
import json

from app.config.database import mysql_db, neo4j_db, redis_db
from app.config.logging_config import log
from app.agents.transcription_agent import TranscriptionAgent
from app.services.note_service import note_service


class AudioService:
    """录音服务类"""
    
    def __init__(self):
        self.transcription_agent = TranscriptionAgent()
    
    def upload_audio(
        self,
        user_id: int,
        audio_file_path: str,
        audio_format: str = "mp3",
        sample_rate: int = 16000,
        channels: int = 1
    ) -> Dict:
        """
        上传音频文件
        
        Args:
            user_id: 用户ID
            audio_file_path: 音频文件路径
            audio_format: 音频格式
            sample_rate: 采样率
            channels: 声道数
        
        Returns:
            录音信息字典
        """
        try:
            # 1. 上传到对象存储
            audio_url = self._upload_to_oss(audio_file_path, user_id)
            
            # 2. 创建临时速记记录
            with mysql_db.get_session() as session:
                from app.models.note import Note, AudioRecording
                note = Note(
                    user_id=user_id,
                    title="录音速记",
                    content="",
                    source="audio",
                    audio_url=audio_url
                )
                session.add(note)
                session.flush()
                
                note_id = note.id
                
                # 创建录音记录
                recording = AudioRecording(
                    user_id=user_id,
                    note_id=note_id,
                    audio_url=audio_url,
                    audio_format=audio_format,
                    sample_rate=sample_rate,
                    channels=channels,
                    status="processing",
                    transcript_status="pending"
                )
                session.add(recording)
                session.flush()
                
                recording_id = recording.id
                
                log.info(f"Audio recording created: {recording_id}")
            
            return {
                "recording_id": recording_id,
                "note_id": note_id,
                "audio_url": audio_url,
                "status": "processing"
            }
        
        except Exception as e:
            log.error(f"Error uploading audio: {e}")
            raise
    
    def _upload_to_oss(self, file_path: str, user_id: int) -> str:
        """上传音频到对象存储"""
        # 这里使用模拟的OSS上传
        # 实际项目中应该使用阿里云OSS或其他对象存储服务
        filename = f"audio/{user_id}/{uuid.uuid4()}.mp3"
        audio_url = f"https://oss.example.com/{filename}"
        log.info(f"Audio uploaded to OSS: {audio_url}")
        return audio_url
    
    def transcribe_audio(
        self,
        recording_id: int,
        user_id: int
    ) -> Dict:
        """
        转录音频
        
        Args:
            recording_id: 录音ID
            user_id: 用户ID
        
        Returns:
            转录结果字典
        """
        try:
            # 1. 获取录音信息
            with mysql_db.get_session() as session:
                from app.models.note import AudioRecording
                recording = session.query(AudioRecording).filter(
                    AudioRecording.id == recording_id,
                    AudioRecording.user_id == user_id
                ).first()
                
                if not recording:
                    raise ValueError("录音记录不存在")
                
                # 更新状态
                recording.transcript_status = "processing"
                session.flush()
                
                audio_url = recording.audio_url
            
            # 2. 调用语音识别服务
            transcription_result = self.transcription_agent.transcribe(audio_url)
            
            # 3. 文本后处理
            processed_text = self.transcription_agent.post_process_text(
                transcription_result["text"]
            )
            
            # 4. 质量评估
            quality_score = self.transcription_agent.assess_quality(processed_text)
            
            # 5. 更新录音记录
            with mysql_db.get_session() as session:
                from app.models.note import AudioRecording
                recording = session.query(AudioRecording).filter(
                    AudioRecording.id == recording_id
                ).first()
                
                recording.transcript_text = processed_text
                recording.transcript_confidence = transcription_result["confidence"]
                recording.status = "completed"
                
                if quality_score < 0.7:
                    recording.transcript_status = "manual_review"
                else:
                    recording.transcript_status = "completed"
                
                session.flush()
                
                note_id = recording.note_id
            
            # 6. 更新速记内容
            with mysql_db.get_session() as session:
                from app.models.note import Note
                note = session.query(Note).filter(Note.id == note_id).first()
                if note:
                    note.title = self._generate_title(processed_text)
                    note.content = processed_text
                    session.flush()
            
            # 7. 在Neo4j中创建Note节点并关联
            note_service._create_neo4j_note(
                note_id, user_id, note.title, processed_text, "audio"
            )
            
            # 8. 调用关联分析
            note_service._incremental_relation_analysis(note_id, user_id, processed_text)
            
            # 9. 清除缓存
            redis_db.delete(f"user:{user_id}:relationships")
            
            return {
                "recording_id": recording_id,
                "note_id": note_id,
                "transcript_text": processed_text,
                "confidence": transcription_result["confidence"],
                "quality_score": quality_score,
                "needs_manual_review": quality_score < 0.7
            }
        
        except Exception as e:
            log.error(f"Error transcribing audio: {e}")
            # 更新状态为失败
            with mysql_db.get_session() as session:
                from app.models.note import AudioRecording
                recording = session.query(AudioRecording).filter(
                    AudioRecording.id == recording_id
                ).first()
                if recording:
                    recording.status = "failed"
                    recording.transcript_status = "failed"
            raise
    
    def _generate_title(self, text: str) -> str:
        """生成速记标题"""
        # 取前50个字符作为标题
        title = text[:50]
        if len(text) > 50:
            title += "..."
        return title
    
    def get_recording(self, recording_id: int, user_id: int) -> Optional[Dict]:
        """获取录音详情"""
        try:
            with mysql_db.get_session() as session:
                from app.models.note import AudioRecording
                recording = session.query(AudioRecording).filter(
                    AudioRecording.id == recording_id,
                    AudioRecording.user_id == user_id
                ).first()
                
                if not recording:
                    return None
                
                return {
                    "id": recording.id,
                    "note_id": recording.note_id,
                    "audio_url": recording.audio_url,
                    "audio_duration": recording.audio_duration,
                    "audio_format": recording.audio_format,
                    "status": recording.status,
                    "transcript_status": recording.transcript_status,
                    "transcript_text": recording.transcript_text,
                    "transcript_confidence": recording.transcript_confidence,
                    "created_at": recording.created_at.isoformat()
                }
        
        except Exception as e:
            log.error(f"Error getting recording: {e}")
            return None
    
    def get_transcript_segments(
        self,
        recording_id: int,
        user_id: int
    ) -> List[Dict]:
        """获取转录分段"""
        try:
            with mysql_db.get_session() as session:
                from app.models.note import TranscriptSegment
                segments = session.query(TranscriptSegment).filter(
                    TranscriptSegment.recording_id == recording_id
                ).order_by(TranscriptSegment.segment_index).all()
                
                return [
                    {
                        "id": seg.id,
                        "segment_index": seg.segment_index,
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                        "confidence": seg.confidence,
                        "speaker": seg.speaker
                    }
                    for seg in segments
                ]
        
        except Exception as e:
            log.error(f"Error getting transcript segments: {e}")
            return []
    
    def update_transcript(
        self,
        recording_id: int,
        user_id: int,
        transcript_text: str
    ) -> Dict:
        """
        更新转录文本（手动编辑）
        
        Args:
            recording_id: 录音ID
            user_id: 用户ID
            transcript_text: 新的转录文本
        
        Returns:
            更新结果
        """
        try:
            with mysql_db.get_session() as session:
                from app.models.note import AudioRecording
                recording = session.query(AudioRecording).filter(
                    AudioRecording.id == recording_id,
                    AudioRecording.user_id == user_id
                ).first()
                
                if not recording:
                    raise ValueError("录音记录不存在")
                
                # 更新转录文本
                recording.transcript_text = transcript_text
                recording.transcript_status = "completed"
                session.flush()
                
                note_id = recording.note_id
            
            # 更新速记内容
            with mysql_db.get_session() as session:
                from app.models.note import Note
                note = session.query(Note).filter(Note.id == note_id).first()
                if note:
                    note.content = transcript_text
                    session.flush()
            
            # 清除缓存
            redis_db.delete(f"user:{user_id}:relationships")
            
            return {
                "recording_id": recording_id,
                "note_id": note_id,
                "transcript_text": transcript_text
            }
        
        except Exception as e:
            log.error(f"Error updating transcript: {e}")
            raise


# 全局录音服务实例
audio_service = AudioService()

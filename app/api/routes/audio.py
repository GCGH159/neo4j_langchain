"""
录音相关API路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from app.services.audio_service import audio_service
from app.config.logging_config import log

router = APIRouter()


class TranscriptUpdateRequest(BaseModel):
    """更新转录文本请求"""
    transcript: str


@router.post("/upload", response_model=dict)
async def upload_audio(user_id: int, file: UploadFile = File(...)):
    """
    上传音频文件
    
    - **user_id**: 用户ID
    - **file**: 音频文件
    """
    try:
        result = await audio_service.upload_audio(
            user_id=user_id,
            file=file
        )
        return {
            "success": True,
            "message": "音频上传成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in upload_audio: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{recording_id}/transcribe", response_model=dict)
async def transcribe_audio(recording_id: int):
    """
    转录音频
    
    - **recording_id**: 录音ID
    """
    try:
        result = await audio_service.transcribe_audio(recording_id)
        return {
            "success": True,
            "message": "音频转录成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in transcribe_audio: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{recording_id}", response_model=dict)
async def get_recording(recording_id: int):
    """
    获取录音详情
    
    - **recording_id**: 录音ID
    """
    try:
        recording = await audio_service.get_recording(recording_id)
        if not recording:
            raise HTTPException(status_code=404, detail="录音不存在")
        
        return {
            "success": True,
            "data": recording
        }
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error in get_recording: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{recording_id}/segments", response_model=dict)
async def get_transcript_segments(recording_id: int):
    """
    获取转录片段
    
    - **recording_id**: 录音ID
    """
    try:
        segments = await audio_service.get_transcript_segments(recording_id)
        return {
            "success": True,
            "data": segments
        }
    except Exception as e:
        log.error(f"Error in get_transcript_segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{recording_id}/transcript", response_model=dict)
async def update_transcript(recording_id: int, request: TranscriptUpdateRequest):
    """
    更新转录文本
    
    - **recording_id**: 录音ID
    - **transcript**: 转录文本
    """
    try:
        result = await audio_service.update_transcript(
            recording_id=recording_id,
            transcript=request.transcript
        )
        return {
            "success": True,
            "message": "转录文本更新成功",
            "data": result
        }
    except Exception as e:
        log.error(f"Error in update_transcript: {e}")
        raise HTTPException(status_code=400, detail=str(e))

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { analyticsApi, courseApi, noteApi, progressApi, videoApi } from '../../api/client'
import {
  ArrowLeft, BookOpen, CheckCircle, Clock, Plus, PlayCircle,
  Pencil, RotateCcw, RotateCw, StickyNote, Trash2, X,
} from 'lucide-react'

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds || 0)))
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const rest = total % 60
  if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${String(rest).padStart(2, '0')}`
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

function getEmbedUrl(url) {
  if (!url) return null
  try {
    const parsed = new URL(url)
    if (parsed.hostname.includes('youtube.com')) {
      const id = parsed.searchParams.get('v') || parsed.pathname.split('/').filter(Boolean).pop()
      return id ? `https://www.youtube.com/embed/${id}` : null
    }
    if (parsed.hostname.includes('youtu.be')) {
      const id = parsed.pathname.split('/').filter(Boolean)[0]
      return id ? `https://www.youtube.com/embed/${id}` : null
    }
    if (parsed.hostname.includes('vimeo.com')) {
      const id = parsed.pathname.split('/').filter(Boolean)[0]
      return id ? `https://player.vimeo.com/video/${id}` : null
    }
  } catch (_) {}
  return null
}

export default function CourseLearnPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const videoRef = useRef(null)
  const progressSyncRef = useRef({ videoId: null, lastSentAt: 0, saving: false })
  const completedRef = useRef(false)
  const seekStartRef = useRef(null)
  const suppressNextSeekEventRef = useRef(false)
  const suppressAutoSeekLogUntilRef = useRef(0)
  const timelineSeekRef = useRef({ active: false, from: null, to: null })
  const [course, setCourse] = useState(null)
  const [videos, setVideos] = useState([])
  const [activeId, setActiveId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [noteText, setNoteText] = useState('')
  const [editingNoteId, setEditingNoteId] = useState(null)
  const [notes, setNotes] = useState([])
  const [noteLoading, setNoteLoading] = useState(false)

  useEffect(() => {
    Promise.all([courseApi.get(id), videoApi.list(id)])
      .then(([courseRes, videoRes]) => {
        setCourse(courseRes.data)
        setVideos(videoRes.data || [])
        setActiveId(videoRes.data?.[0]?.video_id || null)
      })
      .catch((err) => setError(err.response?.data?.error || 'Bạn chưa có quyền học khóa học này.'))
      .finally(() => setLoading(false))
  }, [id])

  const activeVideo = useMemo(
    () => videos.find(video => video.video_id === activeId) || videos[0],
    [videos, activeId]
  )
  const embedUrl = getEmbedUrl(activeVideo?.video_src)

  const logLearningEvent = useCallback((eventType, payload = {}) => {
    if (!activeVideo?.video_id || embedUrl) return
    analyticsApi.trackEvent({
      video: activeVideo.video_id,
      event_type: eventType,
      position_seconds: Math.floor(payload.position_seconds ?? currentTime),
      from_seconds: payload.from_seconds,
      to_seconds: payload.to_seconds,
      delta_seconds: payload.delta_seconds,
      playback_rate: payload.playback_rate,
      metadata: payload.metadata || {},
    }).catch(() => {
      // Analytics must never interrupt the learning flow.
    })
  }, [activeVideo?.video_id, currentTime, embedUrl])

  useEffect(() => {
    progressSyncRef.current = { videoId: activeVideo?.video_id || null, lastSentAt: 0, saving: false }
    completedRef.current = Boolean(activeVideo?.is_completed || activeVideo?.progress?.completed)
  }, [activeVideo?.video_id, activeVideo?.is_completed, activeVideo?.progress?.completed])

  const applyProgressToVideo = (videoId, progress) => {
    setVideos(prev => prev.map(video => {
      if (video.video_id !== videoId) return video
      return {
        ...video,
        progress,
        is_completed: Boolean(progress?.completed),
      }
    }))
  }

  const syncVideoProgress = async ({ current, total, completed = false }) => {
    if (!activeVideo?.video_id || embedUrl) return

    const watchedSeconds = Math.max(0, Math.floor(Number(current || 0)))
    const durationSeconds = Math.max(
      Math.floor(Number(total || 0)),
      Number(activeVideo.duration_seconds || 0)
    )
    const reachedThreshold = Boolean(durationSeconds && watchedSeconds >= durationSeconds * 0.9)
    const shouldComplete = completed || reachedThreshold

    if (!shouldComplete) {
      const now = Date.now()
      if (progressSyncRef.current.saving || now - progressSyncRef.current.lastSentAt < 15000) return
      progressSyncRef.current.lastSentAt = now
    } else if (completedRef.current) {
      return
    }

    progressSyncRef.current.saving = true
    try {
      const res = await progressApi.update(activeVideo.video_id, {
        watched_seconds: watchedSeconds,
        duration_seconds: durationSeconds,
        completed: shouldComplete,
      })
      logLearningEvent('progress_sync', {
        position_seconds: watchedSeconds,
        metadata: { duration_seconds: durationSeconds, completed: shouldComplete },
      })
      applyProgressToVideo(activeVideo.video_id, res.data)
      if (res.data?.completed) completedRef.current = true
    } catch (_) {
      // Progress tracking should never block video playback.
    } finally {
      progressSyncRef.current.saving = false
    }
  }

  useEffect(() => {
    setCurrentTime(0)
    setDuration(0)
    setNoteText('')
    setEditingNoteId(null)
    if (!activeVideo?.video_id) {
      setNotes([])
      return
    }

    setNoteLoading(true)
    noteApi.list(activeVideo.video_id)
      .then(res => setNotes(res.data || []))
      .catch(() => setNotes([]))
      .finally(() => setNoteLoading(false))
  }, [activeVideo?.video_id])

  const seekTo = (seconds, trackedEventType = null, options = {}) => {
    if (!videoRef.current) return
    const max = duration || videoRef.current.duration || 0
    const previous = videoRef.current.currentTime || currentTime || 0
    const next = Math.min(Math.max(Number(seconds || 0), 0), max)
    if (options.suppressAutoSeekLog) {
      suppressNextSeekEventRef.current = true
      suppressAutoSeekLogUntilRef.current = Date.now() + 700
    }
    if (trackedEventType) {
      suppressNextSeekEventRef.current = true
      logLearningEvent(trackedEventType, {
        position_seconds: next,
        from_seconds: Math.floor(previous),
        to_seconds: Math.floor(next),
        delta_seconds: Math.floor(next - previous),
        metadata: options.metadata || {},
      })
    }
    videoRef.current.currentTime = next
    setCurrentTime(next)
  }

  const startTimelineSeek = () => {
    const from = Math.floor(videoRef.current?.currentTime || currentTime || 0)
    timelineSeekRef.current = { active: true, from, to: from }
  }

  const updateTimelineSeek = (value, source = 'custom_timeline') => {
    const next = Math.floor(Number(value || 0))
    if (!timelineSeekRef.current.active) {
      startTimelineSeek()
    }
    timelineSeekRef.current.to = next
    seekTo(value, null, { suppressAutoSeekLog: true, metadata: { source } })
  }

  const commitTimelineSeek = (source = 'custom_timeline') => {
    const seek = timelineSeekRef.current
    timelineSeekRef.current = { active: false, from: null, to: null }
    if (seek.from === null || seek.to === null || Math.abs(seek.to - seek.from) < 2) return

    suppressAutoSeekLogUntilRef.current = Date.now() + 700
    logLearningEvent('seek', {
      position_seconds: seek.to,
      from_seconds: seek.from,
      to_seconds: seek.to,
      delta_seconds: seek.to - seek.from,
      metadata: { source },
    })
  }

  const addNote = async () => {
    if (!noteText.trim() || !activeVideo?.video_id) return
    const payload = {
      timestamp_seconds: Math.floor(currentTime),
      content: noteText.trim(),
    }

    if (editingNoteId) {
      const res = await noteApi.update(editingNoteId, { content: payload.content })
      const next = notes.map(note => note.note_id === editingNoteId ? res.data : note)
      setNotes(next.sort((a, b) => a.timestamp_seconds - b.timestamp_seconds))
    } else {
      const res = await noteApi.create(activeVideo.video_id, payload)
      const next = [...notes, res.data]
      setNotes(next.sort((a, b) => a.timestamp_seconds - b.timestamp_seconds))
    }

    setNoteText('')
    setEditingNoteId(null)
  }

  const startEditNote = (note) => {
    setEditingNoteId(note.note_id)
    setNoteText(note.content)
    seekTo(note.timestamp_seconds)
  }

  const cancelEditNote = () => {
    setEditingNoteId(null)
    setNoteText('')
  }

  const deleteNote = async (noteId) => {
    await noteApi.delete(noteId)
    const next = notes.filter(note => note.note_id !== noteId)
    setNotes(next)
    if (editingNoteId === noteId) cancelEditNote()
  }

  if (loading) {
    return <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 60 }}><div className="spinner" /></div>
  }

  if (error) {
    return (
      <div className="card" style={{ maxWidth: 560 }}>
        <h2 style={{ fontSize: 18, marginBottom: 8 }}>Không thể mở lớp học</h2>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 18 }}>{error}</p>
        <button className="btn btn-primary" onClick={() => navigate(`/courses/${id}`)}>Xem chi tiết khóa học</button>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 22 }}>
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/student/my-courses')}>
          <ArrowLeft size={14} />
        </button>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>{course?.course_name}</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>Không gian học tập của bạn</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 340px', gap: 24, alignItems: 'start' }}>
        <div>
          <div style={{
            background: '#05070d', border: '1px solid var(--border)', borderRadius: 'var(--radius-lg)',
            overflow: 'hidden', aspectRatio: '16 / 9', display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            {embedUrl ? (
              <iframe
                src={embedUrl}
                title={activeVideo.title}
                style={{ width: '100%', height: '100%', border: 0, display: 'block' }}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            ) : activeVideo?.video_src ? (
              <video
                ref={videoRef}
                key={activeVideo.video_src}
                controls
                onTimeUpdate={(e) => {
                  const nextTime = e.currentTarget.currentTime
                  const nextDuration = e.currentTarget.duration || duration || 0
                  setCurrentTime(nextTime)
                  syncVideoProgress({ current: nextTime, total: nextDuration })
                }}
                onPlay={(e) => logLearningEvent('play', {
                  position_seconds: e.currentTarget.currentTime,
                  playback_rate: e.currentTarget.playbackRate,
                })}
                onPause={(e) => {
                  if (!e.currentTarget.ended) {
                    logLearningEvent('pause', {
                      position_seconds: e.currentTarget.currentTime,
                      playback_rate: e.currentTarget.playbackRate,
                    })
                  }
                }}
                onSeeking={(e) => {
                  if (seekStartRef.current === null) {
                    seekStartRef.current = Math.floor(currentTime || e.currentTarget.currentTime || 0)
                  }
                }}
                onSeeked={(e) => {
                  const from = seekStartRef.current
                  const to = Math.floor(e.currentTarget.currentTime || 0)
                  seekStartRef.current = null
                  if (suppressNextSeekEventRef.current) {
                    suppressNextSeekEventRef.current = false
                    return
                  }
                  if (Date.now() < suppressAutoSeekLogUntilRef.current) return
                  if (from !== null && Math.abs(to - from) >= 2) {
                    logLearningEvent('seek', {
                      position_seconds: to,
                      from_seconds: from,
                      to_seconds: to,
                      delta_seconds: to - from,
                    })
                  }
                }}
                onRateChange={(e) => logLearningEvent('rate_change', {
                  position_seconds: e.currentTarget.currentTime,
                  playback_rate: e.currentTarget.playbackRate,
                })}
                onLoadedMetadata={(e) => setDuration(e.currentTarget.duration || 0)}
                onEnded={(e) => {
                  const nextDuration = e.currentTarget.duration || duration || currentTime
                  setCurrentTime(nextDuration)
                  logLearningEvent('ended', { position_seconds: nextDuration })
                  syncVideoProgress({ current: nextDuration, total: nextDuration, completed: true })
                }}
                style={{ width: '100%', height: '100%', display: 'block' }}
              >
                <source src={activeVideo.video_src} />
                Trình duyệt của bạn không hỗ trợ video.
              </video>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <BookOpen size={42} style={{ marginBottom: 12 }} />
                <p>Khóa học chưa có video.</p>
              </div>
            )}
          </div>

          {!embedUrl && activeVideo?.video_src && (
            <div className="card" style={{ marginTop: 14, padding: 16 }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr auto', gap: 12, alignItems: 'center' }}>
                <button className="btn btn-secondary btn-sm" onClick={() => seekTo(currentTime - 10, 'skip_backward_10')}>
                  <RotateCcw size={14} /> 10s
                </button>
                <input
                  type="range"
                  min="0"
                  max={duration || 0}
                  value={Math.min(currentTime, duration || currentTime)}
                  onPointerDown={startTimelineSeek}
                  onPointerUp={() => commitTimelineSeek('custom_timeline_pointer')}
                  onTouchStart={startTimelineSeek}
                  onTouchEnd={() => commitTimelineSeek('custom_timeline_touch')}
                  onKeyDown={startTimelineSeek}
                  onKeyUp={() => commitTimelineSeek('custom_timeline_keyboard')}
                  onChange={(e) => updateTimelineSeek(e.target.value)}
                  style={{ width: '100%' }}
                />
                <button className="btn btn-secondary btn-sm" onClick={() => seekTo(currentTime + 10, 'skip_forward_10')}>
                  10s <RotateCw size={14} />
                </button>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)', fontSize: 12, marginTop: 8 }}>
                <span>{formatTime(currentTime)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>
          )}

          <div className="card" style={{ marginTop: 18 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>
              {activeVideo?.title || 'Chưa có bài học'}
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.8 }}>
              {activeVideo?.description || 'Chọn một bài học trong danh sách để bắt đầu.'}
            </p>
          </div>

          <div className="card" style={{ marginTop: 18 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <StickyNote size={16} /> Ghi chú theo thời gian
            </h2>
            {embedUrl && (
              <p style={{ color: 'var(--text-muted)', fontSize: 13, marginBottom: 12 }}>
                Video nhúng YouTube/Vimeo chưa hỗ trợ lấy thời gian chính xác trong phiên bản này.
              </p>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr auto', gap: 10, alignItems: 'center', marginBottom: 14 }}>
              <span className="badge badge-blue" style={{ justifyContent: 'center' }}>
                <Clock size={11} style={{ marginRight: 4 }} /> {formatTime(currentTime)}
              </span>
              <input
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                placeholder="Ghi lại ý chính tại thời điểm này..."
                style={{
                  width: '100%', padding: '10px 12px', borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border)', background: 'var(--bg-elevated)',
                  color: 'var(--text-primary)', outline: 'none',
                }}
              />
              <button className="btn btn-primary btn-sm" onClick={addNote} disabled={!noteText.trim()}>
                <Plus size={14} /> {editingNoteId ? 'Cập nhật' : 'Lưu'}
              </button>
              {editingNoteId && (
                <button className="btn btn-secondary btn-sm" onClick={cancelEditNote}>
                  <X size={14} />
                </button>
              )}
            </div>
            {noteLoading ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Đang tải ghi chú...</p>
            ) : notes.length === 0 ? (
              <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Chưa có ghi chú nào cho video này.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {notes.map(note => (
                  <div
                    key={note.note_id}
                    style={{
                      display: 'grid', gridTemplateColumns: '70px 1fr auto', gap: 10, alignItems: 'center',
                      padding: '10px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)',
                      background: 'var(--bg-elevated)', color: 'var(--text-primary)', textAlign: 'left',
                    }}
                  >
                    <button
                      onClick={() => seekTo(note.timestamp_seconds)}
                      style={{ border: 'none', background: 'transparent', color: 'var(--accent)', fontWeight: 700, fontSize: 12, textAlign: 'left' }}
                    >
                      {formatTime(note.timestamp_seconds)}
                    </button>
                    <span style={{ fontSize: 13 }}>{note.content}</span>
                    <span style={{ display: 'flex', gap: 6 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => startEditNote(note)} title="Sửa ghi chú">
                        <Pencil size={12} />
                      </button>
                      <button className="btn btn-danger btn-sm" onClick={() => deleteNote(note.note_id)} title="Xóa ghi chú">
                        <Trash2 size={12} />
                      </button>
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'sticky', top: 20 }}>
          <div style={{ padding: 18, borderBottom: '1px solid var(--border)' }}>
            <h2 style={{ fontSize: 16, fontWeight: 700 }}>Nội dung khóa học</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{videos.length} bài học</p>
          </div>

          {videos.length === 0 ? (
            <div style={{ padding: 28, color: 'var(--text-muted)', textAlign: 'center' }}>Chưa có video.</div>
          ) : (
            videos.map(video => {
              const active = video.video_id === activeVideo?.video_id
              const completed = Boolean(video.is_completed)
              return (
                <button
                  key={video.video_id}
                  onClick={() => setActiveId(video.video_id)}
                  style={{
                    width: '100%', display: 'grid', gridTemplateColumns: '28px 1fr auto',
                    gap: 10, alignItems: 'center', padding: '14px 18px',
                    background: completed ? 'var(--success)' : active ? 'var(--bg-elevated)' : 'transparent',
                    color: completed ? '#fff' : 'var(--text-primary)',
                    border: 'none',
                    borderBottom: completed ? '1px solid rgba(255,255,255,0.18)' : '1px solid var(--border)',
                    textAlign: 'left',
                  }}
                >
                  {completed ? (
                    <CheckCircle size={18} color="#fff" />
                  ) : active ? (
                    <PlayCircle size={18} color="var(--accent)" />
                  ) : (
                    <CheckCircle size={18} color="var(--text-muted)" />
                  )}
                  <span style={{ minWidth: 0 }}>
                    <span style={{ display: 'block', fontWeight: active ? 700 : 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {video.order}. {video.title}
                    </span>
                    {video.description && (
                      <span style={{
                        display: 'block',
                        color: completed ? 'rgba(255,255,255,0.78)' : 'var(--text-muted)',
                        fontSize: 12,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}>
                        {video.description}
                      </span>
                    )}
                  </span>
                  <span style={{ color: completed ? 'rgba(255,255,255,0.78)' : 'var(--text-muted)', fontSize: 12 }}>
                    {formatTime(video.duration_seconds)}
                  </span>
                </button>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}

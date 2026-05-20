import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { analyticsApi, courseApi, videoApi } from '../../api/client'
import { AlertTriangle, Flame, ArrowLeft, BarChart2, Bot, Ruler, RefreshCw, CheckCircle, Loader, Users, Video, ChevronDown } from 'lucide-react'

export default function CourseAnalyticsPage() {
  const { id } = useParams()
  const [course, setCourse] = useState(null)
  const [atRiskData, setAtRiskData] = useState(null)
  const [learningStylesData, setLearningStylesData] = useState(null)
  const [videos, setVideos] = useState([])
  const [selectedVideoId, setSelectedVideoId] = useState(null)
  const [heatmapData, setHeatmapData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [training, setTraining] = useState(false)
  const [trainResult, setTrainResult] = useState(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      courseApi.get(id),
      analyticsApi.courseAtRisk(id),
      analyticsApi.learningStyles(id),
      videoApi.list(id)
    ])
      .then(([courseRes, riskRes, stylesRes, videoRes]) => {
        setCourse(courseRes.data)
        setAtRiskData(riskRes.data)
        setLearningStylesData(stylesRes.data)
        const vids = videoRes.data || []
        setVideos(vids)
        if (vids.length > 0) setSelectedVideoId(vids[0].video_id)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    if (!selectedVideoId) return
    analyticsApi.videoHeatmap(selectedVideoId)
      .then(res => setHeatmapData(res.data))
      .catch(console.error)
  }, [selectedVideoId])

  const handleTrainModel = async () => {
    setTraining(true)
    setTrainResult(null)
    try {
      const res = await analyticsApi.trainDropoutModel()
      setTrainResult({ success: true, data: res.data })
      // Reload at-risk data to reflect new model
      const riskRes = await analyticsApi.courseAtRisk(id)
      setAtRiskData(riskRes.data)
    } catch (err) {
      setTrainResult({ success: false, error: err.response?.data?.message || 'Training thất bại' })
    } finally {
      setTraining(false)
    }
  }

  if (loading) return <div style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><div className="spinner" /></div>

  const modelType = atRiskData?.model_type || 'rule-based'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28 }}>
        <Link to="/instructor/courses" className="btn btn-secondary btn-sm"><ArrowLeft size={14} /></Link>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={24} color="var(--accent)" /> Thống kê & Phân tích ML
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>{course?.course_name}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 32 }}>
        
        {/* Tính năng 2: At-Risk Detection + Dropout Prediction */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <AlertTriangle color="var(--danger)" />
              <h2 style={{ fontSize: 18, fontWeight: 700 }}>Học viên cảnh báo (At-Risk Students)</h2>
              {/* Model type badge */}
              {modelType === 'random_forest' ? (
                <span className="badge badge-blue" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, padding: '4px 10px', marginLeft: 8 }}>
                  <Bot size={13} /> AI Model (Tự động cập nhật mỗi 02:00 AM)
                </span>
              ) : (
                <span className="badge badge-yellow" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, padding: '4px 10px', marginLeft: 8 }}>
                  <Ruler size={13} /> Rule-based
                </span>
              )}
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
            Hệ thống AI phân tích hành vi học tập để dự đoán những sinh viên có khả năng bỏ học cao nhất.
          </p>

          {!atRiskData?.students?.length ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có dữ liệu sinh viên.</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '12px 0' }}>Học viên</th>
                    <th>Tiến độ</th>
                    <th>{modelType === 'random_forest' ? 'Xác suất bỏ học' : 'Điểm nguy cơ'}</th>
                    <th>Lý do cảnh báo</th>
                  </tr>
                </thead>
                <tbody>
                  {atRiskData.students.map(s => (
                    <tr key={s.student_id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '12px 0', fontWeight: 500 }}>{s.student_name}</td>
                      <td>{Number(s.course_progress_percent || 0).toFixed(1)}%</td>
                      <td>
                        {modelType === 'random_forest' ? (
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                            padding: '4px 10px',
                            borderRadius: 6,
                            fontSize: 13,
                            fontWeight: 600,
                            background: s.dropout_probability >= 0.7
                              ? 'rgba(239, 68, 68, 0.15)'
                              : s.dropout_probability >= 0.4
                                ? 'rgba(245, 158, 11, 0.15)'
                                : 'rgba(34, 197, 94, 0.15)',
                            color: s.dropout_probability >= 0.7
                              ? 'var(--danger)'
                              : s.dropout_probability >= 0.4
                                ? 'var(--warning)'
                                : 'var(--success)',
                          }}>
                            {s.dropout_probability != null ? `${(s.dropout_probability * 100).toFixed(1)}%` : '—'}
                          </span>
                        ) : (
                          <span className={`badge ${s.risk_level === 'high' ? 'badge-danger' : s.risk_level === 'medium' ? 'badge-warning' : 'badge-success'}`}>
                            {s.risk_score} / 100
                          </span>
                        )}
                      </td>
                      <td style={{ fontSize: 13, color: 'var(--text-secondary)', maxWidth: 300 }}>
                        {s.reasons.length > 0 ? (
                          <ul style={{ paddingLeft: 16, margin: 0 }}>
                            {s.reasons.map((r, i) => <li key={i} style={{ color: s.risk_level === 'high' ? 'var(--danger)' : 'inherit' }}>{r}</li>)}
                          </ul>
                        ) : 'Học tập bình thường'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Tính năng E: Learning Style Clustering */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Users color="var(--primary)" />
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>Phân loại kiểu học sinh viên (Learning Styles)</h2>
            <span className="badge badge-purple" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 12, padding: '4px 10px', marginLeft: 8 }}>
              <Bot size={13} /> KMeans Clustering
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
            Hệ thống nhóm các sinh viên có chung thói quen học tập (như tốc độ xem, tua lùi, ghi chú) giúp giảng viên cá nhân hóa phương pháp dạy.
          </p>

          {learningStylesData?.error ? (
             <div style={{ padding: 20, textAlign: 'center', color: 'var(--warning)' }}>{learningStylesData.error}</div>
          ) : !learningStylesData?.clusters?.length ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có đủ dữ liệu để phân tích kiểu học.</div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
              {learningStylesData.clusters.map(c => (
                <div key={c.cluster_id} style={{ padding: 16, border: '1px solid var(--border)', borderRadius: 8, background: 'var(--bg-elevated)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                    <div style={{ fontSize: 24 }}>{c.icon}</div>
                    <span className="badge" style={{ background: 'var(--bg-surface)', border: '1px solid var(--border)' }}>{c.count} sinh viên</span>
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{c.style_name}</h3>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16, minHeight: 40 }}>{c.description}</p>
                  
                  {c.students.length > 0 && (
                    <div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 8, textTransform: 'uppercase' }}>Danh sách:</div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {c.students.map(s => (
                          <span key={s.student_id} style={{ fontSize: 12, padding: '2px 8px', background: 'var(--bg-surface)', borderRadius: 4, color: 'var(--text-primary)' }}>
                            {s.student_name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Tính năng 3: Video Difficulty Heatmap */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <Flame color="var(--warning)" />
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>Bản đồ điểm khó (Difficulty Heatmap)</h2>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 20 }}>
            Biểu đồ nhiệt cho biết sinh viên hay tua lại và dừng hình ở phút thứ mấy, giúp bạn cải thiện bài giảng.
          </p>

          <div style={{ marginBottom: 24, maxWidth: 420 }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              <Video size={14} /> Chọn video để phân tích
            </label>
            <div style={{ position: 'relative' }}>
              <Video size={16} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--accent)', pointerEvents: 'none' }} />
              <select
                value={selectedVideoId || ''}
                onChange={e => setSelectedVideoId(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 40px 12px 40px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                  fontSize: 14,
                  fontWeight: 500,
                  cursor: 'pointer',
                  appearance: 'none',
                  WebkitAppearance: 'none',
                  outline: 'none',
                  transition: 'border-color 0.2s, box-shadow 0.2s',
                }}
                onFocus={e => { e.currentTarget.style.borderColor = 'var(--accent)'; e.currentTarget.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.15)' }}
                onBlur={e => { e.currentTarget.style.borderColor = 'var(--border)'; e.currentTarget.style.boxShadow = 'none' }}
              >
                <option value="" disabled>— Chọn video —</option>
                {videos.map(v => (
                  <option key={v.video_id} value={v.video_id}>{v.order}. {v.title}</option>
                ))}
              </select>
              <ChevronDown size={16} style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', pointerEvents: 'none' }} />
            </div>
          </div>

          {!heatmapData?.full_heatmap?.length ? (
            <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)' }}>Chưa có đủ dữ liệu hành vi (tua lùi, tạm dừng) cho video này.</div>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: 4, height: 40, alignItems: 'flex-end', marginBottom: 12 }}>
                {heatmapData.full_heatmap.map(seg => {
                  const isHard = seg.difficulty_label === 'hard'
                  const isMed = seg.difficulty_label === 'medium'
                  return (
                    <div 
                      key={seg.segment_index} 
                      title={`Từ ${seg.start_seconds}s - ${seg.end_seconds}s | Lượt tua/dừng: ${seg.difficulty_count}`}
                      style={{
                        flex: 1,
                        height: `${Math.max(10, seg.intensity * 100)}%`,
                        background: isHard ? 'var(--danger)' : isMed ? 'var(--warning)' : 'var(--success)',
                        borderRadius: '4px 4px 0 0',
                        opacity: isHard ? 1 : 0.6,
                        transition: 'all 0.2s',
                        cursor: 'pointer'
                      }}
                    />
                  )
                })}
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)' }}>
                <span>00:00</span>
                <span>{(() => { const s = heatmapData.duration_seconds || 0; const m = Math.floor(s/60); const r = s%60; return `${String(m).padStart(2,'0')}:${String(r).padStart(2,'0')}` })()}</span>
              </div>

              {heatmapData.hardest_segments?.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <h4 style={{ fontSize: 14, marginBottom: 8 }}>🔥 Các đoạn khó hiểu nhất:</h4>
                  <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                    {heatmapData.hardest_segments.map(seg => (
                      <div key={seg.segment_index} style={{ padding: '8px 12px', background: 'var(--bg-elevated)', borderRadius: 6, border: '1px solid var(--danger)', fontSize: 13 }}>
                        <strong style={{ color: 'var(--danger)' }}>{seg.start_seconds}s - {seg.end_seconds}s</strong>
                        <div style={{ color: 'var(--text-secondary)' }}>Cường độ: {seg.intensity * 100}%</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

      </div>

      {/* Keyframes for spinner */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}

export const LEVEL_LABELS = {
  beginner: 'Cơ bản',
  intermediate: 'Trung cấp',
  advanced: 'Nâng cao',
}

export const LANGUAGE_LABELS = {
  vi: 'Tiếng Việt',
  en: 'English',
}

export const STATUS_LABELS = {
  published: 'Đã xuất bản',
  draft: 'Bản nháp',
  archived: 'Lưu trữ',
}

export const STATUS_BADGE = {
  published: 'badge-green',
  draft: 'badge-yellow',
  archived: 'badge-gray',
}

export const ENROLLMENT_STATUS_LABELS = {
  active: 'Đang học',
  completed: 'Hoàn thành',
  dropped: 'Đã bỏ',
}

export const ENROLLMENT_STATUS_BADGE = {
  active: 'badge-blue',
  completed: 'badge-green',
  dropped: 'badge-red',
}

export function getFieldError(error, field) {
  if (!error) return null
  return error[field]?.[0] || null
}

export function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('vi-VN')
}
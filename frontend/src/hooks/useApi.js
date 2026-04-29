import { useState, useCallback } from 'react'

export function useApi(apiFn) {
    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useError(null)

    const execute = useCallback(async (...args) => {
        setLoading(true)
        setError(null)
        try {
            const res = await apiFn(...args)
            setData(res.data)
            return res.data
        } catch (err) {
            const errData = err.response?.data || {detail: 'Đã xảy ra lỗi'}
            setError(errData)
            throw errData
        } finally {
            setLoading(false)
        }
    }, [apiFn])

    return { data, loading, error, execute }
}
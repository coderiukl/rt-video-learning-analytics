import React, { createContext, useContext, useState, useEffect } from "react";
import apiClient, { authApi } from "../api/client"

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [viewMode, setViewModeState] = useState(localStorage.getItem('view_mode') || null)
    const [loading, setLoading] = useState(true)

    const setViewMode = (mode) => {
        if (mode) {
            localStorage.setItem('view_mode', mode)
        } else {
            localStorage.removeItem('view_mode')
        }
        setViewModeState(mode)
    }

    useEffect(() => {
        const token = localStorage.getItem('access_token')
        if (token) {
            authApi.me()
            .then((res) => {
                setUser(res.data)
                if (!localStorage.getItem('view_mode')) {
                    setViewMode(res.data.role === 'instructor' ? 'instructor' : res.data.role)
                }
            })
            .catch(() => {
                localStorage.removeItem('access_token')
                localStorage.removeItem('refresh_token')
            })
            .finally(() => setLoading(false))
        } else {
            setLoading(false)
        }
    }, [])

    const login = async (email, password) => {
        const res = await authApi.login({ email, password })
        const { access, refresh } = res.data.tokens || res.data
        localStorage.setItem('access_token', access)
        localStorage.setItem('refresh_token', refresh)
        const meRes = await authApi.me()
        setUser(meRes.data)
        setViewMode(meRes.data.role === 'instructor' ? 'instructor' : meRes.data.role)
        return meRes.data
    }

    const register = async (data) => {
        const res = await authApi.register(data)
        return res.data
    }

    const logout = async () => {
        try {
            const refresh = localStorage.getItem('refresh_token')
            await authApi.logout({ refresh })
        } catch (_) {}
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('view_mode')
        setUser(null)
        setViewModeState(null)
    }

    const value = {user, loading, login, register, logout, setUser, viewMode, setViewMode}

    return <AuthContext.Provider value={value}> {children} </AuthContext.Provider>
}

export function useAuth() {
    const ctx = useContext(AuthContext)
    if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
        return ctx
}

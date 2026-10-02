/**
 * DataWise AI — WebSocket Hook
 *
 * Manages the persistent WebSocket connection to the backend
 * for real-time agent progress updates and chat messages.
 */

import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

export type WsStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export interface WsMessage {
  type: 'chat' | 'progress' | 'decision' | 'error' | 'artifact' | 'ping';
  payload: unknown;
}

interface UseWebSocketOptions {
  sessionId: string;
  onMessage?: (msg: WsMessage) => void;
  onStatusChange?: (status: WsStatus) => void;
  autoReconnect?: boolean;
  reconnectDelayMs?: number;
}

export function useWebSocket({
  sessionId,
  onMessage,
  onStatusChange,
  autoReconnect = true,
  reconnectDelayMs = 3000,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<WsStatus>('disconnected');
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const updateStatus = useCallback((s: WsStatus) => {
    setStatus(s);
    onStatusChange?.(s);
  }, [onStatusChange]);

  const connect = useCallback(() => {
    if (!sessionId) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const url = `${WS_BASE}/ws/sessions/${sessionId}`;
    updateStatus('connecting');

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (mountedRef.current) updateStatus('connected');
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        try {
          const data: WsMessage = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          console.warn('[WS] Could not parse message', event.data);
        }
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;
        updateStatus('disconnected');
        if (autoReconnect) {
          reconnectTimer.current = setTimeout(connect, reconnectDelayMs);
        }
      };

      ws.onerror = () => {
        if (!mountedRef.current) return;
        updateStatus('error');
      };
    } catch {
      updateStatus('error');
    }
  }, [sessionId, autoReconnect, reconnectDelayMs, onMessage, updateStatus]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    updateStatus('disconnected');
  }, [updateStatus]);

  const send = useCallback((msg: WsMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    } else {
      console.warn('[WS] Cannot send — not connected');
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [sessionId]);  // reconnect when session changes

  return { status, send, connect, disconnect };
}

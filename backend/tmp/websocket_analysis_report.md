# WebSocket Connection Analysis Report

## Issue Summary
The WebSocket shows as "connected" (isConnected = true) but has readyState 0 (CONNECTING), causing messages to queue indefinitely.

## Key Findings

### 1. Race Condition in Connection State Management

**Problem**: The `isConnected` flag is set to `true` in the `onopen` handler (line 67), but there's a potential race condition where:
- The connection status check happens before the WebSocket is fully established
- The `isConnected` flag doesn't accurately reflect the actual `socket.readyState`

**Code Location**: `websocketService.ts` lines 65-84
```typescript
this.socket.onopen = () => {
    console.log('WebSocket connected');
    this.isConnected = true;  // Flag set here
    this.reconnectAttempts = 0;
    this.reconnectDelay = 1000;
    
    // Send queued messages
    while (this.messageQueue.length > 0) {
        const message = this.messageQueue.shift();
        if (message) {
            this.sendMessage(message);  // This checks readyState, not isConnected
        }
    }
```

### 2. Inconsistent State Checking

**Problem**: The code uses two different methods to check connection status:
- `isConnected` flag (managed manually)
- `socket.readyState` (WebSocket's actual state)

**Evidence**:
- `getConnectionStatus()` returns `isConnected` (line 159)
- `sendMessage()` checks `socket?.readyState === WebSocket.OPEN` (line 219)
- This can lead to situations where `isConnected = true` but `readyState = 0`

### 3. Connection URL Construction Issues

**Problem**: The WebSocket URL construction might fail in certain environments:
```typescript
const wsHost = window.location.hostname === 'localhost' 
    ? 'localhost:8000' 
    : `${window.location.hostname}:8000`;
```

This assumes the backend is always on port 8000, which might not be true in all environments.

### 4. updateConfig Race Condition

**Critical Issue** at lines 165-179:
```typescript
updateConfig(config: Partial<CitationConfig>): void {
    const configChanged = /* ... */;
    this.config = { ...this.config, ...config };
    
    if (configChanged && this.isConnected) {
        console.log('[WebSocket] Configuration changed, reconnecting...');
        this.disconnect();  // Sets isConnected = false
        this.connect();     // Async operation
    }
}
```

**Problem**: 
- `disconnect()` is called synchronously
- `connect()` is called immediately after, but the connection is asynchronous
- This can lead to a state where the old connection is closing while the new one is opening

### 5. Message Queue Management

**Issue**: Messages can queue indefinitely if the connection never properly establishes:
- Queue limit is 10 messages (line 225)
- But if `readyState` never becomes `OPEN`, messages stay queued
- No timeout or retry mechanism for queued messages

### 6. Singleton Pattern Issues

**Problem** in `getCitationWebSocketClient()` (lines 358-367):
- The singleton might already have a connection in a bad state
- Calling `updateConfig` on an existing instance can trigger the race condition
- No way to force a fresh connection

## Root Cause Analysis

The most likely root cause is a combination of:

1. **Timing Issue**: The WebSocket connection is initiated but never completes the handshake
2. **State Mismatch**: The `isConnected` flag doesn't accurately represent the WebSocket state
3. **Configuration Updates**: Rapid configuration changes can leave the connection in a limbo state

## Recommended Fixes

### 1. Use Only socket.readyState
Replace the `isConnected` flag with a getter that checks the actual WebSocket state:
```typescript
get isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
}
```

### 2. Add Connection Timeout
Implement a timeout for connection attempts:
```typescript
connect(): void {
    // Set a timeout for connection
    const connectionTimeout = setTimeout(() => {
        if (this.socket?.readyState !== WebSocket.OPEN) {
            console.error('Connection timeout');
            this.socket?.close();
            this.handleReconnection();
        }
    }, 5000); // 5 second timeout
    
    // Clear timeout on successful connection
    this.socket.onopen = () => {
        clearTimeout(connectionTimeout);
        // ... rest of onopen logic
    };
}
```

### 3. Fix updateConfig Method
Add proper state management for configuration updates:
```typescript
async updateConfig(config: Partial<CitationConfig>): Promise<void> {
    const configChanged = /* ... */;
    this.config = { ...this.config, ...config };
    
    if (configChanged && this.socket?.readyState === WebSocket.OPEN) {
        // Properly close existing connection
        this.disconnect();
        // Wait a bit before reconnecting
        await new Promise(resolve => setTimeout(resolve, 100));
        this.connect();
    }
}
```

### 4. Add Connection Health Check
Implement a method to verify the connection is truly working:
```typescript
async verifyConnection(): Promise<boolean> {
    if (this.socket?.readyState !== WebSocket.OPEN) {
        return false;
    }
    
    // Send a ping and wait for pong
    return new Promise((resolve) => {
        const timeout = setTimeout(() => resolve(false), 3000);
        
        const originalHandler = this.handleMessage;
        this.handleMessage = (message) => {
            if (message.type === 'pong') {
                clearTimeout(timeout);
                this.handleMessage = originalHandler;
                resolve(true);
            } else {
                originalHandler.call(this, message);
            }
        };
        
        this.sendMessage({ type: 'ping' });
    });
}
```

### 5. Add Proper Error Recovery
Enhance error handling to detect and recover from bad states:
```typescript
private startHealthCheck(): void {
    setInterval(async () => {
        if (this.isConnected && !(await this.verifyConnection())) {
            console.error('Connection health check failed, reconnecting...');
            this.disconnect();
            this.connect();
        }
    }, 30000); // Check every 30 seconds
}
```

## Testing Recommendations

1. Run the debug script: `python tmp/debug_websocket.py`
2. Monitor browser console for WebSocket state changes
3. Test rapid configuration changes
4. Test network disconnection/reconnection scenarios
5. Verify message queuing behavior

## Immediate Action Items

1. Check if the backend WebSocket server is properly handling the handshake
2. Verify CORS settings for WebSocket connections
3. Check for any proxy or firewall issues blocking WebSocket upgrades
4. Monitor backend logs for connection attempts and errors
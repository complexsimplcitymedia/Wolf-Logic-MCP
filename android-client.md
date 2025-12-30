# Android Client - Wolf Logic MCP

## Overview
Android client for Wolf Logic MCP system. Provides mobile interface for text intake, memory queries, and local AI processing.

## Architecture

### Components
1. **Wolf-Logic-app/** - Full Android application
   - Backend: `backend.py` (FastAPI)
   - Control: `control_app.py` (Android UI controller)
   - UI: `wolf-ui/` (React Native / native Android)
   - Services: Systemd services for background processing

2. **wolflogic-apk/** - Compiled APK files
   - `base.apk` - Core application
   - `split_config.arm64_v8a.apk` - ARM64 architecture
   - Language packs: `en`, `es`
   - Display configs: `hdpi`, `xxhdpi`

3. **Mobile Scripts**
   - `mobile_wolf_gui.py` - Mobile GUI interface
   - `termux_gui_control.py` - Termux-based controls

## MCP Intake Integration

### Client → Server Flow
```
Android App
    ↓
MCP Intake API (OAuth)
Port: 8002
Endpoint: /intake/stream
    ↓
Server: 100.110.82.181
    ↓
/data/client-dumps/
    ↓
Swarm Processing
    ↓
pgai → Database
```

### Authentication
- **Provider:** Authentik (100.110.82.181:9001)
- **Method:** OAuth 2.0
- **Client ID:** mcp-intake
- **Scopes:** openid, profile, email

### API Endpoints

**Base URL:** `http://100.110.82.181:8002`

#### Submit Text Stream
```http
POST /intake/stream
Authorization: Bearer {oauth_token}
Content-Type: application/json

{
  "text": "Your text content here",
  "metadata": {
    "source": "android_app",
    "device": "Pixel 6",
    "version": "1.0.0"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Text stream accepted for processing",
  "data": {
    "file_id": "abc123",
    "username": "wolf",
    "text_length": 1234,
    "queue_file": "wolf_20251224_120000_abc123.json"
  },
  "timestamp": "2025-12-24T12:00:00"
}
```

### How to Stream to MCP Endpoint

#### Continuous Streaming (Real-time)
For apps that need to continuously send text (e.g., live transcription, note-taking):

**Option 1: Batch Submission (Recommended)**
```kotlin
class StreamManager(private val client: WolfMCPClient) {
    private val buffer = StringBuilder()
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var flushJob: Job? = null

    // Buffer text and flush every 5 seconds or 1000 chars
    fun streamText(text: String) {
        buffer.append(text)

        // Auto-flush if buffer gets large
        if (buffer.length > 1000) {
            flush()
        } else {
            // Schedule flush in 5 seconds
            flushJob?.cancel()
            flushJob = scope.launch {
                delay(5000)
                flush()
            }
        }
    }

    private fun flush() {
        if (buffer.isEmpty()) return

        val content = buffer.toString()
        buffer.clear()

        scope.launch {
            client.submitText(
                text = content,
                metadata = mapOf(
                    "source" to "stream",
                    "type" to "continuous",
                    "timestamp" to System.currentTimeMillis()
                )
            )
        }
    }

    fun stop() {
        flush() // Final flush
        flushJob?.cancel()
        scope.cancel()
    }
}
```

**Usage:**
```kotlin
val streamManager = StreamManager(mcpClient)

// As user types or speaks
editText.addTextChangedListener { text ->
    streamManager.streamText(text.toString())
}

// When done
streamManager.stop()
```

**Option 2: Server-Sent Events (SSE) for Bidirectional**
Coming soon - server will support SSE for real-time responses.

**Option 3: WebSocket Streaming (Future)**
For true bidirectional streaming, WebSocket support planned.

#### Background Streaming Service

For continuous background streaming (e.g., clipboard monitor, voice notes):

```kotlin
class MCPStreamService : Service() {
    private lateinit var client: WolfMCPClient
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        client = WolfMCPClient(oauthToken = getStoredToken())

        // Monitor clipboard
        scope.launch {
            monitorClipboard()
        }

        return START_STICKY
    }

    private suspend fun monitorClipboard() {
        val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager

        clipboard.addPrimaryClipChangedListener {
            val clip = clipboard.primaryClip
            if (clip != null && clip.itemCount > 0) {
                val text = clip.getItemAt(0).text.toString()

                // Stream to MCP
                scope.launch {
                    client.submitText(
                        text = text,
                        metadata = mapOf(
                            "source" to "clipboard",
                            "device" to Build.MODEL,
                            "timestamp" to System.currentTimeMillis()
                        )
                    )
                }
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
```

**AndroidManifest.xml:**
```xml
<service
    android:name=".MCPStreamService"
    android:enabled="true"
    android:exported="false" />
```

**Start service:**
```kotlin
val intent = Intent(this, MCPStreamService::class.java)
startForegroundService(intent)
```

#### Voice Streaming Example

```kotlin
class VoiceStreamer(
    private val client: WolfMCPClient,
    private val context: Context
) {
    private val speechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
    private val recognitionListener = object : RecognitionListener {
        override fun onResults(results: Bundle?) {
            val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            matches?.firstOrNull()?.let { text ->
                // Stream recognized text
                CoroutineScope(Dispatchers.IO).launch {
                    client.submitText(
                        text = text,
                        metadata = mapOf(
                            "source" to "voice",
                            "confidence" to (results.getFloatArray(SpeechRecognizer.CONFIDENCE_SCORES)?.firstOrNull() ?: 0f)
                        )
                    )
                }
            }
        }

        // Other callbacks...
        override fun onError(error: Int) {}
        override fun onReadyForSpeech(params: Bundle?) {}
        override fun onBeginningOfSpeech() {}
        override fun onRmsChanged(rmsdB: Float) {}
        override fun onBufferReceived(buffer: ByteArray?) {}
        override fun onEndOfSpeech() {}
        override fun onPartialResults(partialResults: Bundle?) {}
        override fun onEvent(eventType: Int, params: Bundle?) {}
    }

    fun startListening() {
        speechRecognizer.setRecognitionListener(recognitionListener)
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        speechRecognizer.startListening(intent)
    }

    fun stop() {
        speechRecognizer.stopListening()
        speechRecognizer.destroy()
    }
}
```

#### Rate Limiting Best Practices

The MCP endpoint can handle high throughput (4 workers), but implement client-side rate limiting:

```kotlin
class RateLimitedClient(private val client: WolfMCPClient) {
    private val rateLimiter = Semaphore(10) // Max 10 concurrent requests
    private val requestTimes = mutableListOf<Long>()

    suspend fun submitWithRateLimit(text: String, metadata: Map<String, Any>): Result<String> {
        // Check rate (max 100 requests per minute)
        synchronized(requestTimes) {
            val now = System.currentTimeMillis()
            requestTimes.removeAll { it < now - 60000 }
            if (requestTimes.size >= 100) {
                return Result.failure(Exception("Rate limit exceeded"))
            }
            requestTimes.add(now)
        }

        // Acquire semaphore
        rateLimiter.acquire()
        try {
            return client.submitText(text, metadata)
        } finally {
            rateLimiter.release()
        }
    }
}
```

#### Offline Queue with Auto-Sync

For unreliable networks:

```kotlin
class OfflineQueueManager(
    private val client: WolfMCPClient,
    private val context: Context
) {
    private val db = Room.databaseBuilder(
        context,
        QueueDatabase::class.java,
        "mcp-queue"
    ).build()

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    fun queueText(text: String, metadata: Map<String, Any>) {
        scope.launch {
            // Save to local database
            db.queueDao().insert(QueueItem(
                text = text,
                metadata = metadata,
                timestamp = System.currentTimeMillis(),
                synced = false
            ))

            // Try to sync immediately
            syncQueue()
        }
    }

    private suspend fun syncQueue() {
        if (!isNetworkAvailable()) return

        val unsynced = db.queueDao().getUnsynced()
        unsynced.forEach { item ->
            client.submitText(item.text, item.metadata).onSuccess {
                // Mark as synced
                db.queueDao().markSynced(item.id)
            }
        }
    }

    private fun isNetworkAvailable(): Boolean {
        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        return cm.activeNetwork != null
    }

    init {
        // Auto-sync when network becomes available
        val networkCallback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                scope.launch { syncQueue() }
            }
        }

        val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        cm.registerDefaultNetworkCallback(networkCallback)
    }
}
```

#### Get Queue Stats
```http
GET /intake/stats
Authorization: Bearer {oauth_token}
```

#### Health Check
```http
GET /health
```

## Installation

### Prerequisites
- Android 8.0+ (API 26+)
- ARM64 device
- Network access to 100.110.82.181 (Tailscale or VPN)

### Install APK
```bash
# Transfer to device
adb push wolflogic-apk/*.apk /sdcard/Download/

# Install via adb
adb install-multiple \
  wolflogic-apk/base.apk \
  wolflogic-apk/split_config.arm64_v8a.apk \
  wolflogic-apk/split_config.en.apk \
  wolflogic-apk/split_config.xxhdpi.apk
```

### Termux Setup (Optional)
For developers using Termux:

```bash
# Install dependencies
pkg install python git openssh

# Clone repo
git clone https://github.com/yourusername/Wolf-Logic-MCP
cd Wolf-Logic-MCP/android-client

# Run mobile GUI
python mobile_wolf_gui.py
```

## Configuration

### Server Connection
Edit `Wolf-Logic-app/backend.py`:

```python
SERVER_URL = "http://100.110.82.181:8002"
AUTHENTIK_URL = "http://100.110.82.181:9001"
CLIENT_ID = "mcp-intake"
CLIENT_SECRET = "your-secret-here"
```

### OAuth Setup
1. Open app
2. Tap "Login"
3. Authenticate via Authentik
4. Grant permissions
5. Save token

## Features

### Text Intake
- Type or paste text
- Attach metadata (tags, source, etc.)
- Submit to MCP server
- View submission status

### Memory Query
- Search memories by keyword
- Semantic search via qwen3-embedding
- Filter by namespace
- View results

### Local Processing (Future)
- On-device summarization (llama3.2:1b)
- Offline queue
- Sync when online

## API Client Example (Kotlin)

```kotlin
import okhttp3.*
import kotlinx.coroutines.*
import org.json.JSONObject

class WolfMCPClient(
    private val serverUrl: String = "http://100.110.82.181:8002",
    private val oauthToken: String
) {
    private val client = OkHttpClient()

    suspend fun submitText(text: String, metadata: Map<String, Any>): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val json = JSONObject()
                json.put("text", text)
                json.put("metadata", JSONObject(metadata))

                val body = RequestBody.create(
                    MediaType.parse("application/json"),
                    json.toString()
                )

                val request = Request.Builder()
                    .url("$serverUrl/intake/stream")
                    .header("Authorization", "Bearer $oauthToken")
                    .post(body)
                    .build()

                val response = client.newCall(request).execute()
                val responseBody = response.body()?.string()

                if (response.isSuccessful) {
                    Result.success(responseBody ?: "")
                } else {
                    Result.failure(Exception("HTTP ${response.code()}: $responseBody"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }

    suspend fun getStats(): Result<String> {
        return withContext(Dispatchers.IO) {
            try {
                val request = Request.Builder()
                    .url("$serverUrl/intake/stats")
                    .header("Authorization", "Bearer $oauthToken")
                    .get()
                    .build()

                val response = client.newCall(request).execute()
                val responseBody = response.body()?.string()

                if (response.isSuccessful) {
                    Result.success(responseBody ?: "")
                } else {
                    Result.failure(Exception("HTTP ${response.code()}: $responseBody"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
```

## Usage Example

```kotlin
val client = WolfMCPClient(oauthToken = "your-token-here")

// Submit text
lifecycleScope.launch {
    val result = client.submitText(
        text = "Fixed authentication bug in API",
        metadata = mapOf(
            "source" to "android_app",
            "device" to Build.MODEL,
            "version" to BuildConfig.VERSION_NAME
        )
    )

    result.onSuccess { response ->
        Log.d("MCP", "Submitted: $response")
        showToast("Text submitted successfully")
    }.onFailure { error ->
        Log.e("MCP", "Failed: ${error.message}")
        showToast("Submission failed")
    }
}
```

## Troubleshooting

### Cannot connect to server
1. Check Tailscale/VPN connection
2. Verify server IP: `ping 100.110.82.181`
3. Test endpoint: `curl http://100.110.82.181:8002/health`
4. Check firewall rules on server

### Authentication fails
1. Verify OAuth token not expired
2. Check client ID/secret in Authentik
3. Ensure app has correct redirect URI
4. Review Authentik logs

### APK installation fails
1. Enable "Unknown sources" in Android settings
2. Use `adb install-multiple` for split APKs
3. Uninstall old version first
4. Check device architecture (ARM64 required)

## Development

### Build from Source
```bash
cd android-client/Wolf-Logic-app

# Install dependencies
./install-apps.sh

# Build APK
./start-wolf.sh
```

### Run Backend Locally
```bash
# Activate environment
source ~/anaconda3/bin/activate messiah

# Run backend
python backend.py
```

### Debug via ADB
```bash
# View logs
adb logcat | grep WolfLogic

# Monitor network
adb shell tcpdump -i any -s0 -w - | wireshark -k -i -

# Debug layout
adb shell setprop debug.layout true
```

## Security

1. **OAuth tokens** stored in Android Keystore
2. **TLS required** for production (use Caddy)
3. **Certificate pinning** recommended
4. **No credentials** stored in plaintext
5. **Biometric unlock** for sensitive operations

## Roadmap

- [ ] Offline queue with sync
- [ ] On-device LLM (llama3.2:1b via Ollama Android)
- [ ] Voice input integration
- [ ] Multi-account support
- [ ] Widget for quick submit
- [ ] Wear OS companion app

## Support

- **Issues:** GitHub issues
- **Docs:** `/android-client/Wolf-Logic-app/README.md`
- **Server status:** http://100.110.82.181:8002/health

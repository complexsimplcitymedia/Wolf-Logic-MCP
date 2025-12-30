# Android Client - Memory Layer Integration

## Architecture Overview

Android clients are spokes in the Wolf Logic hub-and-spoke architecture. Your Android device:
- **SUBMITS data TO 100.110.82.181** (the hub)
- **Does NOT store memories locally** (no local PostgreSQL on Android)
- **Queries the hub through API** (when read access is needed)

This is different from desktop clients which maintain local PostgreSQL replicas. Android clients are thin by design.

## Data Flow

```
+-------------------+         +------------------------+
|  ANDROID DEVICE   |         |  100.110.82.181 (HUB)  |
|                   |         |  The Librarian         |
+-------------------+         +------------------------+
        |                              ^
        |  [1] Submit Text/Data        |
        +----------------------------->|
        |     POST /intake/stream      |
        |     (OAuth authenticated)    |
                                       |
                          +------------+------------+
                          |                         |
                          v                         v
                  +---------------+         +---------------+
                  | STAGING       |         | VECTORIZATION |
                  | /data/client- |         | qwen3:4b      |
                  | dumps/        |         | 2560 dims     |
                  +---------------+         +---------------+
                          |                         |
                          +------------+------------+
                                       |
                                       v
                          +------------------------+
                          | CANONICAL STORAGE      |
                          | wolf_logic @ 5433      |
                          | 97,000+ memories       |
                          +------------------------+
                                       |
        +------------------------------|
        |                              |
        v                              |
+-------------------+                  |
|  [2] Query API    |<-----------------+
|  (when needed)    |
+-------------------+
```

## Submission: Sending Data to the Hub

All data from your Android device flows TO the hub via the MCP Intake API.

### Endpoint

```
POST http://100.110.82.181:8002/intake/stream
Authorization: Bearer {oauth_token}
Content-Type: application/json
```

### Request Body

```json
{
  "text": "Your text content here",
  "metadata": {
    "source": "android_app",
    "device": "Pixel 6",
    "app_version": "1.0.0",
    "namespace_hint": "mobile_notes"
  }
}
```

### Response

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

### What Happens After Submission

1. Data lands in `/data/client-dumps/` on 181
2. Swarm processor picks it up (runs continuously)
3. Text is vectorized by qwen3-embedding:4b (2560 dimensions)
4. Memory is inserted into `wolf_logic.memories` table
5. Memory is now queryable by any client

**Latency:** Typically under 30 seconds from submission to searchable.

## Android-Specific Implementation

### Kotlin Client

```kotlin
import okhttp3.*
import kotlinx.coroutines.*
import org.json.JSONObject

class WolfMCPClient(
    private val serverUrl: String = "http://100.110.82.181:8002",
    private val oauthToken: String
) {
    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    suspend fun submitText(
        text: String,
        metadata: Map<String, Any> = emptyMap()
    ): Result<SubmissionResponse> = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("text", text)
                put("metadata", JSONObject(metadata.toMutableMap().apply {
                    put("source", "android_app")
                    put("device", android.os.Build.MODEL)
                    put("timestamp", System.currentTimeMillis())
                }))
            }

            val body = json.toString().toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url("$serverUrl/intake/stream")
                .header("Authorization", "Bearer $oauthToken")
                .post(body)
                .build()

            val response = client.newCall(request).execute()
            val responseBody = response.body?.string()

            if (response.isSuccessful && responseBody != null) {
                val jsonResponse = JSONObject(responseBody)
                Result.success(SubmissionResponse(
                    success = jsonResponse.getBoolean("success"),
                    fileId = jsonResponse.getJSONObject("data").getString("file_id"),
                    message = jsonResponse.getString("message")
                ))
            } else {
                Result.failure(Exception("HTTP ${response.code}: $responseBody"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

data class SubmissionResponse(
    val success: Boolean,
    val fileId: String,
    val message: String
)
```

### Usage Example

```kotlin
class MainActivity : AppCompatActivity() {
    private lateinit var mcpClient: WolfMCPClient

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize client with OAuth token
        mcpClient = WolfMCPClient(oauthToken = getStoredOAuthToken())

        // Submit button click
        submitButton.setOnClickListener {
            val text = editText.text.toString()
            if (text.isNotEmpty()) {
                submitToMemory(text)
            }
        }
    }

    private fun submitToMemory(text: String) {
        lifecycleScope.launch {
            val result = mcpClient.submitText(
                text = text,
                metadata = mapOf(
                    "context" to "manual_note",
                    "app_screen" to "main"
                )
            )

            result.onSuccess { response ->
                showToast("Submitted: ${response.fileId}")
                editText.text.clear()
            }.onFailure { error ->
                showToast("Failed: ${error.message}")
            }
        }
    }
}
```

## Offline Queue

Android devices are not always connected. Implement an offline queue.

### Room Database Schema

```kotlin
@Entity(tableName = "pending_submissions")
data class PendingSubmission(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val text: String,
    val metadataJson: String,
    val createdAt: Long = System.currentTimeMillis(),
    val attempts: Int = 0,
    val lastAttempt: Long? = null
)

@Dao
interface SubmissionDao {
    @Query("SELECT * FROM pending_submissions ORDER BY createdAt ASC")
    suspend fun getPending(): List<PendingSubmission>

    @Insert
    suspend fun insert(submission: PendingSubmission): Long

    @Delete
    suspend fun delete(submission: PendingSubmission)

    @Query("UPDATE pending_submissions SET attempts = attempts + 1, lastAttempt = :timestamp WHERE id = :id")
    suspend fun markAttempt(id: Long, timestamp: Long)
}
```

### Sync Worker

```kotlin
class SyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val db = AppDatabase.getInstance(applicationContext)
        val client = WolfMCPClient(oauthToken = getStoredToken())

        val pending = db.submissionDao().getPending()

        for (submission in pending) {
            val result = client.submitText(
                text = submission.text,
                metadata = JSONObject(submission.metadataJson).toMap()
            )

            if (result.isSuccess) {
                db.submissionDao().delete(submission)
            } else {
                db.submissionDao().markAttempt(submission.id, System.currentTimeMillis())
            }
        }

        return Result.success()
    }
}
```

### Schedule Sync

```kotlin
// In Application.onCreate() or MainActivity
val syncRequest = PeriodicWorkRequestBuilder<SyncWorker>(
    15, TimeUnit.MINUTES
).setConstraints(
    Constraints.Builder()
        .setRequiredNetworkType(NetworkType.CONNECTED)
        .build()
).build()

WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "wolf_sync",
    ExistingPeriodicWorkPolicy.KEEP,
    syncRequest
)
```

## Network Requirements

### Tailscale

Android clients must connect to Wolf Logic network via Tailscale.

1. Install Tailscale from Play Store
2. Sign in with Wolf Logic Tailscale account
3. Ensure 100.110.82.181 is reachable: `ping 100.110.82.181`

### Firewall Ports

| Port | Service | Direction |
|------|---------|-----------|
| 8002 | MCP Intake API | Android -> 181 |
| 9001 | Authentik OAuth | Android -> 181 |

## OAuth Authentication

### Authentik Configuration

- **Provider URL:** `http://100.110.82.181:9001`
- **Client ID:** `mcp-intake`
- **Scopes:** `openid profile email`
- **Redirect URI:** `wolflogic://oauth/callback`

### Android OAuth Flow

```kotlin
class OAuthManager(private val context: Context) {
    private val authServiceConfig = AuthorizationServiceConfiguration(
        Uri.parse("http://100.110.82.181:9001/application/o/authorize/"),
        Uri.parse("http://100.110.82.181:9001/application/o/token/")
    )

    fun startLogin(activity: Activity) {
        val authRequest = AuthorizationRequest.Builder(
            authServiceConfig,
            "mcp-intake",
            ResponseTypeValues.CODE,
            Uri.parse("wolflogic://oauth/callback")
        ).setScopes("openid", "profile", "email")
         .build()

        val authService = AuthorizationService(context)
        val authIntent = authService.getAuthorizationRequestIntent(authRequest)
        activity.startActivityForResult(authIntent, REQUEST_CODE_AUTH)
    }

    fun handleAuthResponse(intent: Intent, callback: (String?) -> Unit) {
        val response = AuthorizationResponse.fromIntent(intent)
        val exception = AuthorizationException.fromIntent(intent)

        if (response != null) {
            val authService = AuthorizationService(context)
            authService.performTokenRequest(response.createTokenExchangeRequest()) { tokenResponse, _ ->
                callback(tokenResponse?.accessToken)
            }
        } else {
            callback(null)
        }
    }

    companion object {
        const val REQUEST_CODE_AUTH = 1001
    }
}
```

## Best Practices

### 1. Buffer Before Sending

Don't send every keystroke. Buffer and batch.

```kotlin
class TextBuffer(private val client: WolfMCPClient) {
    private val buffer = StringBuilder()
    private var flushJob: Job? = null
    private val scope = CoroutineScope(Dispatchers.IO)

    fun append(text: String) {
        buffer.append(text)

        // Flush if buffer is large
        if (buffer.length > 500) {
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
            client.submitText(content, mapOf("type" to "buffered"))
        }
    }
}
```

### 2. Handle Network State

```kotlin
fun isNetworkAvailable(context: Context): Boolean {
    val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
    return cm.activeNetwork != null
}

suspend fun submitWithRetry(
    client: WolfMCPClient,
    text: String,
    maxRetries: Int = 3
): Result<SubmissionResponse> {
    repeat(maxRetries) { attempt ->
        val result = client.submitText(text)
        if (result.isSuccess) return result

        delay((attempt + 1) * 1000L) // Exponential backoff
    }
    return Result.failure(Exception("Max retries exceeded"))
}
```

### 3. Respect Battery

Use WorkManager constraints:

```kotlin
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.CONNECTED)
    .setRequiresBatteryNotLow(true)
    .build()
```

## What Android Clients Do NOT Do

1. **No local PostgreSQL** - Too heavy for mobile
2. **No local vectorization** - No GPU, too slow
3. **No direct DB queries** - Use API, not raw SQL
4. **No sync scripts** - No local replica to sync

Android clients are thin. They submit data and optionally query through API. All heavy lifting happens on 181.

## Troubleshooting

### Cannot connect to 100.110.82.181

1. Check Tailscale is connected: `tailscale status`
2. Check VPN is active in Android settings
3. Try: `adb shell ping 100.110.82.181`

### OAuth fails

1. Verify Authentik is running on 181:9001
2. Check client ID matches: `mcp-intake`
3. Verify redirect URI is registered

### Submissions disappear

1. Check `/data/client-dumps/` on 181 for your files
2. Check swarm processor logs
3. Verify submission response includes `file_id`

### App crashes on submit

1. Check OkHttp is on IO dispatcher (not Main)
2. Verify JSON is valid before sending
3. Check OAuth token isn't expired

package ai.bolsamajh.app

import android.Manifest
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import okhttp3.*
import okio.ByteString.Companion.toByteString
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class MainActivity : AppCompatActivity() {

    private lateinit var etServerIp: EditText
    private lateinit var btnConnect: Button
    private lateinit var btnStartCall: Button
    private lateinit var btnInterrupt: Button
    private lateinit var tvStatus: TextView
    private lateinit var tvTranscript: TextView

    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var isRecording = false
    private var audioRecord: AudioRecord? = null
    private var recordingThread: Thread? = null
    private var activeGenId: String? = null

    companion object {
        private const val PERMISSION_RECORD_AUDIO = 101
        private const val SAMPLE_RATE = 16000
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        etServerIp = findViewById(R.id.etServerIp)
        btnConnect = findViewById(R.id.btnConnect)
        btnStartCall = findViewById(R.id.btnStartCall)
        btnInterrupt = findViewById(R.id.btnInterrupt)
        tvStatus = findViewById(R.id.tvStatus)
        tvTranscript = findViewById(R.id.tvTranscript)

        btnConnect.setOnClickListener {
            val ip = etServerIp.text.toString().trim()
            if (ip.isNotEmpty()) {
                connectToCore(ip)
            } else {
                Toast.makeText(this, "Please enter your PC IP address", Toast.LENGTH_SHORT).show()
            }
        }

        btnStartCall.setOnClickListener {
            if (checkAudioPermission()) {
                startAudioStreaming()
            }
        }

        btnInterrupt.setOnClickListener {
            sendBargeIn()
        }
    }

    private fun checkAudioPermission(): Boolean {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
            != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                this,
                arrayOf(Manifest.permission.RECORD_AUDIO),
                PERMISSION_RECORD_AUDIO
            )
            return false
        }
        return true
    }

    private fun connectToCore(hostPort: String) {
        val cleanHost = hostPort.removePrefix("http://").removePrefix("https://").removePrefix("ws://")
        val wsUrl = "ws://$cleanHost/ws/call?lang=hinglish"

        tvStatus.text = "Connecting to $wsUrl..."
        val request = Request.Builder().url(wsUrl).build()

        webSocket?.close(1000, "Reconnecting")
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                runOnUiThread {
                    tvStatus.text = "Connected to $cleanHost ✓"
                    Toast.makeText(this@MainActivity, "Connected to BolSamajh Core", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val json = JSONObject(text)
                    when (json.optString("type")) {
                        "transcript" -> {
                            val userText = json.optString("text")
                            runOnUiThread {
                                tvTranscript.append("\n\nYou: $userText\n")
                            }
                        }
                        "answer" -> {
                            val answerText = json.optString("text")
                            val citations = json.optJSONArray("citations")
                            activeGenId = json.optString("generation_id")
                            runOnUiThread {
                                tvTranscript.append("\nBolSamajh: $answerText\n")
                                if (citations != null && citations.length() > 0) {
                                    val cits = (0 until citations.length()).joinToString(", ") { citations.getString(it) }
                                    tvTranscript.append("  [Citations: $cits]\n")
                                }
                            }
                        }
                        "state" -> {
                            val state = json.optString("state")
                            runOnUiThread {
                                tvStatus.text = "State: $state"
                            }
                        }
                    }
                } catch (e: Exception) {
                    e.printStackTrace()
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                runOnUiThread {
                    tvStatus.text = "Connection failed: ${t.message}"
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                runOnUiThread {
                    tvStatus.text = "Disconnected"
                }
            }
        })
    }

    private fun startAudioStreaming() {
        if (webSocket == null) {
            Toast.makeText(this, "Connect to PC core first", Toast.LENGTH_SHORT).show()
            return
        }
        if (isRecording) {
            stopAudioStreaming()
            btnStartCall.text = getString(R.string.btn_start_call)
            return
        }

        try {
            val minBuf = AudioRecord.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )
            audioRecord = AudioRecord(
                MediaRecorder.AudioSource.MIC,
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                minBuf * 2
            )

            audioRecord?.startRecording()
            isRecording = true
            btnStartCall.text = getString(R.string.btn_end_call)
            webSocket?.send(JSONObject().put("type", "speech_start").toString())

            recordingThread = Thread {
                val buffer = ByteArray(2048)
                while (isRecording && audioRecord != null) {
                    val read = audioRecord!!.read(buffer, 0, buffer.size)
                    if (read > 0) {
                        webSocket?.send(buffer.copyOf(read).toByteString())
                    }
                }
            }
            recordingThread?.start()
        } catch (e: Exception) {
            Toast.makeText(this, "Mic error: ${e.message}", Toast.LENGTH_SHORT).show()
        }
    }

    private fun stopAudioStreaming() {
        isRecording = false
        try {
            audioRecord?.stop()
            audioRecord?.release()
            audioRecord = null
            recordingThread = null
            webSocket?.send(JSONObject().put("type", "speech_end").toString())
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun sendBargeIn() {
        webSocket?.send(
            JSONObject()
                .put("type", "barge_in")
                .put("generation_id", activeGenId ?: "")
                .toString()
        )
        Toast.makeText(this, "Interrupted playback", Toast.LENGTH_SHORT).show()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopAudioStreaming()
        webSocket?.close(1000, "App closed")
    }
}


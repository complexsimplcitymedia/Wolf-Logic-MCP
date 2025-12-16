import React, { useState, useRef, useEffect } from 'react';
import { StyleSheet, Text, View, Image, TouchableOpacity, ScrollView, StatusBar, Dimensions } from 'react-native';
import { Video, ResizeMode, AVPlaybackStatus } from 'expo-av';
import { LinearGradient } from 'expo-linear-gradient';
import { Activity, Cpu, Zap, Terminal, Server, Shield, Power } from 'lucide-react-native';

// --- CONFIGURATION ---
const THEME = {
  background: '#050505',
  cardBg: '#111111',
  accent: '#333333',
  highlight: '#ffffff',
  text: '#e0e0e0',
  textDim: '#666666',
  danger: '#ff3333',
  success: '#00ff66',
};

// --- TYPES ---
interface LogEntry {
  id: string;
  time: string;
  source: string;
  message: string;
}

// --- MOCK DATA (Connecting to Reality Soon) ---
const INITIAL_LOGS: LogEntry[] = [
  { id: '1', time: '14:02:22', source: 'SYS', message: 'Bridge connection established.' },
  { id: '2', time: '14:02:21', source: 'NET', message: 'Tailscale link active: 100.110.82.181' },
  { id: '3', time: '14:02:20', source: 'SEC', message: 'Auth token verified. Welcome, Wolf.' },
];

export default function App() {
  const [booted, setBooted] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>(INITIAL_LOGS);
  
  // If not booted, show the intro video
  if (!booted) {
    return <BootSequence onComplete={() => setBooted(true)} />;
  }

  return <MainInterface logs={logs} />;
}

// --- BOOT SEQUENCE COMPONENT ---
function BootSequence({ onComplete }: { onComplete: () => void }) {
  const videoRef = useRef<Video>(null);

  const handlePlaybackStatusUpdate = (status: AVPlaybackStatus) => {
    if (status.isLoaded && status.didJustFinish) {
      onComplete();
    }
  };

  return (
    <View style={styles.bootContainer}>
      <StatusBar hidden />
      <Video
        ref={videoRef}
        style={styles.video}
        source={require('./assets/video/boot.mp4')}
        useNativeControls={false}
        resizeMode={ResizeMode.COVER}
        isLooping={false}
        shouldPlay={true}
        onPlaybackStatusUpdate={handlePlaybackStatusUpdate}
      />
    </View>
  );
}

// --- MAIN DASHBOARD COMPONENT ---
function MainInterface({ logs }: { logs: LogEntry[] }) {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={THEME.background} />
      
      {/* HEADER */}
      <View style={styles.header}>
        <Image 
          source={require('./assets/images/wolf_logo.png')} 
          style={styles.logo} 
          resizeMode="contain"
        />
        <View>
          <Text style={styles.headerTitle}>WOLF BRIDGE</Text>
          <Text style={styles.headerSubtitle}>OPERATIONAL // V1.0</Text>
        </View>
        <View style={styles.statusIndicator} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        
        {/* TELEMETRY GRID */}
        <Text style={styles.sectionTitle}>// TELEMETRY</Text>
        <View style={styles.grid}>
          <MetricCard title="VRAM" value="21.4 GB" icon={<Cpu color={THEME.text} size={20} />} label="RX 7900 XT" />
          <MetricCard title="LOAD" value="12%" icon={<Activity color={THEME.text} size={20} />} label="SYSTEM" />
          <MetricCard title="MEMORIES" value="10,441" icon={<Server color={THEME.text} size={20} />} label="VECTOR DB" />
          <MetricCard title="PWR" value="STABLE" icon={<Zap color={THEME.success} size={20} />} label="GRID" />
        </View>

        {/* CONTROLS */}
        <Text style={styles.sectionTitle}>// COMMAND DECK</Text>
        <View style={styles.controlRow}>
          <ControlSwitch label="OLLAMA" active={true} />
          <ControlSwitch label="SCRIPTY" active={true} />
          <ControlSwitch label="SHIELD" active={false} warning />
        </View>

        {/* NEURAL LINK / LOGS */}
        <Text style={styles.sectionTitle}>// NEURAL LINK</Text>
        <View style={styles.logContainer}>
          {logs.map((log) => (
            <View key={log.id} style={styles.logRow}>
              <Text style={styles.logTime}>[{log.time}]</Text>
              <Text style={styles.logSource}>{log.source} ::</Text>
              <Text style={styles.logMessage}>{log.message}</Text>
            </View>
          ))}
          <View style={styles.cursorBlock} />
        </View>

      </ScrollView>
    </View>
  );
}

// --- UI COMPONENTS ---

function MetricCard({ title, value, icon, label }: { title: string, value: string, icon: any, label: string }) {
  return (
    <LinearGradient colors={[THEME.cardBg, '#1a1a1a']} style={styles.card}>
      <View style={styles.cardHeader}>
        {icon}
        <Text style={styles.cardTitle}>{title}</Text>
      </View>
      <Text style={styles.cardValue}>{value}</Text>
      <Text style={styles.cardLabel}>{label}</Text>
    </LinearGradient>
  );
}

function ControlSwitch({ label, active, warning }: { label: string, active: boolean, warning?: boolean }) {
  return (
    <TouchableOpacity activeOpacity={0.7} style={[styles.controlButton, active ? styles.controlActive : styles.controlInactive, warning && styles.controlWarning]}>
       <Power size={24} color={active ? '#000' : (warning ? THEME.danger : THEME.textDim)} />
       <Text style={[styles.controlLabel, { color: active ? '#000' : (warning ? THEME.danger : THEME.textDim) }]}>{label}</Text>
    </TouchableOpacity>
  );
}

// --- STYLES ---
const { width, height } = Dimensions.get('window');

const styles = StyleSheet.create({
  bootContainer: {
    flex: 1,
    backgroundColor: '#000',
  },
  video: {
    width: width,
    height: height,
  },
  container: {
    flex: 1,
    backgroundColor: THEME.background,
    paddingTop: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: THEME.accent,
  },
  logo: {
    width: 50,
    height: 50,
    marginRight: 15,
  },
  headerTitle: {
    color: THEME.highlight,
    fontSize: 20,
    fontWeight: '900',
    letterSpacing: 1,
  },
  headerSubtitle: {
    color: THEME.textDim,
    fontSize: 12,
    letterSpacing: 2,
    marginTop: 2,
  },
  statusIndicator: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: THEME.success,
    marginLeft: 'auto',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  sectionTitle: {
    color: THEME.textDim,
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 10,
    marginTop: 10,
    letterSpacing: 1.5,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  card: {
    width: '48%',
    backgroundColor: THEME.cardBg,
    borderRadius: 4,
    padding: 15,
    marginBottom: 15,
    borderWidth: 1,
    borderColor: THEME.accent,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardTitle: {
    color: THEME.textDim,
    fontSize: 12,
    marginLeft: 8,
    fontWeight: '700',
  },
  cardValue: {
    color: THEME.highlight,
    fontSize: 22,
    fontWeight: '700',
  },
  cardLabel: {
    color: THEME.textDim,
    fontSize: 10,
    marginTop: 5,
  },
  controlRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 30,
  },
  controlButton: {
    width: '31%',
    aspectRatio: 1,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: THEME.accent,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: THEME.cardBg,
  },
  controlActive: {
    backgroundColor: THEME.highlight,
    borderColor: THEME.highlight,
  },
  controlInactive: {
    backgroundColor: 'transparent',
  },
  controlWarning: {
    borderColor: THEME.danger,
  },
  controlLabel: {
    fontSize: 10,
    fontWeight: '900',
    marginTop: 8,
    letterSpacing: 1,
  },
  logContainer: {
    backgroundColor: '#000',
    padding: 15,
    borderRadius: 4,
    borderLeftWidth: 2,
    borderLeftColor: THEME.textDim,
    minHeight: 150,
  },
  logRow: {
    flexDirection: 'row',
    marginBottom: 5,
    flexWrap: 'wrap',
  },
  logTime: {
    color: THEME.textDim,
    fontFamily: 'monospace',
    fontSize: 10,
    marginRight: 8,
  },
  logSource: {
    color: THEME.success,
    fontFamily: 'monospace',
    fontSize: 10,
    marginRight: 8,
    fontWeight: '700',
  },
  logMessage: {
    color: THEME.text,
    fontFamily: 'monospace',
    fontSize: 10,
  },
  cursorBlock: {
    width: 8,
    height: 14,
    backgroundColor: THEME.success,
    marginTop: 5,
  }
});
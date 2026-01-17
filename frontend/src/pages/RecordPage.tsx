import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, Mic, Square, Upload, AlertCircle } from 'lucide-react';
import { Student, studentsApi, lessonsApi } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';

export default function RecordPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();
  const [student, setStudent] = useState<Student | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (studentId) {
      loadStudent();
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [studentId]);

  const loadStudent = async () => {
    try {
      const { data } = await studentsApi.get(studentId!);
      setStudent(data);
    } catch (err) {
      console.error('Failed to load student', err);
      navigate('/');
    } finally {
      setIsLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      setRecordingTime(0);
      setError('');

      // Start timer
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError('Failed to access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioBlob(file);
      setError('');
    }
  };

  const uploadAndProcess = async () => {
    if (!audioBlob || !studentId) return;

    setIsUploading(true);
    setError('');

    try {
      // Create lesson
      const lessonRes = await lessonsApi.create({ student_id: studentId });
      const lessonId = lessonRes.data.id;

      // Upload audio
      const file = new File([audioBlob], 'recording.webm', { type: audioBlob.type });
      await lessonsApi.upload(lessonId, file);

      // Navigate to lesson page
      navigate(`/lessons/${lessonId}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload. Please try again.');
      setIsUploading(false);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-brand"></div>
      </div>
    );
  }

  if (!student) return null;

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      {/* Back Button */}
      <Link
        to={`/students/${studentId}`}
        className="inline-flex items-center text-dark-text-secondary hover:text-dark-text-primary transition-colors"
      >
        <ChevronLeft size={20} />
        <span>Back to {student.full_name}</span>
      </Link>

      {/* Recording Card */}
      <Card className="p-8">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-dark-text-primary mb-2">
            Record Lesson
          </h1>
          <p className="text-dark-text-secondary mb-8">
            Recording for {student.full_name} ({student.instrument})
          </p>

          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-3 text-red-400">
              <AlertCircle size={20} />
              <span>{error}</span>
            </div>
          )}

          {/* Recording Button */}
          {!audioBlob ? (
            <>
              <div className="relative inline-block mb-6">
                {isRecording && (
                  <div className="absolute inset-0 rounded-full bg-red-500/30 animate-pulse-ring"></div>
                )}
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`relative w-32 h-32 rounded-full flex items-center justify-center transition-all ${
                    isRecording
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-brand hover:bg-brand-dark'
                  }`}
                >
                  {isRecording ? (
                    <Square size={40} className="text-white" fill="white" />
                  ) : (
                    <Mic size={40} className="text-white" />
                  )}
                </button>
              </div>

              {/* Timer */}
              <p className="text-4xl font-mono text-dark-text-primary mb-4">
                {formatTime(recordingTime)}
              </p>

              <p className="text-dark-text-secondary text-sm mb-8">
                {isRecording ? 'Recording... Click to stop' : 'Click to start recording'}
              </p>

              {/* File Upload Option */}
              {!isRecording && (
                <div className="border-t border-dark-border pt-6">
                  <p className="text-dark-text-secondary text-sm mb-3">
                    Or upload an existing audio file
                  </p>
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept="audio/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <span className="inline-flex items-center gap-2 px-4 py-2 border border-dark-border rounded-lg text-dark-text-secondary hover:text-dark-text-primary hover:border-brand transition-colors">
                      <Upload size={18} />
                      Upload Audio
                    </span>
                  </label>
                </div>
              )}
            </>
          ) : (
            <>
              {/* Audio Preview */}
              <div className="mb-6">
                <audio
                  src={URL.createObjectURL(audioBlob)}
                  controls
                  className="w-full"
                />
              </div>

              <p className="text-dark-text-secondary text-sm mb-6">
                Recording duration: {formatTime(recordingTime)}
              </p>

              <div className="flex justify-center gap-4">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setAudioBlob(null);
                    setRecordingTime(0);
                  }}
                >
                  Record Again
                </Button>
                <Button
                  onClick={uploadAndProcess}
                  isLoading={isUploading}
                >
                  <Upload size={18} className="mr-2" />
                  Upload & Process
                </Button>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}

import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, AlertCircle, RefreshCw } from 'lucide-react';
import { LessonDetail, Output, lessonsApi } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';
import OutputCard from '../components/OutputCard';

const PROCESSING_STATUSES = ['UPLOADED', 'TRANSCRIBING', 'EXTRACTING', 'GENERATING'];

export default function LessonPage() {
  const { lessonId } = useParams<{ lessonId: string }>();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRetrying, setIsRetrying] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    if (lessonId) {
      loadLesson();
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [lessonId]);

  const loadLesson = async () => {
    try {
      const { data } = await lessonsApi.get(lessonId!);
      setLesson(data);

      // Start polling if processing
      if (PROCESSING_STATUSES.includes(data.status)) {
        startPolling();
      }
    } catch (err) {
      console.error('Failed to load lesson', err);
      navigate('/');
    } finally {
      setIsLoading(false);
    }
  };

  const startPolling = () => {
    if (pollRef.current) clearInterval(pollRef.current);

    pollRef.current = window.setInterval(async () => {
      try {
        const { data } = await lessonsApi.get(lessonId!);
        setLesson(data);

        if (!PROCESSING_STATUSES.includes(data.status)) {
          if (pollRef.current) {
            clearInterval(pollRef.current);
            pollRef.current = null;
          }
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 2000);
  };

  const handleRetry = async () => {
    setIsRetrying(true);
    try {
      await lessonsApi.process(lessonId!);
      await loadLesson();
      startPolling();
    } catch (err) {
      console.error('Retry failed', err);
    } finally {
      setIsRetrying(false);
    }
  };

  const handleOutputUpdate = (updated: Output) => {
    if (lesson) {
      setLesson({
        ...lesson,
        outputs: lesson.outputs.map((o) => (o.id === updated.id ? updated : o)),
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-brand"></div>
      </div>
    );
  }

  if (!lesson) return null;

  const isProcessing = PROCESSING_STATUSES.includes(lesson.status);
  const isFailed = lesson.status === 'FAILED';
  const isCompleted = lesson.status === 'COMPLETED';

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back Button */}
      <Link
        to={`/students/${lesson.student_id}`}
        className="inline-flex items-center text-dark-text-secondary hover:text-dark-text-primary transition-colors"
      >
        <ChevronLeft size={20} />
        <span>Back to {lesson.student_name}</span>
      </Link>

      {/* Lesson Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary">
              Lesson with {lesson.student_name}
            </h1>
            <p className="text-dark-text-secondary mt-1">
              {new Date(lesson.lesson_date).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>
          <StatusBadge status={lesson.status} />
        </div>
      </Card>

      {/* Processing State */}
      {isProcessing && (
        <Card className="p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-brand mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-dark-text-primary mb-2">
            Processing Your Lesson
          </h2>
          <p className="text-dark-text-secondary">
            {lesson.status === 'UPLOADED' && 'Preparing to transcribe...'}
            {lesson.status === 'TRANSCRIBING' && 'Transcribing audio...'}
            {lesson.status === 'EXTRACTING' && 'Analyzing lesson content...'}
            {lesson.status === 'GENERATING' && 'Generating outputs...'}
          </p>
          <p className="text-dark-text-secondary text-sm mt-4">
            This usually takes less than 60 seconds
          </p>
        </Card>
      )}

      {/* Failed State */}
      {isFailed && (
        <Card className="p-8 text-center">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-dark-text-primary mb-2">
            Processing Failed
          </h2>
          <p className="text-dark-text-secondary mb-4">
            {lesson.error_message || 'Something went wrong while processing your lesson.'}
          </p>
          <Button onClick={handleRetry} isLoading={isRetrying}>
            <RefreshCw size={18} className="mr-2" />
            Retry Processing
          </Button>
        </Card>
      )}

      {/* Outputs */}
      {isCompleted && lesson.outputs.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-dark-text-primary">Generated Outputs</h2>
          {lesson.outputs.map((output) => (
            <OutputCard
              key={output.id}
              output={output}
              onUpdate={handleOutputUpdate}
            />
          ))}
        </div>
      )}

      {/* Transcript (collapsed by default) */}
      {isCompleted && lesson.transcript && (
        <details className="group">
          <summary className="cursor-pointer text-dark-text-secondary hover:text-dark-text-primary transition-colors">
            View Original Transcript
          </summary>
          <Card className="mt-2 p-4">
            <pre className="whitespace-pre-wrap text-sm text-dark-text-secondary font-mono">
              {lesson.transcript}
            </pre>
          </Card>
        </details>
      )}
    </div>
  );
}

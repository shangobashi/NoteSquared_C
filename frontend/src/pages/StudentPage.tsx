import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ChevronLeft, Mic, Music, Calendar, ChevronRight } from 'lucide-react';
import { Student, studentsApi, Lesson, lessonsApi } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';

export default function StudentPage() {
  const { studentId } = useParams<{ studentId: string }>();
  const navigate = useNavigate();
  const [student, setStudent] = useState<Student | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (studentId) {
      loadData();
    }
  }, [studentId]);

  const loadData = async () => {
    try {
      const [studentRes, lessonsRes] = await Promise.all([
        studentsApi.get(studentId!),
        lessonsApi.list(studentId),
      ]);
      setStudent(studentRes.data);
      setLessons(lessonsRes.data);
    } catch (err) {
      console.error('Failed to load data', err);
      navigate('/');
    } finally {
      setIsLoading(false);
    }
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
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to="/"
        className="inline-flex items-center text-dark-text-secondary hover:text-dark-text-primary transition-colors"
      >
        <ChevronLeft size={20} />
        <span>Back to Students</span>
      </Link>

      {/* Student Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-dark-text-primary">{student.full_name}</h1>
            <div className="flex items-center gap-4 mt-2">
              <div className="flex items-center gap-2 text-dark-text-secondary">
                <Music size={16} className="text-brand" />
                <span>{student.instrument}</span>
              </div>
              <span className="text-dark-text-secondary">•</span>
              <span className="text-dark-text-secondary capitalize">{student.level.toLowerCase()}</span>
            </div>
            {student.parent_name && (
              <p className="mt-3 text-sm text-dark-text-secondary">
                Parent: {student.parent_name}
                {student.parent_email && ` (${student.parent_email})`}
              </p>
            )}
          </div>
          <Button onClick={() => navigate(`/record/${student.id}`)}>
            <Mic size={18} className="mr-2" />
            Record Lesson
          </Button>
        </div>
      </Card>

      {/* Lessons */}
      <section>
        <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Lesson History</h2>
        {lessons.length === 0 ? (
          <Card className="p-8 text-center">
            <Calendar size={48} className="mx-auto text-dark-text-secondary mb-4" />
            <h3 className="font-semibold text-dark-text-primary mb-2">No lessons yet</h3>
            <p className="text-dark-text-secondary mb-4">
              Record your first lesson with {student.full_name}
            </p>
            <Button onClick={() => navigate(`/record/${student.id}`)}>
              <Mic size={18} className="mr-2" />
              Record Lesson
            </Button>
          </Card>
        ) : (
          <Card className="divide-y divide-dark-border">
            {lessons.map((lesson) => (
              <div
                key={lesson.id}
                className="p-4 flex items-center justify-between hover:bg-dark-border/20 cursor-pointer transition-colors"
                onClick={() => navigate(`/lessons/${lesson.id}`)}
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-lg bg-brand/20 flex items-center justify-center">
                    <Calendar size={20} className="text-brand" />
                  </div>
                  <div>
                    <p className="font-medium text-dark-text-primary">
                      {new Date(lesson.lesson_date).toLocaleDateString('en-US', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </p>
                    <p className="text-sm text-dark-text-secondary">
                      {lesson.duration_seconds
                        ? `${Math.round(lesson.duration_seconds / 60)} minutes`
                        : 'Duration unknown'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={lesson.status} />
                  <ChevronRight size={18} className="text-dark-text-secondary" />
                </div>
              </div>
            ))}
          </Card>
        )}
      </section>
    </div>
  );
}

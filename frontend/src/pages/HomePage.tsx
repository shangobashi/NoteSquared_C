import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Music, Mic, ChevronRight, User } from 'lucide-react';
import { Student, studentsApi, Lesson, lessonsApi } from '../services/api';
import Button from '../components/Button';
import Card from '../components/Card';
import StatusBadge from '../components/StatusBadge';

export default function HomePage() {
  const navigate = useNavigate();
  const [students, setStudents] = useState<Student[]>([]);
  const [recentLessons, setRecentLessons] = useState<Lesson[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddStudent, setShowAddStudent] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [studentsRes, lessonsRes] = await Promise.all([
        studentsApi.list(),
        lessonsApi.list(),
      ]);
      setStudents(studentsRes.data);
      setRecentLessons(lessonsRes.data.slice(0, 5));
    } catch (err) {
      console.error('Failed to load data', err);
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

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-dark-text-primary">Welcome Back</h1>
          <p className="text-dark-text-secondary">Manage your students and lessons</p>
        </div>
        <Button onClick={() => setShowAddStudent(true)}>
          <Plus size={18} className="mr-2" />
          Add Student
        </Button>
      </div>

      {/* Students Grid */}
      <section>
        <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Your Students</h2>
        {students.length === 0 ? (
          <Card className="p-8 text-center">
            <User size={48} className="mx-auto text-dark-text-secondary mb-4" />
            <h3 className="font-semibold text-dark-text-primary mb-2">No students yet</h3>
            <p className="text-dark-text-secondary mb-4">
              Add your first student to get started
            </p>
            <Button onClick={() => setShowAddStudent(true)}>
              <Plus size={18} className="mr-2" />
              Add Student
            </Button>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {students.map((student) => (
              <Card
                key={student.id}
                className="p-4 hover:border-brand/50 cursor-pointer transition-colors"
                onClick={() => navigate(`/students/${student.id}`)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-dark-text-primary">{student.full_name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Music size={14} className="text-brand" />
                      <span className="text-sm text-dark-text-secondary">{student.instrument}</span>
                    </div>
                    <p className="text-xs text-dark-text-secondary mt-2">
                      {student.lesson_count} {student.lesson_count === 1 ? 'lesson' : 'lessons'}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/record/${student.id}`);
                    }}
                  >
                    <Mic size={18} />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </section>

      {/* Recent Lessons */}
      {recentLessons.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-dark-text-primary mb-4">Recent Lessons</h2>
          <Card className="divide-y divide-dark-border">
            {recentLessons.map((lesson) => (
              <div
                key={lesson.id}
                className="p-4 flex items-center justify-between hover:bg-dark-border/20 cursor-pointer transition-colors"
                onClick={() => navigate(`/lessons/${lesson.id}`)}
              >
                <div>
                  <h3 className="font-medium text-dark-text-primary">{lesson.student_name}</h3>
                  <p className="text-sm text-dark-text-secondary">
                    {new Date(lesson.lesson_date).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={lesson.status} />
                  <ChevronRight size={18} className="text-dark-text-secondary" />
                </div>
              </div>
            ))}
          </Card>
        </section>
      )}

      {/* Add Student Modal */}
      {showAddStudent && (
        <AddStudentModal
          onClose={() => setShowAddStudent(false)}
          onAdded={(student) => {
            setStudents([...students, student]);
            setShowAddStudent(false);
          }}
        />
      )}
    </div>
  );
}

// Add Student Modal
function AddStudentModal({
  onClose,
  onAdded,
}: {
  onClose: () => void;
  onAdded: (student: Student) => void;
}) {
  const [fullName, setFullName] = useState('');
  const [instrument, setInstrument] = useState('Piano');
  const [level, setLevel] = useState('BEGINNER');
  const [parentEmail, setParentEmail] = useState('');
  const [parentName, setParentName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const instruments = [
    'Piano', 'Violin', 'Viola', 'Cello', 'Guitar', 'Voice',
    'Flute', 'Clarinet', 'Saxophone', 'Trumpet', 'Drums', 'Other',
  ];

  const levels = [
    { value: 'BEGINNER', label: 'Beginner' },
    { value: 'INTERMEDIATE', label: 'Intermediate' },
    { value: 'ADVANCED', label: 'Advanced' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      const { data } = await studentsApi.create({
        full_name: fullName,
        instrument,
        level,
        parent_email: parentEmail || undefined,
        parent_name: parentName || undefined,
      });
      onAdded(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to add student');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-lg p-6">
        <h2 className="text-xl font-semibold text-dark-text-primary mb-4">Add New Student</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-1">
              Student Name *
            </label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full px-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-dark-text-primary mb-1">
                Instrument *
              </label>
              <select
                value={instrument}
                onChange={(e) => setInstrument(e.target.value)}
                className="w-full px-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary"
              >
                {instruments.map((inst) => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-dark-text-primary mb-1">
                Level
              </label>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="w-full px-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary"
              >
                {levels.map((l) => (
                  <option key={l.value} value={l.value}>{l.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-1">
              Parent Name
            </label>
            <input
              type="text"
              value={parentName}
              onChange={(e) => setParentName(e.target.value)}
              className="w-full px-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-text-primary mb-1">
              Parent Email
            </label>
            <input
              type="email"
              value={parentEmail}
              onChange={(e) => setParentEmail(e.target.value)}
              className="w-full px-4 py-2.5 bg-dark-bg border border-dark-border rounded-lg text-dark-text-primary"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Button type="button" variant="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" isLoading={isLoading}>
              Add Student
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

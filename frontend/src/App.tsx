import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './services/store';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import HomePage from './pages/HomePage';
import StudentPage from './pages/StudentPage';
import RecordPage from './pages/RecordPage';
import LessonPage from './pages/LessonPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomePage />} />
        <Route path="students/:studentId" element={<StudentPage />} />
        <Route path="record/:studentId" element={<RecordPage />} />
        <Route path="lessons/:lessonId" element={<LessonPage />} />
      </Route>
    </Routes>
  );
}

export default App;

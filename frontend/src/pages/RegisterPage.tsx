import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { authApi } from '../services/api';
import { useAuthStore } from '../services/store';
import Button from '../components/Button';
import Input from '../components/Input';
import Card from '../components/Card';

export default function RegisterPage() {
  const navigate = useNavigate();
  const { setToken, setUser } = useAuthStore();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setIsLoading(true);

    try {
      // Register
      const { data } = await authApi.register({ email, password, full_name: fullName });
      setToken(data.access_token);

      // Get user info
      const userRes = await authApi.me();
      setUser(userRes.data);

      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg flex flex-col items-center justify-center p-4">
      {/* Logo */}
      <div className="mb-8 text-center">
        <img src="/logo.png" alt="Note²" className="h-24 w-24 mx-auto mb-4 rounded-2xl shadow-lg" />
        <h1 className="text-3xl font-bold text-dark-text-primary">
          Note<sup className="text-brand text-lg">2</sup>
        </h1>
        <p className="text-dark-text-secondary mt-2">AI Practice Plan Generator for Music Teachers</p>
      </div>

      <Card className="w-full max-w-md p-8">
        <h2 className="text-xl font-semibold text-dark-text-primary mb-6">Create Account</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            type="text"
            label="Full Name"
            placeholder="Your name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />

          <Input
            type="email"
            label="Email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <Input
            type="password"
            label="Password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <Input
            type="password"
            label="Confirm Password"
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <Button type="submit" className="w-full" isLoading={isLoading}>
            Create Account
          </Button>
        </form>

        <p className="mt-6 text-center text-dark-text-secondary text-sm">
          Already have an account?{' '}
          <Link to="/login" className="text-brand hover:text-brand-light">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}

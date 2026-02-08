import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';

export const Login = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    if (isLogin) {
      const result = await login(email, password);
      if (result.success) {
        toast.success('Login realizado com sucesso!');
        navigate('/dashboard');
      } else {
        toast.error(result.error);
      }
    } else {
      if (!fullName) {
        toast.error('Por favor, preencha o nome completo');
        setLoading(false);
        return;
      }
      const result = await register(email, password, fullName);
      if (result.success) {
        toast.success('Cadastro realizado com sucesso!');
        navigate('/dashboard');
      } else {
        toast.error(result.error);
      }
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      <div 
        className="hidden lg:flex lg:w-1/2 relative bg-cover bg-center"
        style={{
          backgroundImage: `linear-gradient(rgba(15, 23, 42, 0.7), rgba(15, 23, 42, 0.7)), url('https://images.unsplash.com/photo-1757771440568-9613fc76b122?w=1200')`
        }}
        data-testid="login-background"
      >
        <div className="flex flex-col justify-center px-12 text-white">
          <h1 className="text-5xl font-heading font-black tracking-tight mb-4">FOX Locações</h1>
          <p className="text-lg text-slate-300">Sistema de gerenciamento de locação de caçambas</p>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-8 bg-slate-50">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-8" data-testid="login-form-container">
            <div className="mb-8">
              <h2 className="text-3xl font-heading font-bold text-slate-900 mb-2" data-testid="form-title">
                {isLogin ? 'Entrar' : 'Criar Conta'}
              </h2>
              <p className="text-slate-600">
                {isLogin ? 'Acesse sua conta para continuar' : 'Preencha os dados para criar sua conta'}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <Label htmlFor="fullName" data-testid="full-name-label">Nome Completo</Label>
                  <Input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Digite seu nome completo"
                    className="rounded-sm h-10"
                    data-testid="full-name-input"
                    required={!isLogin}
                  />
                </div>
              )}

              <div>
                <Label htmlFor="email" data-testid="email-label">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="seu@email.com"
                  className="rounded-sm h-10"
                  data-testid="email-input"
                  required
                />
              </div>

              <div>
                <Label htmlFor="password" data-testid="password-label">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="rounded-sm h-10"
                  data-testid="password-input"
                  required
                />
              </div>

              <Button
                type="submit"
                className="w-full btn-accent"
                disabled={loading}
                data-testid="submit-button"
              >
                {loading ? 'Aguarde...' : isLogin ? 'Entrar' : 'Criar Conta'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-sm text-slate-600 hover:text-slate-900 transition-colors"
                data-testid="toggle-form-button"
              >
                {isLogin ? 'Não tem uma conta? Criar conta' : 'Já tem uma conta? Entrar'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { DollarSign, TrendingUp, TrendingDown, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Cash = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      toast.error('Erro ao carregar dados do caixa');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-600">Carregando...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden" data-testid="cash-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="cash-title">
              Caixa
            </h1>
            <p className="text-slate-600 mt-2">Visão geral financeira</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-slate-900 rounded-sm border border-slate-800 shadow-lg p-8" data-testid="cash-balance-card">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-white/10 rounded-sm">
                  <Wallet className="w-8 h-8 text-white" strokeWidth={1.5} />
                </div>
                <div>
                  <h2 className="text-lg font-heading font-bold text-white">Saldo Atual</h2>
                  <p className="text-sm text-slate-400">Fluxo de caixa consolidado</p>
                </div>
              </div>
              <div className="font-mono text-5xl font-black text-white mb-2" data-testid="cash-balance">
                R$ {stats?.cash_balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </div>
              <div className="text-sm text-slate-400">Atualizado em tempo real</div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-8" data-testid="revenue-card">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-emerald-100 rounded-sm">
                  <DollarSign className="w-8 h-8 text-emerald-600" strokeWidth={1.5} />
                </div>
                <div>
                  <h2 className="text-lg font-heading font-bold text-slate-900">Receita do Mês</h2>
                  <p className="text-sm text-slate-600">Total de locações</p>
                </div>
              </div>
              <div className="font-mono text-5xl font-black text-slate-900 mb-2" data-testid="monthly-revenue">
                R$ {stats?.total_revenue_month?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </div>
              <div className="text-sm text-slate-600">{stats?.active_orders || 0} pedidos ativos</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm" data-testid="receivable-card">
              <div className="p-6 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-6 h-6 text-emerald-600" strokeWidth={1.5} />
                  <h2 className="text-xl font-heading font-bold text-slate-900">Contas a Receber</h2>
                </div>
              </div>
              <div className="p-8">
                <div className="font-mono text-4xl font-black text-emerald-600 mb-2" data-testid="total-receivable">
                  R$ {stats?.total_receivable?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
                </div>
                <p className="text-sm text-slate-600">Valores pendentes de recebimento</p>
                <div className="mt-6 pt-6 border-t border-slate-100">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Total de caçambas alugadas</span>
                    <span className="font-mono font-bold text-slate-900" data-testid="rented-count">{stats?.rented_dumpsters || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm" data-testid="payable-card">
              <div className="p-6 border-b border-slate-200">
                <div className="flex items-center gap-3">
                  <TrendingDown className="w-6 h-6 text-red-600" strokeWidth={1.5} />
                  <h2 className="text-xl font-heading font-bold text-slate-900">Contas a Pagar</h2>
                </div>
              </div>
              <div className="p-8">
                <div className="font-mono text-4xl font-black text-red-600 mb-2" data-testid="total-payable">
                  R$ {stats?.total_payable?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
                </div>
                <p className="text-sm text-slate-600">Valores pendentes de pagamento</p>
                <div className="mt-6 pt-6 border-t border-slate-100">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-600">Caçambas disponíveis</span>
                    <span className="font-mono font-bold text-slate-900" data-testid="available-count">{stats?.available_dumpsters || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 bg-blue-50 rounded-sm border border-blue-200 p-6" data-testid="pix-notice">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-blue-100 rounded-sm">
                <DollarSign className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-heading font-bold text-blue-900 mb-2">Integração PIX</h3>
                <p className="text-sm text-blue-800">
                  A integração com PIX está preparada para ser implementada. Entre em contato com o suporte para ativar esta funcionalidade.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Container, Users, FileText, DollarSign, Package, TrendingUp, TrendingDown, Clock } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, ordersRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/orders`)
      ]);
      setStats(statsRes.data);
      setRecentOrders(ordersRes.data.slice(0, 5));
    } catch (error) {
      toast.error('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      pending: 'bg-amber-100 text-amber-800',
      in_progress: 'bg-blue-100 text-blue-800',
      completed: 'bg-emerald-100 text-emerald-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return classes[status] || 'bg-slate-100 text-slate-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      pending: 'Pendente',
      in_progress: 'Em Andamento',
      completed: 'Concluído',
      cancelled: 'Cancelado'
    };
    return labels[status] || status;
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
    <div className="flex h-screen overflow-hidden" data-testid="dashboard-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="blueprint-bg" style={{ opacity: 0.03, position: 'fixed', inset: 0, pointerEvents: 'none' }}></div>
        <div className="max-w-[1600px] mx-auto p-8 relative">
          <div className="mb-8">
            <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="dashboard-title">
              Dashboard
            </h1>
            <p className="text-slate-600 mt-2">Visão geral do sistema FOX</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow duration-200" data-testid="stat-total-dumpsters">
              <div className="flex items-center justify-between mb-4">
                <Container className="w-8 h-8 text-slate-500" strokeWidth={1.5} />
                <Package className="w-5 h-5 text-slate-400" />
              </div>
              <div className="font-mono text-3xl font-bold text-slate-900" data-testid="total-dumpsters-value">{stats?.total_dumpsters || 0}</div>
              <div className="text-sm text-slate-600 mt-1">Total de Caçambas</div>
              <div className="flex gap-4 mt-3 text-xs">
                <span className="text-emerald-600" data-testid="available-dumpsters">Disponíveis: {stats?.available_dumpsters || 0}</span>
                <span className="text-orange-600" data-testid="rented-dumpsters">Alugadas: {stats?.rented_dumpsters || 0}</span>
              </div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow duration-200" data-testid="stat-active-orders">
              <div className="flex items-center justify-between mb-4">
                <FileText className="w-8 h-8 text-slate-500" strokeWidth={1.5} />
                <Clock className="w-5 h-5 text-slate-400" />
              </div>
              <div className="font-mono text-3xl font-bold text-slate-900" data-testid="active-orders-value">{stats?.active_orders || 0}</div>
              <div className="text-sm text-slate-600 mt-1">Pedidos Ativos</div>
              <div className="text-xs text-amber-600 mt-3" data-testid="pending-orders">Pendentes: {stats?.pending_orders || 0}</div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow duration-200" data-testid="stat-revenue">
              <div className="flex items-center justify-between mb-4">
                <DollarSign className="w-8 h-8 text-emerald-500" strokeWidth={1.5} />
                <TrendingUp className="w-5 h-5 text-emerald-400" />
              </div>
              <div className="font-mono text-3xl font-bold text-slate-900" data-testid="revenue-value">
                R$ {stats?.total_revenue_month?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </div>
              <div className="text-sm text-slate-600 mt-1">Receita do Mês</div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow duration-200" data-testid="stat-cash-balance">
              <div className="flex items-center justify-between mb-4">
                <DollarSign className="w-8 h-8 text-slate-500" strokeWidth={1.5} />
              </div>
              <div className="font-mono text-3xl font-bold text-slate-900" data-testid="cash-balance-value">
                R$ {stats?.cash_balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
              </div>
              <div className="text-sm text-slate-600 mt-1">Saldo em Caixa</div>
              <div className="flex gap-4 mt-3 text-xs">
                <span className="text-emerald-600" data-testid="total-receivable">A Receber: R$ {stats?.total_receivable?.toFixed(2) || '0.00'}</span>
                <span className="text-red-600" data-testid="total-payable">A Pagar: R$ {stats?.total_payable?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm" data-testid="recent-orders-section">
              <div className="p-6 border-b border-slate-200">
                <h2 className="text-xl font-heading font-bold text-slate-900" data-testid="recent-orders-title">Pedidos Recentes</h2>
              </div>
              <div className="p-6">
                {recentOrders.length === 0 ? (
                  <p className="text-slate-500 text-center py-8" data-testid="no-orders-message">Nenhum pedido encontrado</p>
                ) : (
                  <div className="space-y-3">
                    {recentOrders.map((order) => (
                      <div 
                        key={order.id} 
                        className="flex items-center justify-between p-4 bg-slate-50 rounded-sm hover:bg-slate-100 transition-colors"
                        data-testid={`order-item-${order.id}`}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-sm text-slate-500" data-testid={`order-id-${order.id}`}>
                              #{order.id.slice(0, 8)}
                            </span>
                            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(order.status)}`} data-testid={`order-status-${order.id}`}>
                              {getStatusLabel(order.status)}
                            </span>
                          </div>
                          <div className="text-sm font-medium text-slate-900 mt-1" data-testid={`order-client-${order.id}`}>{order.client_name}</div>
                          <div className="text-xs text-slate-600 mt-0.5" data-testid={`order-dumpster-${order.id}`}>Caçamba: {order.dumpster_identifier}</div>
                        </div>
                        <div className="text-right">
                          <div className="font-mono font-bold text-slate-900" data-testid={`order-value-${order.id}`}>
                            R$ {order.rental_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                          </div>
                          <div className="text-xs text-slate-500 mt-1" data-testid={`order-type-${order.id}`}>
                            {order.order_type === 'placement' ? 'Colocação' : order.order_type === 'removal' ? 'Retirada' : 'Troca'}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white rounded-sm border border-slate-200 shadow-sm" data-testid="financial-summary-section">
              <div className="p-6 border-b border-slate-200">
                <h2 className="text-xl font-heading font-bold text-slate-900" data-testid="financial-summary-title">Resumo Financeiro</h2>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between p-4 bg-emerald-50 rounded-sm" data-testid="receivable-summary">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="w-6 h-6 text-emerald-600" />
                    <div>
                      <div className="text-sm text-slate-600">Contas a Receber</div>
                      <div className="font-mono text-xl font-bold text-emerald-700" data-testid="receivable-amount">
                        R$ {stats?.total_receivable?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-red-50 rounded-sm" data-testid="payable-summary">
                  <div className="flex items-center gap-3">
                    <TrendingDown className="w-6 h-6 text-red-600" />
                    <div>
                      <div className="text-sm text-slate-600">Contas a Pagar</div>
                      <div className="font-mono text-xl font-bold text-red-700" data-testid="payable-amount">
                        R$ {stats?.total_payable?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-900 rounded-sm" data-testid="balance-summary">
                  <div className="flex items-center gap-3">
                    <DollarSign className="w-6 h-6 text-white" />
                    <div>
                      <div className="text-sm text-slate-300">Saldo Atual</div>
                      <div className="font-mono text-2xl font-bold text-white" data-testid="balance-amount">
                        R$ {stats?.cash_balance?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) || '0,00'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { TrendingUp, CheckCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AccountsReceivable = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, received: 0, pending: 0 });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/finance/accounts-receivable`);
      const data = response.data;
      setAccounts(data);
      
      const total = data.reduce((sum, acc) => sum + acc.amount, 0);
      const received = data.filter(acc => acc.is_received).reduce((sum, acc) => sum + acc.amount, 0);
      const pending = data.filter(acc => !acc.is_received).reduce((sum, acc) => sum + acc.amount, 0);
      setStats({ total, received, pending });
    } catch (error) {
      toast.error('Erro ao carregar contas');
    } finally {
      setLoading(false);
    }
  };

  const handleReceive = async (accountId) => {
    try {
      await axios.patch(`${API}/finance/accounts-receivable/${accountId}/receive`);
      toast.success('Pagamento recebido!');
      fetchAccounts();
    } catch (error) {
      toast.error('Erro ao marcar como recebido');
    }
  };

  const isOverdue = (dueDate) => {
    return new Date(dueDate) < new Date() ;
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="receivable-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="mb-8">
            <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="receivable-title">
              Contas a Receber
            </h1>
            <p className="text-slate-600 mt-2">Gerencie seus recebíveis</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6" data-testid="stat-total">
              <div className="flex items-center gap-3 mb-2">
                <TrendingUp className="w-6 h-6 text-slate-500" />
                <span className="text-sm text-slate-600">Total</span>
              </div>
              <div className="font-mono text-2xl font-bold text-slate-900" data-testid="total-value">
                R$ {stats.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-emerald-50 rounded-sm border border-emerald-200 shadow-sm p-6" data-testid="stat-received">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
                <span className="text-sm text-emerald-700">Recebido</span>
              </div>
              <div className="font-mono text-2xl font-bold text-emerald-900" data-testid="received-value">
                R$ {stats.received.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-amber-50 rounded-sm border border-amber-200 shadow-sm p-6" data-testid="stat-pending">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="w-6 h-6 text-amber-600" />
                <span className="text-sm text-amber-700">Pendente</span>
              </div>
              <div className="font-mono text-2xl font-bold text-amber-900" data-testid="pending-value">
                R$ {stats.pending.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-600">Carregando...</div>
          ) : accounts.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center" data-testid="no-accounts-message">
              <TrendingUp className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhuma conta a receber</p>
            </div>
          ) : (
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm overflow-hidden" data-testid="receivable-table">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-client">Cliente</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-order">Pedido</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-amount">Valor</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-due">Vencimento</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-status">Status</th>
                    <th className="text-right px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-actions">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {accounts.map((account) => (
                    <tr key={account.id} className="hover:bg-slate-50 transition-colors" data-testid={`account-row-${account.id}`}>
                      <td className="px-6 py-4" data-testid={`account-client-${account.id}`}>
                        <div className="font-medium text-slate-900">{account.client_name}</div>
                      </td>
                      <td className="px-6 py-4" data-testid={`account-order-${account.id}`}>
                        <span className="font-mono text-xs text-slate-500">#{account.order_id.slice(0, 8)}</span>
                        {account.notes && <div className="text-xs text-slate-500 mt-1">{account.notes}</div>}
                      </td>
                      <td className="px-6 py-4" data-testid={`account-amount-${account.id}`}>
                        <span className="font-mono font-bold text-slate-900">
                          R$ {account.amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="px-6 py-4" data-testid={`account-due-${account.id}`}>
                        <div className={`text-sm ${isOverdue(account.due_date) && !account.is_received ? 'text-red-600 font-medium' : 'text-slate-700'}`}>
                          {new Date(account.due_date).toLocaleDateString('pt-BR')}
                        </div>
                        {isOverdue(account.due_date) && !account.is_received && (
                          <div className="text-xs text-red-600">Vencido</div>
                        )}
                      </td>
                      <td className="px-6 py-4" data-testid={`account-status-${account.id}`}>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          account.is_received
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {account.is_received ? 'Recebido' : 'Pendente'}
                        </span>
                        {account.received_date && (
                          <div className="text-xs text-slate-500 mt-1">
                            {new Date(account.received_date).toLocaleDateString('pt-BR')}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {!account.is_received && (
                          <Button
                            size="sm"
                            onClick={() => handleReceive(account.id)}
                            className="btn-accent"
                            data-testid={`receive-button-${account.id}`}
                          >
                            Marcar como Recebido
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
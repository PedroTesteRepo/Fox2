import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Plus, TrendingDown, CheckCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const AccountsPayable = () => {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [stats, setStats] = useState({ total: 0, paid: 0, pending: 0 });
  const [formData, setFormData] = useState({
    description: '',
    amount: '',
    due_date: '',
    category: '',
    notes: ''
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      const response = await axios.get(`${API}/finance/accounts-payable`);
      const data = response.data;
      setAccounts(data);
      
      const total = data.reduce((sum, acc) => sum + acc.amount, 0);
      const paid = data.filter(acc => acc.is_paid).reduce((sum, acc) => sum + acc.amount, 0);
      const pending = data.filter(acc => !acc.is_paid).reduce((sum, acc) => sum + acc.amount, 0);
      setStats({ total, paid, pending });
    } catch (error) {
      toast.error('Erro ao carregar contas');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        amount: parseFloat(formData.amount),
        due_date: new Date(formData.due_date).toISOString()
      };
      await axios.post(`${API}/finance/accounts-payable`, data);
      toast.success('Conta criada com sucesso!');
      fetchAccounts();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Erro ao criar conta');
    }
  };

  const handlePay = async (accountId) => {
    try {
      await axios.patch(`${API}/finance/accounts-payable/${accountId}/pay`);
      toast.success('Conta marcada como paga!');
      fetchAccounts();
    } catch (error) {
      toast.error('Erro ao marcar como paga');
    }
  };

  const resetForm = () => {
    setFormData({
      description: '',
      amount: '',
      due_date: '',
      category: '',
      notes: ''
    });
  };

  const isOverdue = (dueDate) => {
    return new Date(dueDate) < new Date();
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="payable-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="payable-title">
                Contas a Pagar
              </h1>
              <p className="text-slate-600 mt-2">Gerencie suas despesas</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="btn-accent" data-testid="add-payable-button">
                  <Plus className="w-5 h-5 mr-2" />
                  Nova Despesa
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]" data-testid="payable-dialog">
                <DialogHeader>
                  <DialogTitle data-testid="dialog-title">Nova Despesa</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="description" data-testid="description-label">Descrição</Label>
                    <Input
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Descrição da despesa"
                      className="rounded-sm"
                      data-testid="description-input"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="amount" data-testid="amount-label">Valor</Label>
                      <Input
                        id="amount"
                        type="number"
                        step="0.01"
                        value={formData.amount}
                        onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                        placeholder="0.00"
                        className="rounded-sm"
                        data-testid="amount-input"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="category" data-testid="category-label">Categoria</Label>
                      <Input
                        id="category"
                        value={formData.category}
                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                        placeholder="Ex: Combustível"
                        className="rounded-sm"
                        data-testid="category-input"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="due_date" data-testid="due-date-label">Data de Vencimento</Label>
                    <Input
                      id="due_date"
                      type="datetime-local"
                      value={formData.due_date}
                      onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
                      className="rounded-sm"
                      data-testid="due-date-input"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="notes" data-testid="notes-label">Observações</Label>
                    <Input
                      id="notes"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Observações adicionais"
                      className="rounded-sm"
                      data-testid="notes-input"
                    />
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="btn-accent flex-1" data-testid="submit-payable-button">
                      Criar
                    </Button>
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setIsDialogOpen(false)}
                      className="rounded-sm"
                      data-testid="cancel-button"
                    >
                      Cancelar
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm p-6" data-testid="stat-total">
              <div className="flex items-center gap-3 mb-2">
                <TrendingDown className="w-6 h-6 text-slate-500" />
                <span className="text-sm text-slate-600">Total</span>
              </div>
              <div className="font-mono text-2xl font-bold text-slate-900" data-testid="total-value">
                R$ {stats.total.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-emerald-50 rounded-sm border border-emerald-200 shadow-sm p-6" data-testid="stat-paid">
              <div className="flex items-center gap-3 mb-2">
                <CheckCircle className="w-6 h-6 text-emerald-600" />
                <span className="text-sm text-emerald-700">Pago</span>
              </div>
              <div className="font-mono text-2xl font-bold text-emerald-900" data-testid="paid-value">
                R$ {stats.paid.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>

            <div className="bg-red-50 rounded-sm border border-red-200 shadow-sm p-6" data-testid="stat-pending">
              <div className="flex items-center gap-3 mb-2">
                <Clock className="w-6 h-6 text-red-600" />
                <span className="text-sm text-red-700">Pendente</span>
              </div>
              <div className="font-mono text-2xl font-bold text-red-900" data-testid="pending-value">
                R$ {stats.pending.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-600">Carregando...</div>
          ) : accounts.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center" data-testid="no-accounts-message">
              <TrendingDown className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhuma conta a pagar</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Nova Despesa" para começar</p>
            </div>
          ) : (
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm overflow-hidden" data-testid="payable-table">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-description">Descrição</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-category">Categoria</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-amount">Valor</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-due">Vencimento</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-status">Status</th>
                    <th className="text-right px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-actions">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {accounts.map((account) => (
                    <tr key={account.id} className="hover:bg-slate-50 transition-colors" data-testid={`account-row-${account.id}`}>
                      <td className="px-6 py-4" data-testid={`account-description-${account.id}`}>
                        <div className="font-medium text-slate-900">{account.description}</div>
                        {account.notes && <div className="text-xs text-slate-500 mt-1">{account.notes}</div>}
                      </td>
                      <td className="px-6 py-4" data-testid={`account-category-${account.id}`}>
                        <span className="px-2 py-1 bg-slate-100 text-slate-700 text-xs rounded-sm">{account.category}</span>
                      </td>
                      <td className="px-6 py-4" data-testid={`account-amount-${account.id}`}>
                        <span className="font-mono font-bold text-slate-900">
                          R$ {account.amount.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                      </td>
                      <td className="px-6 py-4" data-testid={`account-due-${account.id}`}>
                        <div className={`text-sm ${isOverdue(account.due_date) && !account.is_paid ? 'text-red-600 font-medium' : 'text-slate-700'}`}>
                          {new Date(account.due_date).toLocaleDateString('pt-BR')}
                        </div>
                        {isOverdue(account.due_date) && !account.is_paid && (
                          <div className="text-xs text-red-600">Vencido</div>
                        )}
                      </td>
                      <td className="px-6 py-4" data-testid={`account-status-${account.id}`}>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          account.is_paid
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {account.is_paid ? 'Pago' : 'Pendente'}
                        </span>
                        {account.paid_date && (
                          <div className="text-xs text-slate-500 mt-1">
                            {new Date(account.paid_date).toLocaleDateString('pt-BR')}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        {!account.is_paid && (
                          <Button
                            size="sm"
                            onClick={() => handlePay(account.id)}
                            className="btn-accent"
                            data-testid={`pay-button-${account.id}`}
                          >
                            Marcar como Pago
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
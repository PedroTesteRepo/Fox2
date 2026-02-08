import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, FileText, Calendar } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [clients, setClients] = useState([]);
  const [dumpsters, setDumpsters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    client_id: '',
    dumpster_id: '',
    order_type: 'placement',
    delivery_address: '',
    rental_value: '',
    payment_method: 'cash',
    scheduled_date: '',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordersRes, clientsRes, dumpstersRes] = await Promise.all([
        axios.get(`${API}/orders`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/dumpsters`)
      ]);
      setOrders(ordersRes.data);
      setClients(clientsRes.data);
      setDumpsters(dumpstersRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const data = {
        ...formData,
        rental_value: parseFloat(formData.rental_value),
        scheduled_date: new Date(formData.scheduled_date).toISOString()
      };
      await axios.post(`${API}/orders`, data);
      toast.success('Pedido criado com sucesso!');
      fetchData();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar pedido');
    }
  };

  const handleStatusChange = async (orderId, status) => {
    try {
      await axios.patch(`${API}/orders/${orderId}/status?status=${status}`);
      toast.success('Status atualizado com sucesso!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const resetForm = () => {
    setFormData({
      client_id: '',
      dumpster_id: '',
      order_type: 'placement',
      delivery_address: '',
      rental_value: '',
      payment_method: 'cash',
      scheduled_date: '',
      notes: ''
    });
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

  const getOrderTypeLabel = (type) => {
    const labels = {
      placement: 'Colocação',
      removal: 'Retirada',
      exchange: 'Troca'
    };
    return labels[type] || type;
  };

  const getPaymentMethodLabel = (method) => {
    const labels = {
      cash: 'Dinheiro',
      credit_card: 'Cartão de Crédito',
      debit_card: 'Cartão de Débito',
      bank_transfer: 'Transferência',
      pix: 'PIX'
    };
    return labels[method] || method;
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="orders-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="orders-title">
                Pedidos
              </h1>
              <p className="text-slate-600 mt-2">Gerencie suas locações</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="btn-accent" data-testid="add-order-button">
                  <Plus className="w-5 h-5 mr-2" />
                  Novo Pedido
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto" data-testid="order-dialog">
                <DialogHeader>
                  <DialogTitle data-testid="dialog-title">Novo Pedido</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="client_id" data-testid="client-label">Cliente</Label>
                    <Select
                      value={formData.client_id}
                      onValueChange={(value) => setFormData({ ...formData, client_id: value })}
                      required
                    >
                      <SelectTrigger className="rounded-sm" data-testid="client-select">
                        <SelectValue placeholder="Selecione um cliente" />
                      </SelectTrigger>
                      <SelectContent>
                        {clients.map((client) => (
                          <SelectItem key={client.id} value={client.id}>{client.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="dumpster_id" data-testid="dumpster-label">Caçamba</Label>
                    <Select
                      value={formData.dumpster_id}
                      onValueChange={(value) => setFormData({ ...formData, dumpster_id: value })}
                      required
                    >
                      <SelectTrigger className="rounded-sm" data-testid="dumpster-select">
                        <SelectValue placeholder="Selecione uma caçamba" />
                      </SelectTrigger>
                      <SelectContent>
                        {dumpsters.filter(d => d.status === 'available' || formData.order_type !== 'placement').map((dumpster) => (
                          <SelectItem key={dumpster.id} value={dumpster.id}>
                            {dumpster.identifier} - {dumpster.size} ({dumpster.status})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="order_type" data-testid="order-type-label">Tipo de Pedido</Label>
                    <Select
                      value={formData.order_type}
                      onValueChange={(value) => setFormData({ ...formData, order_type: value })}
                    >
                      <SelectTrigger className="rounded-sm" data-testid="order-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="placement">Colocação</SelectItem>
                        <SelectItem value="removal">Retirada</SelectItem>
                        <SelectItem value="exchange">Troca</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="delivery_address" data-testid="address-label">Endereço de Entrega</Label>
                    <Input
                      id="delivery_address"
                      value={formData.delivery_address}
                      onChange={(e) => setFormData({ ...formData, delivery_address: e.target.value })}
                      placeholder="Endereço completo"
                      className="rounded-sm"
                      data-testid="address-input"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="rental_value" data-testid="value-label">Valor da Locação</Label>
                      <Input
                        id="rental_value"
                        type="number"
                        step="0.01"
                        value={formData.rental_value}
                        onChange={(e) => setFormData({ ...formData, rental_value: e.target.value })}
                        placeholder="0.00"
                        className="rounded-sm"
                        data-testid="value-input"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="payment_method" data-testid="payment-label">Forma de Pagamento</Label>
                      <Select
                        value={formData.payment_method}
                        onValueChange={(value) => setFormData({ ...formData, payment_method: value })}
                      >
                        <SelectTrigger className="rounded-sm" data-testid="payment-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cash">Dinheiro</SelectItem>
                          <SelectItem value="credit_card">Cartão de Crédito</SelectItem>
                          <SelectItem value="debit_card">Cartão de Débito</SelectItem>
                          <SelectItem value="bank_transfer">Transferência</SelectItem>
                          <SelectItem value="pix">PIX (Em Breve)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="scheduled_date" data-testid="date-label">Data Agendada</Label>
                    <Input
                      id="scheduled_date"
                      type="datetime-local"
                      value={formData.scheduled_date}
                      onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                      className="rounded-sm"
                      data-testid="date-input"
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
                    <Button type="submit" className="btn-accent flex-1" data-testid="submit-order-button">
                      Criar Pedido
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

          {loading ? (
            <div className="text-center py-12 text-slate-600">Carregando...</div>
          ) : orders.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center" data-testid="no-orders-message">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhum pedido cadastrado</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Novo Pedido" para começar</p>
            </div>
          ) : (
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm overflow-hidden" data-testid="orders-table">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-id">ID</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-client">Cliente</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-dumpster">Caçamba</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-type">Tipo</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-value">Valor</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-status">Status</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-date">Data</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {orders.map((order) => (
                    <tr key={order.id} className="hover:bg-slate-50 transition-colors" data-testid={`order-row-${order.id}`}>
                      <td className="px-6 py-4" data-testid={`order-id-${order.id}`}>
                        <span className="font-mono text-xs text-slate-500">#{order.id.slice(0, 8)}</span>
                      </td>
                      <td className="px-6 py-4" data-testid={`order-client-${order.id}`}>
                        <div className="font-medium text-slate-900">{order.client_name}</div>
                      </td>
                      <td className="px-6 py-4" data-testid={`order-dumpster-${order.id}`}>
                        <span className="font-mono text-sm text-slate-700">{order.dumpster_identifier}</span>
                      </td>
                      <td className="px-6 py-4" data-testid={`order-type-${order.id}`}>
                        <span className="text-sm text-slate-700">{getOrderTypeLabel(order.order_type)}</span>
                      </td>
                      <td className="px-6 py-4" data-testid={`order-value-${order.id}`}>
                        <span className="font-mono font-medium text-slate-900">
                          R$ {order.rental_value.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                        <div className="text-xs text-slate-500">{getPaymentMethodLabel(order.payment_method)}</div>
                      </td>
                      <td className="px-6 py-4">
                        <Select
                          value={order.status}
                          onValueChange={(value) => handleStatusChange(order.id, value)}
                        >
                          <SelectTrigger className="rounded-sm w-[140px]" data-testid={`status-select-${order.id}`}>
                            <SelectValue>
                              <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(order.status)}`}>
                                {getStatusLabel(order.status)}
                              </span>
                            </SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pendente</SelectItem>
                            <SelectItem value="in_progress">Em Andamento</SelectItem>
                            <SelectItem value="completed">Concluído</SelectItem>
                            <SelectItem value="cancelled">Cancelado</SelectItem>
                          </SelectContent>
                        </Select>
                      </td>
                      <td className="px-6 py-4" data-testid={`order-date-${order.id}`}>
                        <div className="flex items-center gap-2 text-sm text-slate-700">
                          <Calendar className="w-4 h-4 text-slate-400" />
                          {new Date(order.scheduled_date).toLocaleDateString('pt-BR')}
                        </div>
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
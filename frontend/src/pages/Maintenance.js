import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Wrench, CheckCircle, XCircle, Calendar, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Maintenance = () => {
  const [maintenances, setMaintenances] = useState([]);
  const [dumpsters, setDumpsters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingMaintenance, setEditingMaintenance] = useState(null);
  const [formData, setFormData] = useState({
    dumpster_id: '',
    reason: '',
    supplier: '',
    start_date: '',
    expected_end_date: '',
    estimated_cost: '',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [maintenanceRes, dumpstersRes] = await Promise.all([
        axios.get(`${API}/maintenance`),
        axios.get(`${API}/dumpsters`)
      ]);
      setMaintenances(maintenanceRes.data);
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
      const payload = {
        ...formData,
        start_date: formData.start_date ? new Date(formData.start_date).toISOString() : new Date().toISOString(),
        expected_end_date: formData.expected_end_date ? new Date(formData.expected_end_date).toISOString() : null,
        estimated_cost: formData.estimated_cost ? parseFloat(formData.estimated_cost) : null
      };

      if (editingMaintenance) {
        await axios.put(`${API}/maintenance/${editingMaintenance.id}`, payload);
        toast.success('Manutenção atualizada com sucesso!');
      } else {
        await axios.post(`${API}/dumpsters/${formData.dumpster_id}/maintenance`, payload);
        toast.success('Manutenção cadastrada com sucesso!');
      }
      
      fetchData();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Erro ao salvar manutenção');
      console.error(error);
    }
  };

  const handleComplete = async (maintenanceId) => {
    const actualCost = prompt('Qual foi o custo real da manutenção?');
    if (actualCost === null) return;

    try {
      const cost = actualCost ? parseFloat(actualCost) : null;
      await axios.patch(`${API}/maintenance/${maintenanceId}/complete`, null, {
        params: { actual_cost: cost }
      });
      toast.success('Manutenção concluída! Caçamba disponível novamente.');
      fetchData();
    } catch (error) {
      toast.error('Erro ao concluir manutenção');
    }
  };

  const handleEdit = (maintenance) => {
    setEditingMaintenance(maintenance);
    setFormData({
      dumpster_id: maintenance.dumpster_id,
      reason: maintenance.reason || '',
      supplier: maintenance.supplier || '',
      start_date: maintenance.start_date ? new Date(maintenance.start_date).toISOString().slice(0, 16) : '',
      expected_end_date: maintenance.expected_end_date ? new Date(maintenance.expected_end_date).toISOString().slice(0, 16) : '',
      estimated_cost: maintenance.estimated_cost || '',
      notes: maintenance.notes || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este registro de manutenção?')) return;
    try {
      await axios.delete(`${API}/maintenance/${id}`);
      toast.success('Registro excluído com sucesso!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao excluir registro');
    }
  };

  const resetForm = () => {
    setEditingMaintenance(null);
    setFormData({
      dumpster_id: '',
      reason: '',
      supplier: '',
      start_date: '',
      expected_end_date: '',
      estimated_cost: '',
      notes: ''
    });
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      in_progress: { label: 'Em Andamento', class: 'bg-yellow-100 text-yellow-800', icon: Wrench },
      completed: { label: 'Concluída', class: 'bg-green-100 text-green-800', icon: CheckCircle },
      cancelled: { label: 'Cancelada', class: 'bg-red-100 text-red-800', icon: XCircle }
    };
    return statusConfig[status] || statusConfig.in_progress;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('pt-BR');
  };

  const formatCurrency = (value) => {
    if (!value) return '-';
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight">
                Manutenções
              </h1>
              <p className="text-slate-600 mt-2">Gerencie as manutenções das caçambas</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="btn-accent">
                  <Plus className="w-5 h-5 mr-2" />
                  Nova Manutenção
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>{editingMaintenance ? 'Editar Manutenção' : 'Nova Manutenção'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="dumpster_id">Caçamba *</Label>
                    <Select
                      value={formData.dumpster_id}
                      onValueChange={(value) => setFormData({ ...formData, dumpster_id: value })}
                      required
                      disabled={editingMaintenance}
                    >
                      <SelectTrigger className="rounded-sm">
                        <SelectValue placeholder="Selecione uma caçamba" />
                      </SelectTrigger>
                      <SelectContent>
                        {dumpsters.filter(d => d.status === 'available' || d.id === formData.dumpster_id).map((dumpster) => (
                          <SelectItem key={dumpster.id} value={dumpster.id}>
                            {dumpster.identifier} - {dumpster.size}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="reason">Motivo</Label>
                    <Textarea
                      id="reason"
                      value={formData.reason}
                      onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                      placeholder="Descreva o motivo da manutenção"
                      className="rounded-sm"
                      rows={3}
                    />
                  </div>

                  <div>
                    <Label htmlFor="supplier">Fornecedor</Label>
                    <Input
                      id="supplier"
                      value={formData.supplier}
                      onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                      placeholder="Nome do fornecedor/oficina"
                      className="rounded-sm"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="start_date">Data de Início</Label>
                      <Input
                        id="start_date"
                        type="datetime-local"
                        value={formData.start_date}
                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                        className="rounded-sm"
                      />
                    </div>
                    <div>
                      <Label htmlFor="expected_end_date">Previsão de Término</Label>
                      <Input
                        id="expected_end_date"
                        type="datetime-local"
                        value={formData.expected_end_date}
                        onChange={(e) => setFormData({ ...formData, expected_end_date: e.target.value })}
                        className="rounded-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="estimated_cost">Custo Estimado (R$)</Label>
                    <Input
                      id="estimated_cost"
                      type="number"
                      step="0.01"
                      value={formData.estimated_cost}
                      onChange={(e) => setFormData({ ...formData, estimated_cost: e.target.value })}
                      placeholder="0.00"
                      className="rounded-sm"
                    />
                  </div>

                  <div>
                    <Label htmlFor="notes">Observações</Label>
                    <Textarea
                      id="notes"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Informações adicionais"
                      className="rounded-sm"
                      rows={3}
                    />
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="btn-accent flex-1">
                      {editingMaintenance ? 'Atualizar' : 'Cadastrar'}
                    </Button>
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setIsDialogOpen(false)}
                      className="rounded-sm"
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
          ) : maintenances.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center">
              <Wrench className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhuma manutenção cadastrada</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Nova Manutenção" para começar</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {maintenances.map((maintenance) => {
                const statusInfo = getStatusBadge(maintenance.status);
                const StatusIcon = statusInfo.icon;
                
                return (
                  <div 
                    key={maintenance.id} 
                    className="bg-white rounded-sm border border-slate-200 shadow-sm hover:shadow-md transition-shadow duration-200 p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-slate-100 rounded-sm">
                          <Wrench className="w-6 h-6 text-slate-700" />
                        </div>
                        <div>
                          <h3 className="font-heading font-bold text-lg text-slate-900">
                            {maintenance.dumpster_identifier || 'Caçamba'}
                          </h3>
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium mt-1 ${statusInfo.class}`}>
                            <StatusIcon className="w-3 h-3" />
                            {statusInfo.label}
                          </span>
                        </div>
                      </div>
                      {maintenance.status === 'in_progress' && (
                        <Button
                          size="sm"
                          onClick={() => handleComplete(maintenance.id)}
                          className="btn-accent"
                        >
                          <CheckCircle className="w-4 h-4 mr-2" />
                          Concluir
                        </Button>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                      <div className="flex items-start gap-2">
                        <Calendar className="w-4 h-4 text-slate-500 mt-1" />
                        <div>
                          <p className="text-xs text-slate-500">Início</p>
                          <p className="text-sm font-medium text-slate-900">{formatDate(maintenance.start_date)}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <Calendar className="w-4 h-4 text-slate-500 mt-1" />
                        <div>
                          <p className="text-xs text-slate-500">Previsão</p>
                          <p className="text-sm font-medium text-slate-900">{formatDate(maintenance.expected_end_date)}</p>
                        </div>
                      </div>
                      <div className="flex items-start gap-2">
                        <DollarSign className="w-4 h-4 text-slate-500 mt-1" />
                        <div>
                          <p className="text-xs text-slate-500">Custo Estimado</p>
                          <p className="text-sm font-medium text-slate-900">{formatCurrency(maintenance.estimated_cost)}</p>
                        </div>
                      </div>
                    </div>

                    {maintenance.reason && (
                      <div className="mb-3 p-3 bg-slate-50 rounded-sm">
                        <p className="text-xs text-slate-500 mb-1">Motivo</p>
                        <p className="text-sm text-slate-900">{maintenance.reason}</p>
                      </div>
                    )}

                    {maintenance.supplier && (
                      <div className="mb-3">
                        <span className="text-xs text-slate-500">Fornecedor: </span>
                        <span className="text-sm font-medium text-slate-900">{maintenance.supplier}</span>
                      </div>
                    )}

                    {maintenance.notes && (
                      <div className="mb-3 text-sm text-slate-600 border-t border-slate-100 pt-3">
                        <p className="text-xs text-slate-500 mb-1">Observações</p>
                        <p>{maintenance.notes}</p>
                      </div>
                    )}

                    {maintenance.status === 'completed' && maintenance.actual_cost && (
                      <div className="mb-3 p-3 bg-green-50 rounded-sm border border-green-200">
                        <p className="text-xs text-green-700 mb-1">Custo Real</p>
                        <p className="text-lg font-bold text-green-900">{formatCurrency(maintenance.actual_cost)}</p>
                        <p className="text-xs text-green-600 mt-1">Concluída em {formatDate(maintenance.actual_end_date)}</p>
                      </div>
                    )}

                    <div className="flex gap-2 pt-3 border-t border-slate-100">
                      {maintenance.status === 'in_progress' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(maintenance)}
                          className="rounded-sm"
                        >
                          Editar
                        </Button>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(maintenance.id)}
                        className="rounded-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        Excluir
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

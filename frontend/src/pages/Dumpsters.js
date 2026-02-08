import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Pencil, Trash2, Container } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dumpsters = () => {
  const [dumpsters, setDumpsters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingDumpster, setEditingDumpster] = useState(null);
  const [formData, setFormData] = useState({
    identifier: '',
    size: '',
    capacity: '',
    description: ''
  });

  useEffect(() => {
    fetchDumpsters();
  }, []);

  const fetchDumpsters = async () => {
    try {
      const response = await axios.get(`${API}/dumpsters`);
      setDumpsters(response.data);
    } catch (error) {
      toast.error('Erro ao carregar caçambas');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingDumpster) {
        await axios.put(`${API}/dumpsters/${editingDumpster.id}`, formData);
        toast.success('Caçamba atualizada com sucesso!');
      } else {
        await axios.post(`${API}/dumpsters`, formData);
        toast.success('Caçamba criada com sucesso!');
      }
      fetchDumpsters();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Erro ao salvar caçamba');
    }
  };

  const handleEdit = (dumpster) => {
    setEditingDumpster(dumpster);
    setFormData({
      identifier: dumpster.identifier,
      size: dumpster.size,
      capacity: dumpster.capacity,
      description: dumpster.description || ''
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir esta caçamba?')) return;
    try {
      await axios.delete(`${API}/dumpsters/${id}`);
      toast.success('Caçamba excluída com sucesso!');
      fetchDumpsters();
    } catch (error) {
      toast.error('Erro ao excluir caçamba');
    }
  };

  const handleStatusChange = async (id, status) => {
    try {
      await axios.patch(`${API}/dumpsters/${id}/status?status=${status}`);
      toast.success('Status atualizado com sucesso!');
      fetchDumpsters();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const resetForm = () => {
    setEditingDumpster(null);
    setFormData({
      identifier: '',
      size: '',
      capacity: '',
      description: ''
    });
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      available: 'bg-emerald-100 text-emerald-800',
      rented: 'bg-orange-100 text-orange-800',
      maintenance: 'bg-red-100 text-red-800',
      in_transit: 'bg-blue-100 text-blue-800'
    };
    return classes[status] || 'bg-slate-100 text-slate-800';
  };

  const getStatusLabel = (status) => {
    const labels = {
      available: 'Disponível',
      rented: 'Em Uso',
      maintenance: 'Manutenção',
      in_transit: 'Em Trânsito'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      available: '#10b981', // green
      rented: '#f59e0b',    // yellow/amber
      maintenance: '#ef4444', // red
      in_transit: '#3b82f6'  // blue
    };
    return colors[status] || '#64748b';
  };

  // SVG Component for Dumpster
  const DumpsterIcon = ({ status, size = 80 }) => {
    const color = getStatusColor(status);
    return (
      <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
        {/* Caçamba */}
        <path
          d="M20 35 L15 85 L85 85 L80 35 Z"
          fill={color}
          stroke={color}
          strokeWidth="2"
        />
        {/* Tampa/Top */}
        <rect
          x="15"
          y="30"
          width="70"
          height="8"
          fill={color}
          stroke="#000"
          strokeWidth="1"
          opacity="0.8"
        />
        {/* Detalhes laterais */}
        <line x1="25" y1="40" x2="22" y2="80" stroke="#000" strokeWidth="1.5" opacity="0.3" />
        <line x1="50" y1="40" x2="50" y2="80" stroke="#000" strokeWidth="1.5" opacity="0.3" />
        <line x1="75" y1="40" x2="78" y2="80" stroke="#000" strokeWidth="1.5" opacity="0.3" />
        {/* Base */}
        <rect
          x="12"
          y="85"
          width="76"
          height="5"
          fill="#1e293b"
          rx="1"
        />
      </svg>
    );
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="dumpsters-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="dumpsters-title">
                Caçambas
              </h1>
              <p className="text-slate-600 mt-2">Gerencie suas caçambas</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="btn-accent" data-testid="add-dumpster-button">
                  <Plus className="w-5 h-5 mr-2" />
                  Nova Caçamba
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]" data-testid="dumpster-dialog">
                <DialogHeader>
                  <DialogTitle data-testid="dialog-title">{editingDumpster ? 'Editar Caçamba' : 'Nova Caçamba'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="identifier" data-testid="identifier-label">Identificador</Label>
                    <Input
                      id="identifier"
                      value={formData.identifier}
                      onChange={(e) => setFormData({ ...formData, identifier: e.target.value })}
                      placeholder="Ex: CAC-001"
                      className="rounded-sm"
                      data-testid="identifier-input"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="size" data-testid="size-label">Tamanho</Label>
                      <Input
                        id="size"
                        value={formData.size}
                        onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                        placeholder="Ex: 5m³"
                        className="rounded-sm"
                        data-testid="size-input"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="capacity" data-testid="capacity-label">Capacidade</Label>
                      <Input
                        id="capacity"
                        value={formData.capacity}
                        onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                        placeholder="Ex: 3 toneladas"
                        className="rounded-sm"
                        data-testid="capacity-input"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="description" data-testid="description-label">Descrição</Label>
                    <Input
                      id="description"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="Descrição adicional"
                      className="rounded-sm"
                      data-testid="description-input"
                    />
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="btn-accent flex-1" data-testid="submit-dumpster-button">
                      {editingDumpster ? 'Atualizar' : 'Criar'}
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
          ) : dumpsters.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center" data-testid="no-dumpsters-message">
              <Container className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhuma caçamba cadastrada</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Nova Caçamba" para começar</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="dumpsters-grid">
              {dumpsters.map((dumpster) => (
                <div 
                  key={dumpster.id} 
                  className="bg-white rounded-sm border border-slate-200 shadow-sm hover:shadow-md transition-shadow duration-200"
                  data-testid={`dumpster-card-${dumpster.id}`}
                >
                  <div className="p-6">
                    {/* Caçamba Visual */}
                    <div className="flex justify-center mb-4">
                      <DumpsterIcon status={dumpster.status} size={100} />
                    </div>

                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1 text-center">
                        <h3 className="font-heading font-bold text-xl text-slate-900 mb-2" data-testid={`dumpster-identifier-${dumpster.id}`}>
                          {dumpster.identifier}
                        </h3>
                        <span 
                          className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeClass(dumpster.status)}`}
                          data-testid={`dumpster-status-${dumpster.id}`}
                        >
                          {getStatusLabel(dumpster.status)}
                        </span>
                      </div>
                    </div>

                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Tamanho:</span>
                        <span className="font-mono font-medium text-slate-900" data-testid={`dumpster-size-${dumpster.id}`}>{dumpster.size}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-600">Capacidade:</span>
                        <span className="font-mono font-medium text-slate-900" data-testid={`dumpster-capacity-${dumpster.id}`}>{dumpster.capacity}</span>
                      </div>
                      {dumpster.description && (
                        <div className="text-sm text-slate-600 pt-2 border-t border-slate-100" data-testid={`dumpster-description-${dumpster.id}`}>
                          {dumpster.description}
                        </div>
                      )}
                      {dumpster.current_location && (
                        <div className="text-sm text-slate-600 pt-2 border-t border-slate-100" data-testid={`dumpster-location-${dumpster.id}`}>
                          <strong>Localização:</strong> {dumpster.current_location}
                        </div>
                      )}
                    </div>

                    <div className="flex flex-col gap-2">
                      <Select
                        value={dumpster.status}
                        onValueChange={(value) => handleStatusChange(dumpster.id, value)}
                      >
                        <SelectTrigger className="rounded-sm w-full" data-testid={`status-select-${dumpster.id}`}>
                          <SelectValue>Mudar Status</SelectValue>
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="available">Disponível</SelectItem>
                          <SelectItem value="rented">Em Uso</SelectItem>
                          <SelectItem value="maintenance">Manutenção</SelectItem>
                          <SelectItem value="in_transit">Em Trânsito</SelectItem>
                        </SelectContent>
                      </Select>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(dumpster)}
                          className="rounded-sm flex-1"
                          data-testid={`edit-dumpster-${dumpster.id}`}
                        >
                          <Pencil className="w-4 h-4 mr-2" />
                          Editar
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDelete(dumpster.id)}
                          className="rounded-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                          data-testid={`delete-dumpster-${dumpster.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
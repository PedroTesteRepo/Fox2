import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Pencil, Trash2, User, Phone, MapPin, FileText } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingClient, setEditingClient] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    document: '',
    document_type: 'cpf'
  });

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`);
      setClients(response.data);
    } catch (error) {
      toast.error('Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingClient) {
        await axios.put(`${API}/clients/${editingClient.id}`, formData);
        toast.success('Cliente atualizado com sucesso!');
      } else {
        await axios.post(`${API}/clients`, formData);
        toast.success('Cliente criado com sucesso!');
      }
      fetchClients();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Erro ao salvar cliente');
    }
  };

  const handleEdit = (client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      email: client.email || '',
      phone: client.phone,
      address: client.address,
      document: client.document,
      document_type: client.document_type
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este cliente?')) return;
    try {
      await axios.delete(`${API}/clients/${id}`);
      toast.success('Cliente excluído com sucesso!');
      fetchClients();
    } catch (error) {
      toast.error('Erro ao excluir cliente');
    }
  };

  const resetForm = () => {
    setEditingClient(null);
    setFormData({
      name: '',
      email: '',
      phone: '',
      address: '',
      document: '',
      document_type: 'cpf'
    });
  };

  return (
    <div className="flex h-screen overflow-hidden" data-testid="clients-page">
      <Sidebar />
      <div className="flex-1 overflow-auto">
        <div className="max-w-[1600px] mx-auto p-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-4xl font-heading font-black text-slate-900 tracking-tight" data-testid="clients-title">
                Clientes
              </h1>
              <p className="text-slate-600 mt-2">Gerencie seus clientes</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={(open) => {
              setIsDialogOpen(open);
              if (!open) resetForm();
            }}>
              <DialogTrigger asChild>
                <Button className="btn-accent" data-testid="add-client-button">
                  <Plus className="w-5 h-5 mr-2" />
                  Novo Cliente
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[600px]" data-testid="client-dialog">
                <DialogHeader>
                  <DialogTitle data-testid="dialog-title">{editingClient ? 'Editar Cliente' : 'Novo Cliente'}</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="name" data-testid="name-label">Nome</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Nome do cliente"
                      className="rounded-sm"
                      data-testid="name-input"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="document_type" data-testid="document-type-label">Tipo de Documento</Label>
                      <Select
                        value={formData.document_type}
                        onValueChange={(value) => setFormData({ ...formData, document_type: value })}
                      >
                        <SelectTrigger className="rounded-sm" data-testid="document-type-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="cpf" data-testid="document-type-cpf">CPF</SelectItem>
                          <SelectItem value="cnpj" data-testid="document-type-cnpj">CNPJ</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="document" data-testid="document-label">{formData.document_type === 'cpf' ? 'CPF' : 'CNPJ'}</Label>
                      <Input
                        id="document"
                        value={formData.document}
                        onChange={(e) => setFormData({ ...formData, document: e.target.value })}
                        placeholder={formData.document_type === 'cpf' ? '000.000.000-00' : '00.000.000/0000-00'}
                        className="rounded-sm"
                        data-testid="document-input"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="email" data-testid="email-label">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="email@exemplo.com"
                        className="rounded-sm"
                        data-testid="email-input"
                      />
                    </div>
                    <div>
                      <Label htmlFor="phone" data-testid="phone-label">Telefone</Label>
                      <Input
                        id="phone"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        placeholder="(00) 00000-0000"
                        className="rounded-sm"
                        data-testid="phone-input"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="address" data-testid="address-label">Endereço</Label>
                    <Input
                      id="address"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      placeholder="Endereço completo"
                      className="rounded-sm"
                      data-testid="address-input"
                      required
                    />
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="btn-accent flex-1" data-testid="submit-client-button">
                      {editingClient ? 'Atualizar' : 'Criar'}
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
          ) : clients.length === 0 ? (
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center" data-testid="no-clients-message">
              <User className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhum cliente cadastrado</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Novo Cliente" para começar</p>
            </div>
          ) : (
            <div className="bg-white rounded-sm border border-slate-200 shadow-sm overflow-hidden" data-testid="clients-table">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-name">Cliente</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-document">Documento</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-contact">Contato</th>
                    <th className="text-left px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-address">Endereço</th>
                    <th className="text-right px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider" data-testid="header-actions">Ações</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {clients.map((client) => (
                    <tr key={client.id} className="hover:bg-slate-50 transition-colors" data-testid={`client-row-${client.id}`}>
                      <td className="px-6 py-4" data-testid={`client-name-${client.id}`}>
                        <div className="font-medium text-slate-900">{client.name}</div>
                        {client.email && <div className="text-sm text-slate-500">{client.email}</div>}
                      </td>
                      <td className="px-6 py-4" data-testid={`client-document-${client.id}`}>
                        <div className="font-mono text-sm text-slate-700">{client.document}</div>
                        <div className="text-xs text-slate-500 uppercase">{client.document_type}</div>
                      </td>
                      <td className="px-6 py-4" data-testid={`client-phone-${client.id}`}>
                        <div className="flex items-center gap-2 text-sm text-slate-700">
                          <Phone className="w-4 h-4 text-slate-400" />
                          {client.phone}
                        </div>
                      </td>
                      <td className="px-6 py-4" data-testid={`client-address-${client.id}`}>
                        <div className="flex items-center gap-2 text-sm text-slate-700">
                          <MapPin className="w-4 h-4 text-slate-400" />
                          {client.address}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex gap-2 justify-end">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleEdit(client)}
                            className="rounded-sm"
                            data-testid={`edit-client-${client.id}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleDelete(client.id)}
                            className="rounded-sm text-red-600 hover:text-red-700 hover:bg-red-50"
                            data-testid={`delete-client-${client.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
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
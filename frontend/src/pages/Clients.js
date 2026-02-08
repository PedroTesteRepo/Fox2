import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Sidebar } from '../components/Sidebar';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Plus, Pencil, Trash2, User, Phone, MapPin, FileText, DollarSign, X } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Get auth headers
const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export const Clients = () => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isFinancialDialogOpen, setIsFinancialDialogOpen] = useState(false);
  const [selectedClientForFinancial, setSelectedClientForFinancial] = useState(null);
  const [financialSummary, setFinancialSummary] = useState(null);
  const [editingClient, setEditingClient] = useState(null);
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    address: '',
    document: '',
    document_type: 'cpf'
  });

  // Phones state
  const [phones, setPhones] = useState([{ phone: '', phone_type: 'Celular', is_primary: true }]);
  
  // Addresses state
  const [addresses, setAddresses] = useState([{
    address_type: 'Residencial',
    cep: '',
    street: '',
    number: '',
    complement: '',
    neighborhood: '',
    city: '',
    state: '',
    is_primary: true
  }]);

  useEffect(() => {
    fetchClients();
  }, []);

  const fetchClients = async () => {
    try {
      const response = await axios.get(`${API}/clients`, { headers: getAuthHeaders() });
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
      let clientId;
      
      if (editingClient) {
        // Update basic client info
        await axios.put(`${API}/clients/${editingClient.id}`, formData, { headers: getAuthHeaders() });
        clientId = editingClient.id;
        
        // Delete old phones and addresses
        const existingPhones = await axios.get(`${API}/clients/${clientId}/phones`, { headers: getAuthHeaders() });
        for (const phone of existingPhones.data) {
          await axios.delete(`${API}/clients/${clientId}/phones/${phone.id}`, { headers: getAuthHeaders() });
        }
        
        const existingAddresses = await axios.get(`${API}/clients/${clientId}/addresses`, { headers: getAuthHeaders() });
        for (const address of existingAddresses.data) {
          await axios.delete(`${API}/clients/${clientId}/addresses/${address.id}`, { headers: getAuthHeaders() });
        }
        
        toast.success('Cliente atualizado com sucesso!');
      } else {
        // Create new client
        const response = await axios.post(`${API}/clients`, formData, { headers: getAuthHeaders() });
        clientId = response.data.id;
        toast.success('Cliente criado com sucesso!');
      }
      
      // Add phones
      for (const phone of phones.filter(p => p.phone)) {
        await axios.post(`${API}/clients/${clientId}/phones`, phone, { headers: getAuthHeaders() });
      }
      
      // Add addresses
      for (const address of addresses.filter(a => a.cep && a.street)) {
        await axios.post(`${API}/clients/${clientId}/addresses`, address, { headers: getAuthHeaders() });
      }
      
      fetchClients();
      resetForm();
      setIsDialogOpen(false);
    } catch (error) {
      toast.error('Erro ao salvar cliente');
      console.error(error);
    }
  };

  const handleEdit = async (client) => {
    setEditingClient(client);
    setFormData({
      name: client.name,
      email: client.email || '',
      phone: client.phone,
      address: client.address,
      document: client.document,
      document_type: client.document_type
    });
    
    try {
      // Load phones
      const phonesResponse = await axios.get(`${API}/clients/${client.id}/phones`, { headers: getAuthHeaders() });
      if (phonesResponse.data.length > 0) {
        setPhones(phonesResponse.data.map(p => ({
          phone: p.phone,
          phone_type: p.phone_type,
          is_primary: p.is_primary
        })));
      }
      
      // Load addresses
      const addressesResponse = await axios.get(`${API}/clients/${client.id}/addresses`, { headers: getAuthHeaders() });
      if (addressesResponse.data.length > 0) {
        setAddresses(addressesResponse.data.map(a => ({
          address_type: a.address_type,
          cep: a.cep,
          street: a.street,
          number: a.number,
          complement: a.complement || '',
          neighborhood: a.neighborhood,
          city: a.city,
          state: a.state,
          is_primary: a.is_primary
        })));
      }
    } catch (error) {
      console.error('Error loading client details:', error);
    }
    
    setIsDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este cliente?')) return;
    try {
      await axios.delete(`${API}/clients/${id}`, { headers: getAuthHeaders() });
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
    setPhones([{ phone: '', phone_type: 'Celular', is_primary: true }]);
    setAddresses([{
      address_type: 'Residencial',
      cep: '',
      street: '',
      number: '',
      complement: '',
      neighborhood: '',
      city: '',
      state: '',
      is_primary: true
    }]);
  };

  // Phone management
  const addPhone = () => {
    setPhones([...phones, { phone: '', phone_type: 'Celular', is_primary: false }]);
  };

  const removePhone = (index) => {
    setPhones(phones.filter((_, i) => i !== index));
  };

  const updatePhone = (index, field, value) => {
    const newPhones = [...phones];
    newPhones[index][field] = value;
    
    // If setting primary, unset others
    if (field === 'is_primary' && value) {
      newPhones.forEach((p, i) => {
        if (i !== index) p.is_primary = false;
      });
    }
    
    setPhones(newPhones);
  };

  // Address management
  const addAddress = () => {
    setAddresses([...addresses, {
      address_type: 'Residencial',
      cep: '',
      street: '',
      number: '',
      complement: '',
      neighborhood: '',
      city: '',
      state: '',
      is_primary: false
    }]);
  };

  const removeAddress = (index) => {
    setAddresses(addresses.filter((_, i) => i !== index));
  };

  const updateAddress = (index, field, value) => {
    const newAddresses = [...addresses];
    newAddresses[index][field] = value;
    
    // If setting primary, unset others
    if (field === 'is_primary' && value) {
      newAddresses.forEach((a, i) => {
        if (i !== index) a.is_primary = false;
      });
    }
    
    setAddresses(newAddresses);
  };

  // CEP lookup
  const handleCepBlur = async (index) => {
    const cep = addresses[index].cep.replace(/\D/g, '');
    
    if (cep.length !== 8) return;
    
    try {
      const response = await axios.get(`${API}/cep/${cep}`, { headers: getAuthHeaders() });
      const data = response.data;
      
      const newAddresses = [...addresses];
      newAddresses[index] = {
        ...newAddresses[index],
        street: data.street || '',
        neighborhood: data.neighborhood || '',
        city: data.city || '',
        state: data.state || ''
      };
      setAddresses(newAddresses);
      
      toast.success('CEP encontrado!');
    } catch (error) {
      toast.error('CEP não encontrado');
    }
  };

  // Financial summary
  const viewFinancialSummary = async (client) => {
    setSelectedClientForFinancial(client);
    try {
      const response = await axios.get(`${API}/clients/${client.id}/financial-summary`, { headers: getAuthHeaders() });
      setFinancialSummary(response.data);
      setIsFinancialDialogOpen(true);
    } catch (error) {
      toast.error('Erro ao carregar resumo financeiro');
    }
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
              <p className="text-slate-600 mt-2">Gerencie seus clientes com múltiplos endereços e telefones</p>
            </div>
            
            {/* New Client Dialog */}
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
              <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto" data-testid="client-dialog">
                <DialogHeader>
                  <DialogTitle data-testid="dialog-title">{editingClient ? 'Editar Cliente' : 'Novo Cliente'}</DialogTitle>
                </DialogHeader>
                
                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Basic Info */}
                  <div className="space-y-4">
                    <h3 className="font-semibold text-lg border-b pb-2">Informações Básicas</h3>
                    
                    <div>
                      <Label htmlFor="name">Nome</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Nome do cliente"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label htmlFor="document_type">Tipo de Documento</Label>
                        <Select
                          value={formData.document_type}
                          onValueChange={(value) => setFormData({ ...formData, document_type: value })}
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="cpf">CPF</SelectItem>
                            <SelectItem value="cnpj">CNPJ</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div>
                        <Label htmlFor="document">{formData.document_type === 'cpf' ? 'CPF' : 'CNPJ'}</Label>
                        <Input
                          id="document"
                          value={formData.document}
                          onChange={(e) => setFormData({ ...formData, document: e.target.value })}
                          placeholder={formData.document_type === 'cpf' ? '000.000.000-00' : '00.000.000/0000-00'}
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <Label htmlFor="email">Email</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="email@exemplo.com"
                      />
                    </div>

                    {/* Keep old phone and address for backward compatibility */}
                    <Input type="hidden" value={formData.phone} />
                    <Input type="hidden" value={formData.address} />
                  </div>

                  {/* Phones Section */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b pb-2">
                      <h3 className="font-semibold text-lg">Telefones</h3>
                      <Button type="button" onClick={addPhone} variant="outline" size="sm">
                        <Plus className="w-4 h-4 mr-1" />
                        Adicionar
                      </Button>
                    </div>
                    
                    {phones.map((phone, index) => (
                      <div key={index} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Telefone {index + 1}</span>
                          {phones.length > 1 && (
                            <Button
                              type="button"
                              onClick={() => removePhone(index)}
                              variant="ghost"
                              size="sm"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label>Número</Label>
                            <Input
                              value={phone.phone}
                              onChange={(e) => updatePhone(index, 'phone', e.target.value)}
                              placeholder="(00) 00000-0000"
                              required
                            />
                          </div>
                          <div>
                            <Label>Tipo</Label>
                            <Input
                              value={phone.phone_type}
                              onChange={(e) => updatePhone(index, 'phone_type', e.target.value)}
                              placeholder="Ex: Celular, Comercial, WhatsApp"
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={phone.is_primary}
                            onChange={(e) => updatePhone(index, 'is_primary', e.target.checked)}
                            className="mr-2"
                          />
                          <Label className="mb-0">Telefone principal</Label>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Addresses Section */}
                  <div className="space-y-4">
                    <div className="flex items-center justify-between border-b pb-2">
                      <h3 className="font-semibold text-lg">Endereços</h3>
                      <Button type="button" onClick={addAddress} variant="outline" size="sm">
                        <Plus className="w-4 h-4 mr-1" />
                        Adicionar
                      </Button>
                    </div>
                    
                    {addresses.map((address, index) => (
                      <div key={index} className="border rounded-lg p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">Endereço {index + 1}</span>
                          {addresses.length > 1 && (
                            <Button
                              type="button"
                              onClick={() => removeAddress(index)}
                              variant="ghost"
                              size="sm"
                            >
                              <X className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <Label>Tipo</Label>
                            <Input
                              value={address.address_type}
                              onChange={(e) => updateAddress(index, 'address_type', e.target.value)}
                              placeholder="Ex: Residencial, Comercial, Obra"
                            />
                          </div>
                          <div>
                            <Label>CEP</Label>
                            <Input
                              value={address.cep}
                              onChange={(e) => updateAddress(index, 'cep', e.target.value)}
                              onBlur={() => handleCepBlur(index)}
                              placeholder="00000-000"
                              required
                            />
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-3 gap-3">
                          <div className="col-span-2">
                            <Label>Logradouro</Label>
                            <Input
                              value={address.street}
                              onChange={(e) => updateAddress(index, 'street', e.target.value)}
                              placeholder="Rua, Avenida..."
                              required
                            />
                          </div>
                          <div>
                            <Label>Número</Label>
                            <Input
                              value={address.number}
                              onChange={(e) => updateAddress(index, 'number', e.target.value)}
                              placeholder="123"
                              required
                            />
                          </div>
                        </div>
                        
                        <div>
                          <Label>Complemento</Label>
                          <Input
                            value={address.complement}
                            onChange={(e) => updateAddress(index, 'complement', e.target.value)}
                            placeholder="Apto, Bloco, Sala..."
                          />
                        </div>
                        
                        <div className="grid grid-cols-3 gap-3">
                          <div>
                            <Label>Bairro</Label>
                            <Input
                              value={address.neighborhood}
                              onChange={(e) => updateAddress(index, 'neighborhood', e.target.value)}
                              placeholder="Bairro"
                              required
                            />
                          </div>
                          <div>
                            <Label>Cidade</Label>
                            <Input
                              value={address.city}
                              onChange={(e) => updateAddress(index, 'city', e.target.value)}
                              placeholder="Cidade"
                              required
                            />
                          </div>
                          <div>
                            <Label>UF</Label>
                            <Input
                              value={address.state}
                              onChange={(e) => updateAddress(index, 'state', e.target.value)}
                              placeholder="SP"
                              maxLength={2}
                              required
                            />
                          </div>
                        </div>
                        
                        <div className="flex items-center">
                          <input
                            type="checkbox"
                            checked={address.is_primary}
                            onChange={(e) => updateAddress(index, 'is_primary', e.target.checked)}
                            className="mr-2"
                          />
                          <Label className="mb-0">Endereço principal</Label>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="flex gap-2 pt-4">
                    <Button type="submit" className="btn-accent flex-1">
                      {editingClient ? 'Atualizar' : 'Criar'}
                    </Button>
                    <Button 
                      type="button" 
                      variant="outline" 
                      onClick={() => setIsDialogOpen(false)}
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
            <div className="bg-white rounded-sm border border-slate-200 p-12 text-center">
              <User className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-600">Nenhum cliente cadastrado</p>
              <p className="text-sm text-slate-500 mt-2">Clique em "Novo Cliente" para começar</p>
            </div>
          ) : (
            <div className="grid gap-6">
              {clients.map((client) => (
                <div key={client.id} className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                          <User className="w-6 h-6 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="text-xl font-semibold text-slate-900">{client.name}</h3>
                          <p className="text-sm text-slate-500">
                            {client.document_type.toUpperCase()}: {client.document}
                          </p>
                        </div>
                      </div>
                      
                      {client.email && (
                        <p className="text-sm text-slate-600 mb-2">✉️ {client.email}</p>
                      )}
                      
                      <div className="flex items-center gap-2 text-sm text-slate-600 mb-1">
                        <Phone className="w-4 h-4" />
                        {client.phone}
                      </div>
                      
                      <div className="flex items-start gap-2 text-sm text-slate-600">
                        <MapPin className="w-4 h-4 mt-0.5" />
                        <span className="line-clamp-2">{client.address}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => viewFinancialSummary(client)}
                        title="Ver Pedidos e Financeiro"
                      >
                        <DollarSign className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(client)}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(client.id)}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Financial Summary Dialog */}
      <Dialog open={isFinancialDialogOpen} onOpenChange={setIsFinancialDialogOpen}>
        <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              Histórico Financeiro - {selectedClientForFinancial?.name}
            </DialogTitle>
          </DialogHeader>
          
          {financialSummary && (
            <div className="space-y-6">
              {/* Statistics */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="text-sm text-blue-600 font-medium">Total de Pedidos</p>
                  <p className="text-2xl font-bold text-blue-900">{financialSummary.total_orders}</p>
                </div>
                <div className="bg-yellow-50 p-4 rounded-lg">
                  <p className="text-sm text-yellow-600 font-medium">Pedidos Pendentes</p>
                  <p className="text-2xl font-bold text-yellow-900">{financialSummary.pending_orders}</p>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <p className="text-sm text-green-600 font-medium">Pedidos Concluídos</p>
                  <p className="text-2xl font-bold text-green-900">{financialSummary.completed_orders}</p>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="bg-purple-50 p-4 rounded-lg">
                  <p className="text-sm text-purple-600 font-medium">Total a Receber</p>
                  <p className="text-2xl font-bold text-purple-900">
                    R$ {financialSummary.total_receivable.toFixed(2)}
                  </p>
                </div>
                <div className="bg-red-50 p-4 rounded-lg">
                  <p className="text-sm text-red-600 font-medium">Valor Pendente</p>
                  <p className="text-2xl font-bold text-red-900">
                    R$ {financialSummary.pending_amount.toFixed(2)}
                  </p>
                </div>
                <div className="bg-teal-50 p-4 rounded-lg">
                  <p className="text-sm text-teal-600 font-medium">Já Recebido</p>
                  <p className="text-2xl font-bold text-teal-900">
                    R$ {financialSummary.total_received.toFixed(2)}
                  </p>
                </div>
              </div>

              {/* Orders List */}
              <div>
                <h3 className="font-semibold text-lg mb-3 border-b pb-2">Pedidos</h3>
                {financialSummary.orders.length === 0 ? (
                  <p className="text-slate-500 text-center py-4">Nenhum pedido encontrado</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {financialSummary.orders.map((order) => (
                      <div key={order.id} className="border rounded p-3 text-sm">
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{order.dumpster_identifier}</p>
                            <p className="text-slate-600">{order.order_type}</p>
                            <p className="text-xs text-slate-500">{order.delivery_address}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-green-600">R$ {order.rental_value.toFixed(2)}</p>
                            <span className={`text-xs px-2 py-1 rounded ${
                              order.status === 'completed' ? 'bg-green-100 text-green-700' :
                              order.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                              'bg-yellow-100 text-yellow-700'
                            }`}>
                              {order.status}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Accounts Receivable */}
              <div>
                <h3 className="font-semibold text-lg mb-3 border-b pb-2">Contas a Receber</h3>
                {financialSummary.accounts_receivable.length === 0 ? (
                  <p className="text-slate-500 text-center py-4">Nenhuma conta a receber</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {financialSummary.accounts_receivable.map((account) => (
                      <div key={account.id} className={`border rounded p-3 text-sm ${
                        account.is_received ? 'bg-green-50' : 'bg-red-50'
                      }`}>
                        <div className="flex justify-between items-start">
                          <div>
                            <p className="font-medium">{account.notes}</p>
                            <p className="text-xs text-slate-600">
                              Vencimento: {new Date(account.due_date).toLocaleDateString('pt-BR')}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold">R$ {account.amount.toFixed(2)}</p>
                            <span className={`text-xs px-2 py-1 rounded ${
                              account.is_received 
                                ? 'bg-green-200 text-green-800' 
                                : 'bg-red-200 text-red-800'
                            }`}>
                              {account.is_received ? 'Recebido' : 'Pendente'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

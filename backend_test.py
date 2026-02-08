#!/usr/bin/env python3
"""
Sistema FOX - Teste completo das APIs Backend
Testa todas as rotas migradas de MongoDB para MySQL/MariaDB
"""
import requests
import json
import uuid
from datetime import datetime, timezone, timedelta

class FOXAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.headers = {"Content-Type": "application/json"}
        self.test_data = {
            "user": {
                "email": "teste@fox.com",
                "password": "senha123", 
                "full_name": "Usuário Teste"
            },
            "client": {
                "name": "Cliente Teste",
                "email": "cliente@teste.com",
                "phone": "(11) 99999-9999",
                "address": "Rua Teste, 123",
                "document": "12345678901",
                "document_type": "cpf"
            },
            "dumpster": {
                "identifier": "CAC-001",
                "size": "5m³",
                "capacity": "3 toneladas",
                "description": "Caçamba de teste"
            },
            "order": {
                "order_type": "placement",
                "delivery_address": "Rua Entrega, 456",
                "rental_value": 500.00,
                "payment_method": "pix",
                "scheduled_date": "2025-07-15T10:00:00Z",
                "notes": "Teste de pedido"
            },
            "accounts_payable": {
                "description": "Manutenção Equipamento",
                "amount": 200.00,
                "due_date": "2025-07-20T00:00:00Z",
                "category": "manutenção",
                "notes": "Teste"
            }
        }
        self.created_ids = {}
        
    def log(self, message, status="INFO"):
        print(f"[{status}] {message}")
        
    def set_auth_token(self, token):
        """Define o token de autenticação"""
        self.token = token
        self.headers["Authorization"] = f"Bearer {token}"
        
    def test_request(self, method, endpoint, data=None, require_auth=True):
        """Executa uma requisição HTTP e retorna resultado"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if require_auth and not self.token:
            return {"success": False, "error": "Token não definido"}
            
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method == "PATCH":
                response = requests.patch(url, headers=headers, json=data, timeout=30)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return {"success": False, "error": f"Método {method} não suportado"}
                
            # Log da requisição
            self.log(f"{method} {url} -> {response.status_code}")
            
            if response.status_code >= 200 and response.status_code < 300:
                try:
                    result = response.json()
                    return {"success": True, "data": result, "status_code": response.status_code}
                except:
                    return {"success": True, "data": response.text, "status_code": response.status_code}
            else:
                try:
                    error_data = response.json()
                    return {"success": False, "error": error_data, "status_code": response.status_code}
                except:
                    return {"success": False, "error": response.text, "status_code": response.status_code}
                    
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout na requisição"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Erro de conexão"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def test_auth_register(self):
        """Testa registro de usuário"""
        self.log("\n=== TESTANDO REGISTRO DE USUÁRIO ===")
        
        result = self.test_request("POST", "/api/auth/register", self.test_data["user"], require_auth=False)
        
        if result["success"]:
            if "access_token" in result["data"] and "user" in result["data"]:
                self.set_auth_token(result["data"]["access_token"])
                self.log("✅ Registro realizado com sucesso")
                self.log(f"   Token recebido: {result['data']['access_token'][:20]}...")
                self.log(f"   Usuário: {result['data']['user']['full_name']}")
                return True
            else:
                self.log("❌ Registro falhou - Token ou dados do usuário não recebidos")
                return False
        else:
            # Se já existe, tenta fazer login
            if "already registered" in str(result["error"]).lower():
                self.log("⚠️  Usuário já existe, tentando login...")
                return self.test_auth_login()
            else:
                self.log(f"❌ Erro no registro: {result['error']}")
                return False

    def test_auth_login(self):
        """Testa login de usuário"""
        self.log("\n=== TESTANDO LOGIN DE USUÁRIO ===")
        
        login_data = {
            "email": self.test_data["user"]["email"],
            "password": self.test_data["user"]["password"]
        }
        
        result = self.test_request("POST", "/api/auth/login", login_data, require_auth=False)
        
        if result["success"]:
            if "access_token" in result["data"]:
                self.set_auth_token(result["data"]["access_token"])
                self.log("✅ Login realizado com sucesso")
                self.log(f"   Token recebido: {result['data']['access_token'][:20]}...")
                return True
            else:
                self.log("❌ Login falhou - Token não recebido")
                return False
        else:
            self.log(f"❌ Erro no login: {result['error']}")
            return False

    def test_auth_protection(self):
        """Testa se rotas protegidas retornam 401 sem autenticação"""
        self.log("\n=== TESTANDO PROTEÇÃO DE ROTAS ===")
        
        # Remove temporariamente o token
        old_token = self.token
        self.token = None
        self.headers.pop("Authorization", None)
        
        result = self.test_request("GET", "/api/clients")
        
        # Restaura o token
        self.set_auth_token(old_token)
        
        if not result["success"] and result.get("status_code") == 401:
            self.log("✅ Rota protegida funciona corretamente (401 sem auth)")
            return True
        else:
            self.log("❌ Rota protegida não está funcionando")
            return False

    def test_clients_crud(self):
        """Testa CRUD completo de clientes"""
        self.log("\n=== TESTANDO CRUD DE CLIENTES ===")
        
        success_count = 0
        
        # CREATE - Criar cliente
        result = self.test_request("POST", "/api/clients", self.test_data["client"])
        if result["success"]:
            client_id = result["data"]["id"]
            self.created_ids["client_id"] = client_id
            self.log(f"✅ Cliente criado: ID {client_id}")
            success_count += 1
        else:
            self.log(f"❌ Erro ao criar cliente: {result['error']}")
            return False

        # READ - Listar todos os clientes
        result = self.test_request("GET", "/api/clients")
        if result["success"] and isinstance(result["data"], list):
            self.log(f"✅ Lista de clientes obtida: {len(result['data'])} clientes")
            success_count += 1
        else:
            self.log(f"❌ Erro ao listar clientes: {result['error']}")

        # READ - Buscar cliente específico
        if "client_id" in self.created_ids:
            result = self.test_request("GET", f"/api/clients/{self.created_ids['client_id']}")
            if result["success"]:
                self.log("✅ Cliente específico encontrado")
                success_count += 1
            else:
                self.log(f"❌ Erro ao buscar cliente: {result['error']}")

        # UPDATE - Atualizar cliente
        if "client_id" in self.created_ids:
            updated_data = self.test_data["client"].copy()
            updated_data["name"] = "Cliente Teste Atualizado"
            result = self.test_request("PUT", f"/api/clients/{self.created_ids['client_id']}", updated_data)
            if result["success"]:
                self.log("✅ Cliente atualizado com sucesso")
                success_count += 1
            else:
                self.log(f"❌ Erro ao atualizar cliente: {result['error']}")

        return success_count >= 3

    def test_dumpsters_crud(self):
        """Testa CRUD completo de caçambas"""
        self.log("\n=== TESTANDO CRUD DE CAÇAMBAS ===")
        
        success_count = 0
        
        # CREATE - Criar caçamba
        result = self.test_request("POST", "/api/dumpsters", self.test_data["dumpster"])
        if result["success"]:
            dumpster_id = result["data"]["id"]
            self.created_ids["dumpster_id"] = dumpster_id
            self.log(f"✅ Caçamba criada: ID {dumpster_id}")
            success_count += 1
        else:
            self.log(f"❌ Erro ao criar caçamba: {result['error']}")
            return False

        # READ - Listar todas as caçambas
        result = self.test_request("GET", "/api/dumpsters")
        if result["success"] and isinstance(result["data"], list):
            self.log(f"✅ Lista de caçambas obtida: {len(result['data'])} caçambas")
            success_count += 1
        else:
            self.log(f"❌ Erro ao listar caçambas: {result['error']}")

        # READ - Buscar caçamba específica
        if "dumpster_id" in self.created_ids:
            result = self.test_request("GET", f"/api/dumpsters/{self.created_ids['dumpster_id']}")
            if result["success"]:
                self.log("✅ Caçamba específica encontrada")
                success_count += 1
            else:
                self.log(f"❌ Erro ao buscar caçamba: {result['error']}")

        # UPDATE - Atualizar caçamba
        if "dumpster_id" in self.created_ids:
            updated_data = self.test_data["dumpster"].copy()
            updated_data["description"] = "Caçamba de teste atualizada"
            result = self.test_request("PUT", f"/api/dumpsters/{self.created_ids['dumpster_id']}", updated_data)
            if result["success"]:
                self.log("✅ Caçamba atualizada com sucesso")
                success_count += 1
            else:
                self.log(f"❌ Erro ao atualizar caçamba: {result['error']}")

        # PATCH - Atualizar status da caçamba
        if "dumpster_id" in self.created_ids:
            result = self.test_request("PATCH", f"/api/dumpsters/{self.created_ids['dumpster_id']}/status?status=available")
            if result["success"]:
                self.log("✅ Status da caçamba atualizado")
                success_count += 1
            else:
                self.log(f"❌ Erro ao atualizar status: {result['error']}")

        return success_count >= 4

    def test_orders_crud(self):
        """Testa CRUD completo de pedidos"""
        self.log("\n=== TESTANDO CRUD DE PEDIDOS ===")
        
        if "client_id" not in self.created_ids or "dumpster_id" not in self.created_ids:
            self.log("❌ Cliente ou caçamba não criados - não é possível testar pedidos")
            return False
        
        success_count = 0
        
        # CREATE - Criar pedido
        order_data = self.test_data["order"].copy()
        order_data["client_id"] = self.created_ids["client_id"]
        order_data["dumpster_id"] = self.created_ids["dumpster_id"]
        
        result = self.test_request("POST", "/api/orders", order_data)
        if result["success"]:
            order_id = result["data"]["id"]
            self.created_ids["order_id"] = order_id
            self.log(f"✅ Pedido criado: ID {order_id}")
            success_count += 1
            
            # Verificar se caçamba mudou status para 'rented'
            dumpster_result = self.test_request("GET", f"/api/dumpsters/{self.created_ids['dumpster_id']}")
            if dumpster_result["success"] and dumpster_result["data"]["status"] == "rented":
                self.log("✅ Status da caçamba mudou para 'rented' corretamente")
                success_count += 1
            else:
                self.log("⚠️  Status da caçamba não mudou para 'rented'")
        else:
            self.log(f"❌ Erro ao criar pedido: {result['error']}")
            return False

        # READ - Listar todos os pedidos
        result = self.test_request("GET", "/api/orders")
        if result["success"] and isinstance(result["data"], list):
            self.log(f"✅ Lista de pedidos obtida: {len(result['data'])} pedidos")
            success_count += 1
        else:
            self.log(f"❌ Erro ao listar pedidos: {result['error']}")

        # READ - Buscar pedido específico
        if "order_id" in self.created_ids:
            result = self.test_request("GET", f"/api/orders/{self.created_ids['order_id']}")
            if result["success"]:
                self.log("✅ Pedido específico encontrado")
                success_count += 1
            else:
                self.log(f"❌ Erro ao buscar pedido: {result['error']}")

        # PATCH - Atualizar status do pedido
        if "order_id" in self.created_ids:
            result = self.test_request("PATCH", f"/api/orders/{self.created_ids['order_id']}/status?status=completed")
            if result["success"]:
                self.log("✅ Status do pedido atualizado")
                success_count += 1
            else:
                self.log(f"❌ Erro ao atualizar status: {result['error']}")

        # READ - Histórico de pedidos do cliente
        if "client_id" in self.created_ids:
            result = self.test_request("GET", f"/api/clients/{self.created_ids['client_id']}/orders")
            if result["success"] and isinstance(result["data"], list):
                self.log(f"✅ Histórico do cliente obtido: {len(result['data'])} pedidos")
                success_count += 1
            else:
                self.log(f"❌ Erro ao obter histórico: {result['error']}")

        return success_count >= 5

    def test_accounts_payable(self):
        """Testa funcionalidades de contas a pagar"""
        self.log("\n=== TESTANDO CONTAS A PAGAR ===")
        
        success_count = 0
        
        # CREATE - Criar conta a pagar
        result = self.test_request("POST", "/api/finance/accounts-payable", self.test_data["accounts_payable"])
        if result["success"]:
            payable_id = result["data"]["id"]
            self.created_ids["payable_id"] = payable_id
            self.log(f"✅ Conta a pagar criada: ID {payable_id}")
            success_count += 1
        else:
            self.log(f"❌ Erro ao criar conta a pagar: {result['error']}")
            return False

        # READ - Listar contas a pagar
        result = self.test_request("GET", "/api/finance/accounts-payable")
        if result["success"] and isinstance(result["data"], list):
            self.log(f"✅ Lista de contas a pagar obtida: {len(result['data'])} contas")
            success_count += 1
        else:
            self.log(f"❌ Erro ao listar contas a pagar: {result['error']}")

        # PATCH - Marcar como pago
        if "payable_id" in self.created_ids:
            result = self.test_request("PATCH", f"/api/finance/accounts-payable/{self.created_ids['payable_id']}/pay")
            if result["success"]:
                self.log("✅ Conta marcada como paga")
                success_count += 1
            else:
                self.log(f"❌ Erro ao marcar como paga: {result['error']}")

        return success_count >= 2

    def test_accounts_receivable(self):
        """Testa funcionalidades de contas a receber"""
        self.log("\n=== TESTANDO CONTAS A RECEBER ===")
        
        success_count = 0
        
        # READ - Listar contas a receber (devem ter sido criadas automaticamente no pedido)
        result = self.test_request("GET", "/api/finance/accounts-receivable")
        if result["success"] and isinstance(result["data"], list):
            self.log(f"✅ Lista de contas a receber obtida: {len(result['data'])} contas")
            if len(result["data"]) > 0:
                receivable_id = result["data"][0]["id"]
                self.created_ids["receivable_id"] = receivable_id
                self.log("✅ Conta a receber foi criada automaticamente no pedido")
                success_count += 2
            success_count += 1
        else:
            self.log(f"❌ Erro ao listar contas a receber: {result['error']}")

        # PATCH - Marcar como recebido
        if "receivable_id" in self.created_ids:
            result = self.test_request("PATCH", f"/api/finance/accounts-receivable/{self.created_ids['receivable_id']}/receive")
            if result["success"]:
                self.log("✅ Pagamento recebido")
                success_count += 1
            else:
                self.log(f"❌ Erro ao marcar como recebido: {result['error']}")

        return success_count >= 2

    def test_dashboard_stats(self):
        """Testa estatísticas do dashboard"""
        self.log("\n=== TESTANDO DASHBOARD STATS ===")
        
        result = self.test_request("GET", "/api/dashboard/stats")
        
        if result["success"]:
            stats = result["data"]
            required_fields = [
                "total_dumpsters", "available_dumpsters", "rented_dumpsters",
                "active_orders", "pending_orders", "total_revenue_month",
                "total_receivable", "total_payable", "cash_balance"
            ]
            
            missing_fields = [field for field in required_fields if field not in stats]
            
            if not missing_fields:
                self.log("✅ Dashboard retorna todas as estatísticas")
                self.log(f"   Total de caçambas: {stats['total_dumpsters']}")
                self.log(f"   Caçambas disponíveis: {stats['available_dumpsters']}")
                self.log(f"   Caçambas alugadas: {stats['rented_dumpsters']}")
                self.log(f"   Pedidos ativos: {stats['active_orders']}")
                self.log(f"   Receita do mês: R$ {stats['total_revenue_month']}")
                return True
            else:
                self.log(f"❌ Campos faltando no dashboard: {missing_fields}")
                return False
        else:
            self.log(f"❌ Erro ao obter stats do dashboard: {result['error']}")
            return False

    def cleanup_test_data(self):
        """Remove dados de teste criados"""
        self.log("\n=== LIMPANDO DADOS DE TESTE ===")
        
        # Deletar pedido (se existir)
        if "order_id" in self.created_ids:
            result = self.test_request("DELETE", f"/api/orders/{self.created_ids['order_id']}")
            if result["success"]:
                self.log("✅ Pedido removido")
            else:
                self.log(f"⚠️  Erro ao remover pedido: {result['error']}")

        # Deletar contas (se existirem)
        if "payable_id" in self.created_ids:
            result = self.test_request("DELETE", f"/api/finance/accounts-payable/{self.created_ids['payable_id']}")
            if result["success"]:
                self.log("✅ Conta a pagar removida")

        if "receivable_id" in self.created_ids:
            result = self.test_request("DELETE", f"/api/finance/accounts-receivable/{self.created_ids['receivable_id']}")
            if result["success"]:
                self.log("✅ Conta a receber removida")

        # Deletar caçamba (se existir)
        if "dumpster_id" in self.created_ids:
            result = self.test_request("DELETE", f"/api/dumpsters/{self.created_ids['dumpster_id']}")
            if result["success"]:
                self.log("✅ Caçamba removida")
            else:
                self.log(f"⚠️  Erro ao remover caçamba: {result['error']}")

        # Deletar cliente (se existir)
        if "client_id" in self.created_ids:
            result = self.test_request("DELETE", f"/api/clients/{self.created_ids['client_id']}")
            if result["success"]:
                self.log("✅ Cliente removido")
            else:
                self.log(f"⚠️  Erro ao remover cliente: {result['error']}")

    def run_all_tests(self):
        """Executa todos os testes em sequência"""
        self.log("🚀 INICIANDO TESTES DO SISTEMA FOX")
        self.log(f"🔗 Base URL: {self.base_url}")
        
        results = {}
        
        # 1. Teste de Autenticação
        results["auth_register"] = self.test_auth_register()
        if not results["auth_register"]:
            self.log("❌ Falha crítica na autenticação - parando testes")
            return results
            
        results["auth_protection"] = self.test_auth_protection()
        
        # 2. Testes CRUD
        results["clients_crud"] = self.test_clients_crud()
        results["dumpsters_crud"] = self.test_dumpsters_crud()
        results["orders_crud"] = self.test_orders_crud()
        
        # 3. Testes Financeiros
        results["accounts_payable"] = self.test_accounts_payable()
        results["accounts_receivable"] = self.test_accounts_receivable()
        
        # 4. Dashboard
        results["dashboard_stats"] = self.test_dashboard_stats()
        
        # 5. Limpeza
        self.cleanup_test_data()
        
        # Relatório final
        self.log("\n" + "="*60)
        self.log("📊 RELATÓRIO FINAL DOS TESTES")
        self.log("="*60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASSOU" if result else "❌ FALHOU"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        self.log(f"\nRESULTADO: {passed}/{total} testes passaram")
        
        if passed == total:
            self.log("🎉 TODOS OS TESTES PASSARAM!")
        elif passed >= total * 0.8:
            self.log("⚠️  MAIORIA DOS TESTES PASSOU - Verificar falhas")
        else:
            self.log("❌ MUITOS TESTES FALHARAM - Sistema precisa de correção")
        
        return results

def main():
    """Função principal"""
    base_url = "https://cargo-monitor-30.preview.emergentagent.com"
    tester = FOXAPITester(base_url)
    results = tester.run_all_tests()
    return results

if __name__ == "__main__":
    main()
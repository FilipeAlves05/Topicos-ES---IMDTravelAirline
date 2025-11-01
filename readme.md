# 🛫 Projeto IMDAirline (Baseline)

**IMDAirline** é um sistema de **microsserviços** para compra de passagens aéreas, desenvolvido como parte da avaliação da disciplina **Tópicos Especiais em Engenharia de Software**.  

O sistema é totalmente **containerizado** e composto por **4 microsserviços** e um **orquestrador**, todos executados em **Docker**.

---

## 🧩 Arquitetura do Sistema

O projeto segue uma **arquitetura de microsserviços orquestrada**, conforme o diagrama fornecido na especificação do projeto [cite:45].

### 🔹 Serviços

| Serviço | Porta | Descrição | Endpoints |
|----------|-------|------------|------------|
| **IMDTravel (Orquestrador)** | `8000` | Coordena a compra de passagens aéreas | `/buyTicket` [cite:56] |
| **AirlinesHub** | `8001` | Gerencia informações de voos e processa vendas | `/flight` [cite:62], `/sell` [cite:71] |
| **Exchange** | `8002` | Fornece taxa de câmbio Dólar → Real | `/convert` [cite:67] |
| **Fidelity** | `8003` | Gerencia o programa de bônus de fidelidade | `/bonus` [cite:76] |

---

## ⚙️ Como Executar o Sistema

O sistema é **100% containerizado**.  
A única dependência necessária é o **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**.

### ✅ 1. Pré-requisitos

- Docker Desktop instalado e em execução.

### 🚀 2. Executando os Serviços

Abra um terminal na **raiz do projeto** e execute:

```bash
docker-compose up --build
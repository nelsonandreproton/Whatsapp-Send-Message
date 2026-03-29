# WhatsApp Aniversários — OutSystems O11

**Data:** 2026-03-29
**Tags:** #outsystems #whatsapp #integração #hobby

---

## Contexto

Integração entre uma aplicação OutSystems O11 (com tabela de amigos/família com nome, telemóvel e data de aniversário) e grupos WhatsApp, para envio automático de mensagens de parabéns.

---

## Solução: Evolution API (self-hosted, gratuita)

Projeto open source que simula o WhatsApp Web e expõe uma REST API.
Corre no servidor **Hetzner via Docker**.

> ⚠️ Não é API oficial da Meta. Viola os ToS do WhatsApp. Para uso pessoal/hobby o risco é baixo, mas o número pode ser banido se houver abuso.

---

## Arquitetura

```
OutSystems Timer (diário, ex: 9h00)
    ↓
Query: amigos com aniversário hoje
    ↓
REST call → Evolution API (Hetzner Docker)
    ↓
Mensagem enviada para o grupo WhatsApp
```

---

## Setup da Evolution API

### docker-compose.yml

```yaml
version: '3'
services:
  evolution-api:
    image: atendai/evolution-api:latest
    ports:
      - "8080:8080"
    environment:
      - AUTHENTICATION_API_KEY=o_teu_api_key_secreto
    volumes:
      - evolution_data:/evolution/instances
volumes:
  evolution_data:
```

```bash
docker compose up -d
```

---

## Endpoints Principais

### Criar instância
```
POST http://servidor:8080/instance/create
Headers: apikey: <api_key>
Body: { "instanceName": "aniversarios", "qrcode": true }
```

### Ligar número (QR code)
```
GET http://servidor:8080/instance/connect/aniversarios
```
→ Escanear com WhatsApp > Dispositivos ligados > Ligar um dispositivo

### Obter ID do grupo
```
GET http://servidor:8080/group/fetchAllGroups/aniversarios?getParticipants=false
```
→ Guardar o ID do tipo `120363XXXXXXXXX@g.us`

### Enviar mensagem para o grupo
```
POST http://servidor:8080/message/sendText/aniversarios
Headers: apikey: <api_key>
Body:
{
  "number": "120363XXXXXXXXX@g.us",
  "text": "🎂 Hoje é aniversário do João! Parabéns! 🎉"
}
```

---

## OutSystems O11 — Lógica do Timer

1. **Timer** diário (ex: 9h00)
2. **Query:** `SELECT * FROM Amigos WHERE DAY(DataAniversario) = DAY(TODAY()) AND MONTH(DataAniversario) = MONTH(TODAY())`
3. Para cada registo → chamar REST API externo (consume) apontando para a Evolution API
4. **REST externo:**
   - Base URL: `http://servidor:8080`
   - Header fixo: `apikey = <api_key>`
   - Method: `POST /message/sendText/aniversarios`

---

## Multi-grupo (Trabalho + Família)

Usa **uma única instância** com **dois Group IDs** diferentes:

| Grupo | Tabela OutSystems | Group ID WhatsApp |
|-------|-------------------|-------------------|
| Trabalho | Colegas | `120363XXX@g.us` |
| Família | Familia | `120363YYY@g.us` |

💡 Guardar os Group IDs como configuração na BD do OutSystems (não hardcoded).

---

## Notas

- Não é necessário ser admin do grupo para enviar mensagens
- Só é necessário ser membro do grupo com o número ligado à Evolution API
- Ser admin só seria necessário para gerir membros, nome ou permissões do grupo

---

## Links Úteis

- [Evolution API GitHub](https://github.com/EvolutionAPI/evolution-api)
- [Evolution API Docs](https://doc.evolution-api.com)

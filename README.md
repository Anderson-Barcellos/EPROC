
## 🔧 Pré-requisitos

### Software Necessário
- Python 3.8+
- Google Chrome
- ChromeDriver

### Dependências Python
```bash
selenium
google-cloud-vision
openai
google-generativeai
PyMuPDF (fitz)
Pillow
tqdm
tiktoken
```

### Serviços Externos
- **Google Cloud Vision API**: Para OCR
- **OpenAI API**: Para modelos GPT
- **Google Gemini API**: Para modelos Gemini

## 🚀 Instalação

1. **Clone o repositório**:
```bash
git clone <repository-url>
cd "Nova pasta (2)"
```

2. **Instale as dependências**:
```bash
pip install -r requirements.txt
```

3. **Configure o ChromeDriver**:
   - Baixe o ChromeDriver compatível com sua versão do Chrome
   - Adicione ao PATH do sistema

## ⚙️ Configuração

### 1. Chaves de API

Configure as seguintes variáveis de ambiente:

```bash
# OpenAI
export OPENAI="sua-chave-openai"

# Google Gemini
export GEMINI="sua-chave-gemini"
```

### 2. Google Cloud Vision

Crie o arquivo `cloud_ocr/key.json` com suas credenciais do Google Cloud:

```json
{
  "type": "service_account",
  "project_id": "seu-projeto",
  "private_key_id": "...",
  "private_key": "...",
  "client_email": "...",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token"
}
```

### 3. Configuração do e-Proc

Configure suas credenciais de acesso ao sistema e-Proc no código de automação.

## 📖 Uso

### Processamento Individual

```python
from WorkFlow import Generate_Final_Report

# Gerar laudo usando GPT-4
Generate_Final_Report(
    model="gpt-4o-2024-08-06",
    system_instruction="prompt_personalizado",
    reasoning_effort="medium"
)
```

### Processamento em Lote

```python
from run_one_at_time import run_processes_sequentially

# Processar todos os relatórios na pasta Reports/
run_processes_sequentially()
```

### Automação e-Proc

```python
from autofill import main
from selenium import webdriver

driver = webdriver.Chrome()
main(driver, "numero_do_processo")
```

## 🧩 Módulos

### 📄 WorkFlow.py
Módulo principal que coordena todo o fluxo de processamento:
- Reconhecimento OCR de documentos
- Geração de relatórios com IA
- Limpeza de arquivos temporários

### 🤖 Models/models.py
Interface para modelos de IA:
- **GPTReport**: Geração usando modelos GPT
- **GeminiReport**: Geração usando Gemini
- **O3Report**: Suporte para modelos O3
- **MiniTemplate**: Organização de dados estruturados

### 🌐 autofill.py
Automação completa do sistema e-Proc:
- Login automático
- Navegação por processos
- Preenchimento de formulários
- Upload de documentos

### 🔍 cloud_ocr/
Processamento OCR avançado:
- Extração de texto de PDFs
- Processamento por páginas
- Otimização de qualidade

### 🛠️ Tools/
Utilitários do sistema:
- Contagem de tokens
- Barras de progresso
- Cálculo de custos de API

## 📊 Exemplo de Fluxo Completo

```python
# 1. Processar documento PDF
from cloud_ocr.cloud_ocr import VertexOCR
VertexOCR("documento.pdf", "output.txt")

# 2. Gerar template estruturado
from Models.models import MiniTemplate
template = MiniTemplate("gpt-4o-mini", "output.txt", None)

# 3. Gerar laudo final
from Models.models import GPTReport
GPTReport("output.txt", "gpt-4o-2024-08-06", system_instruction)

# 4. Automatizar preenchimento
from autofill import main
main(driver, "numero_processo")
```

## 🔒 Segurança e Conformidade

- **Dados Sensíveis**: Todos os documentos médicos são processados localmente
- **APIs Seguras**: Comunicação criptografada com serviços de IA
- **Conformidade LGPD**: Processamento responsável de dados pessoais

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Erro de ChromeDriver**:
   - Verifique se o ChromeDriver está no PATH
   - Confirme compatibilidade de versões

2. **Erro de API**:
   - Verifique as chaves de API
   - Confirme limites de uso

3. **Erro de OCR**:
   - Verifique as credenciais do Google Cloud
   - Confirme qualidade do PDF

## 📈 Roadmap

- [ ] Interface gráfica (GUI)
- [ ] Suporte a mais formatos de documento
- [ ] Integração com outros sistemas judiciais
- [ ] Dashboard de métricas
- [ ] API REST

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença [MIT](LICENSE).

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no GitHub
- Consulte a documentação dos módulos
- Verifique os logs de erro

---

**⚠️ Aviso Legal**: Este sistema é uma ferramenta de apoio para profissionais médicos e jurídicos. A responsabilidade final pelos laudos e decisões permanece com os profissionais qualificados.

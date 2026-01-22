# Bot para Emissão de NFS-e Nacional

Um bot para automatizar o preenchimento e a emissão de Notas Fiscais de Serviço Eletrônicas (NFS-e) no portal nacional.

## 🎯 Objetivos

O principal objetivo deste projeto é simplificar e agilizar o processo de emissão de NFS-e para prestadores de serviço, especialmente para aqueles que emitem notas com frequência. A automação reduz o trabalho manual, minimiza erros de digitação e economiza tempo.

## 🚀 Instalação

Siga os passos abaixo para configurar o ambiente e instalar o bot.

**Pré-requisitos:**
- [Python 3.13+](https://www.python.org/downloads/)
- Git

**Passos:**

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/seu-usuario/bot_nfse_nacional.git
   cd bot_nfse_nacional
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   # Crie o ambiente
   python -m venv .venv

   # Ative o ambiente
   # No Windows:
   .venv\Scripts\activate
   # No macOS/Linux:
   source .venv/bin/activate
   ```

3. **Instale as dependências:**
   O projeto usa um `pyproject.toml` para gerenciar as dependências. Instale-as com o pip:
   ```bash
   pip install .
   ```

## ⚙️ Uso

1. **Configuração:**
   - Antes de iniciar, configure seus dados de acesso e as informações padrão para a emissão da nota. Renomeie o arquivo `config.example.py` para `config.py` (ou verifique a estrutura de configuração existente) e preencha todas as variáveis necessárias, como login, senha, e dados do tomador e do serviço.

2. **Executando o Bot:**
   Para iniciar a aplicação, execute a interface gráfica:
   ```bash
   python gui.py
   ```
   A interface permitirá que você inicie o processo de automação, que abrirá o navegador, fará o login no portal da NFS-e e preencherá os dados da nota fiscal conforme configurado.

## 🤝 Contribuições

Contribuições são bem-vindas! Se você tem ideias para melhorar o projeto, siga os passos abaixo:

1. **Faça um Fork** do projeto.
2. **Crie uma Branch** para sua feature (`git checkout -b feature/sua-feature`).
3. **Faça o Commit** de suas mudanças (`git commit -m 'Adiciona sua-feature'`).
4. **Faça o Push** para a Branch (`git push origin feature/sua-feature`).
5. **Abra um Pull Request**.

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

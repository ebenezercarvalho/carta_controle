# Gerador de Carta de Controle

Este projeto é um aplicativo web desenvolvido em Python utilizando a biblioteca **Streamlit**. O aplicativo permite que o usuário insira dados (por meio de colagem direta ou upload de arquivo CSV) para gerar uma carta de controle, um tipo de gráfico utilizado para monitoramento de processos. Além disso, o aplicativo gera um relatório em PDF contendo o gráfico e informações estatísticas do conjunto de dados.

## Funcionalidades

- **Entrada de Dados**: 
  - O usuário pode colar os dados diretamente em um campo de texto ou fazer upload de um arquivo CSV.
  - Os dados devem conter duas colunas: `Data` (no formato `aaaa-mm-dd`) e `Valor` (numérico).

- **Validação e Processamento de Dados**:
  - O aplicativo valida se as colunas necessárias estão presentes e se os dados estão no formato correto.
  - Realiza a conversão de datas e valores para os tipos apropriados utilizando **Pandas** e **Numpy**.

- **Geração de Gráfico**:
  - Utiliza a biblioteca **Plotly** para criar um gráfico interativo que exibe a evolução dos valores ao longo do tempo.
  - Adiciona linhas de controle, incluindo a média e os limites de controle baseados em desvios padrão (+/-1σ, +/-2σ, +/-3σ).

- **Relatório em PDF**:
  - Gera um relatório em PDF utilizando a biblioteca **fpdf**.
  - O relatório contém informações gerais, o gráfico da carta de controle e estatísticas relevantes (média, desvio padrão e número de amostras).
  - Disponibiliza o PDF para download diretamente na interface do aplicativo.

  ## O aplicativo já está implantado e pode ser acessado em: [https://cartacontrole.streamlit.app/](https://cartacontrole.streamlit.app/).

## Tecnologias Utilizadas

- **Python**: Linguagem de programação utilizada para o desenvolvimento do aplicativo.
- **Streamlit**: Framework para criação de aplicativos web interativos.
- **Pandas**: Biblioteca para manipulação e análise de dados.
- **Numpy**: Biblioteca para cálculos numéricos.
- **Plotly**: Biblioteca para criação de gráficos interativos.
- **fpdf**: Biblioteca para geração de arquivos PDF.
- **Docker**: Ferramenta utilizada para conteinerização e deploy do aplicativo. Com Docker, é possível criar um ambiente isolado e replicável, facilitando a execução do aplicativo em diferentes sistemas.

## Como Executar

### Requisitos
- Python 3.7 ou superior
- Pip (gerenciador de pacotes)

### Instalação

1. Clone o repositório:

```bash
git clone https://github.com/ebenezercarvalho/carta_controle.git
cd carta_controle
```

**Instale as dependências:**

```bash
pip install -r requirements.txt
```

**Executando o Aplicativo**

```bash
streamlit run app.py
```

**Executando com Docker**

**Construa a imagem Docker:**

```bash
docker build -t carta-controle .
```

**Execute o contêiner:**

```bash
docker run -p 8501:8501 carta-controle
```

Acesse o aplicativo no navegador em: http://localhost:8501

**Estrutura do Projeto**

```bash
├── app.py               # Arquivo principal do aplicativo
├── Dockerfile           # Arquivo para construção da imagem Docker
├── requirements.txt     # Lista de dependências do projeto
├── README.md            # Documentação do projeto
└── ...                  # Outros arquivos e pastas do projeto
```

**Contribuição**

Contribuições são bem-vindas! Se você deseja melhorar o projeto, por favor, abra uma issue ou envie um pull request.

**Desenvolvido por Ebenézer Carvalho**


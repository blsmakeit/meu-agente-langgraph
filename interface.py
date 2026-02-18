import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd
import requests
import time
from typing import Dict, Any, Optional

# ===========================
# CONFIGURAÇÃO DA PÁGINA
# ===========================

st.set_page_config(
    page_title="AIOps Command Center",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===========================
# CONSTANTES
# ===========================

DEFAULT_BACKEND_URL = "https://langgraph-content-engine.onrender.com"

# ===========================
# FUNÇÕES AUXILIARES
# ===========================

def make_api_request(url: str, endpoint: str, data: Optional[Dict] = None, method: str = "POST") -> Optional[Dict[str, Any]]:
    """
    Make API request with error handling.

    Args:
        url: Base URL of the API
        endpoint: API endpoint
        data: Request data (for POST)
        method: HTTP method

    Returns:
        Response JSON or None if error
    """
    try:
        full_url = f"{url}{endpoint}"

        if method == "POST":
            response = requests.post(full_url, json=data, timeout=120)
        else:
            response = requests.get(full_url, timeout=30)

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout: A requisição demorou muito. Tente novamente.")
        return None
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Erro de conexão: Não foi possível conectar ao backend em {url}")
        return None
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro HTTP {e.response.status_code}: {e.response.text}")
        return None
    except Exception as e:
        st.error(f"❌ Erro inesperado: {str(e)}")
        return None

def show_progress_bar(status_text: str, progress: int):
    """Show progress bar with status text"""
    progress_bar = st.progress(progress)
    status = st.empty()
    status.text(status_text)
    time.sleep(0.3)
    return progress_bar, status

def format_timestamp(timestamp_str: str) -> str:
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%H:%M:%S")
    except:
        return timestamp_str

# ===========================
# INICIALIZAÇÃO DO SESSION STATE
# ===========================

if 'last_response' not in st.session_state:
    st.session_state.last_response = None

# ===========================
# SIDEBAR - CONTROL PANEL
# ===========================

with st.sidebar:
    st.title("⚙️ Control Panel")

    # API Configuration
    st.subheader("🔌 API Configuration")
    api_url = st.text_input(
        "Backend URL",
        value=DEFAULT_BACKEND_URL,
        help="URL do backend FastAPI"
    )

    # Test connection
    if st.button("🧪 Test Connection"):
        with st.spinner("Testando conexão..."):
            health = make_api_request(api_url, "/health", method="GET")
            if health:
                st.success(f"✅ Conectado! Modelo: {health.get('modelo_ativo', 'N/A')}")
            else:
                st.error("❌ Falha na conexão")

    st.divider()

    # System Status
    st.subheader("📊 System Status")
    health = make_api_request(api_url, "/health", method="GET")
    if health:
        st.metric("Status", health.get("status", "unknown"))
        st.metric("Versão", health.get("versao", "N/A"))
    else:
        st.warning("Backend offline")

    st.divider()

    # About
    st.caption("🧠 AIOps Command Center v2.0")
    st.caption("Developed by **Bruno Sousa**")

# ===========================
# MAIN CONTENT - TABS
# ===========================

st.title("🧠 AIOps Content Engine")
st.markdown("Sistema empresarial de geração de conteúdo com tracking completo")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 Product View",
    "🔍 Logic Trace",
    "📊 Performance Analytics",
    "🧪 Prompt Lab"
])

# ===========================
# TAB 1: PRODUCT VIEW
# ===========================

with tab1:
    st.header("📝 Content Generator")
    st.markdown("Interface limpa para geração de conteúdo profissional")

    # Input area
    tema = st.text_area(
        "Tema do Artigo",
        placeholder="Digite o tema do artigo que deseja gerar...\n\nExemplo: A importância da Inteligência Artificial no futuro da medicina",
        height=120,
        help="Descreva o tema sobre o qual deseja gerar conteúdo"
    )

    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        generate_btn = st.button("🚀 Gerar Conteúdo", type="primary", use_container_width=True)

    if generate_btn:
        if not tema:
            st.warning("⚠️ Por favor, insira um tema antes de gerar.")
        else:
            # Progress indicators
            progress_container = st.container()

            with progress_container:
                st.markdown("### ⏳ Processando requisição...")

                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Stage 1: Initialization
                    status_text.text("🔄 Inicializando agente...")
                    progress_bar.progress(20)
                    time.sleep(0.5)

                    # Stage 2: Making API call
                    status_text.text("✍️ Redator gerando primeiro rascunho...")
                    progress_bar.progress(40)

                    response = make_api_request(api_url, "/gerar", {"tema": tema})

                    if response:
                        # Stage 3: Processing
                        status_text.text("🔍 Revisor analisando conteúdo...")
                        progress_bar.progress(70)
                        time.sleep(0.5)

                        # Stage 4: Finalizing
                        status_text.text("✅ Finalizando...")
                        progress_bar.progress(100)
                        time.sleep(0.3)

                        # Store in session state
                        st.session_state.last_response = response

                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        progress_container.empty()

                        # Show success message
                        st.success("✅ Conteúdo gerado com sucesso!")

                        # Display result
                        st.markdown("### 📄 Texto Final")
                        st.markdown(response["texto_final"])

                        # Show quick metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Iterações", response["metricas"]["numero_iteracoes"])
                        with col2:
                            st.metric("Tempo", f"{response['metricas']['tempo_total_segundos']:.2f}s")
                        with col3:
                            st.metric("Custo", f"${response['metricas']['custo_estimado_usd']:.4f}")

                        # Expander with reviewer feedback
                        with st.expander("💬 Ver Feedback do Revisor"):
                            for critica in response["historico_criticas"]:
                                if critica:
                                    st.info(critica["feedback"])

                    else:
                        progress_bar.empty()
                        status_text.empty()

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Erro inesperado: {str(e)}")

# ===========================
# TAB 2: LOGIC TRACE
# ===========================

with tab2:
    st.header("🔍 Logic Trace - Diálogo Interno")
    st.markdown("Timeline completa do processo de geração e revisão")

    if st.session_state.last_response:
        response = st.session_state.last_response

        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Request ID", response["request_id"][:8] + "...")
        with col2:
            st.metric("Total de Logs", len(response["logs_decisao"]))
        with col3:
            st.metric("Status", "✅ APROVADO" if response["aprovado"] else "⚠️ REJEITADO")

        st.divider()

        # Timeline visualization
        for i, log in enumerate(response["logs_decisao"]):
            # Determine if this should be expanded (only first one)
            is_expanded = (i == 0)

            # Icon based on action
            icon = "✍️" if log["acao"] == "redator" else "🔍"

            with st.expander(
                f"{icon} Iteração {log['iteracao']} - {log['acao'].upper()} ({format_timestamp(log['timestamp'])})",
                expanded=is_expanded
            ):
                # Two columns for input/output
                col1, col2 = st.columns([1, 1])

                with col1:
                    st.markdown("**📥 Entrada:**")
                    st.code(log["entrada"], language="markdown")

                with col2:
                    st.markdown("**📤 Saída:**")
                    st.code(log["saida"], language="markdown")

                # Metrics row
                m1, m2, m3 = st.columns(3)
                with m1:
                    st.metric("Tokens Usados", log.get("tokens_usados", "N/A"))
                with m2:
                    st.metric("Tempo de Execução", f"{log['tempo_execucao']:.2f}s")
                with m3:
                    badge = "✅ Redator" if log["acao"] == "redator" else "🔍 Revisor"
                    st.metric("Ação", badge)

    else:
        st.info("💡 Nenhuma execução disponível. Gere conteúdo na aba 'Product View' primeiro.")

# ===========================
# TAB 3: PERFORMANCE ANALYTICS
# ===========================

with tab3:
    st.header("📊 Performance Analytics")
    st.markdown("Métricas detalhadas de performance e custos")

    if st.session_state.last_response:
        response = st.session_state.last_response
        metricas = response["metricas"]

        # Row 1: Key Metrics with Delta
        st.subheader("⚡ Métricas Principais")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            # Latency vs target (5s)
            delta_latency = metricas["tempo_total_segundos"] - 5.0
            st.metric(
                "⚡ Latência Total",
                f"{metricas['tempo_total_segundos']:.2f}s",
                delta=f"{delta_latency:+.2f}s vs target (5.0s)",
                delta_color="inverse"
            )

        with col2:
            # Iterations vs ideal (2)
            delta_iter = metricas["numero_iteracoes"] - 2
            st.metric(
                "🔄 Iterações",
                metricas["numero_iteracoes"],
                delta=f"{delta_iter:+d} vs ideal (2)",
                delta_color="inverse" if delta_iter > 0 else "normal"
            )

        with col3:
            # Total tokens
            st.metric(
                "🪙 Tokens Totais",
                f"{metricas['tokens_totais']:,}",
                delta=f"${metricas['custo_estimado_usd']:.4f}"
            )

        with col4:
            # Estimated cost
            st.metric(
                "💰 Custo Estimado",
                f"${metricas['custo_estimado_usd']:.4f}",
                delta=None
            )

        st.divider()

        # Row 2: Plotly Charts
        st.subheader("📈 Visualizações Interativas")

        chart_col1, chart_col2 = st.columns([1, 1])

        with chart_col1:
            # Gauge Chart for Latency
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=metricas["tempo_total_segundos"],
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Latência (segundos)", 'font': {'size': 24, 'color': '#00ff41'}},
                delta={'reference': 5.0, 'increasing': {'color': "#ff00ff"}, 'decreasing': {'color': "#00ff41"}},
                gauge={
                    'axis': {'range': [None, 15], 'tickcolor': '#00ff41'},
                    'bar': {'color': "#00ff41"},
                    'steps': [
                        {'range': [0, 5], 'color': "#1a1a2e"},
                        {'range': [5, 10], 'color': "#16213e"},
                        {'range': [10, 15], 'color': "#0f3460"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 10
                    }
                }
            ))

            fig_gauge.update_layout(height=400)

            st.plotly_chart(fig_gauge, use_container_width=True)

        with chart_col2:
            # Donut Chart for Token Distribution
            labels = ['Input Tokens', 'Output Tokens']
            values = [
                metricas["tokens_totais_input"],
                metricas["tokens_totais_output"]
            ]

            fig_donut = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.5,
                marker=dict(colors=['#ff6b6b', '#4ecdc4']),
                textfont=dict(size=14, color='white')
            )])

            fig_donut.update_layout(
                title_text="Distribuição de Tokens",
                height=400
            )

            st.plotly_chart(fig_donut, use_container_width=True)

        st.divider()

        # Row 3: Cost Simulator
        st.subheader("💸 Simulador de Custos")

        num_execucoes = st.slider(
            "Projetar custos para quantas execuções?",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            help="Simula o custo total para múltiplas execuções com métricas similares"
        )

        custo_projetado = metricas["custo_estimado_usd"] * num_execucoes

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(f"Custo para {num_execucoes:,} execuções", f"${custo_projetado:.2f}")
        with col2:
            st.metric("Custo médio por execução", f"${metricas['custo_estimado_usd']:.4f}")
        with col3:
            tokens_medios = metricas["tokens_totais"]
            st.metric("Tokens médios por execução", f"{tokens_medios:,}")

        st.divider()

        # Row 4: Performance Table with Conditional Styling
        st.subheader("📈 Tabela Comparativa de Performance")

        df_performance = pd.DataFrame({
            'Métrica': [
                'Tempo Total',
                'Iterações',
                'Tokens Input',
                'Tokens Output',
                'Custo Estimado'
            ],
            'Valor Atual': [
                f"{metricas['tempo_total_segundos']:.2f}s",
                metricas["numero_iteracoes"],
                f"{metricas['tokens_totais_input']:,}",
                f"{metricas['tokens_totais_output']:,}",
                f"${metricas['custo_estimado_usd']:.4f}"
            ],
            'Target/Ideal': [
                '≤ 5.0s',
                '≤ 2',
                'N/A',
                'N/A',
                'N/A'
            ],
            'Status': [
                '✅ OK' if metricas['tempo_total_segundos'] <= 5.0 else '⚠️ Alto',
                '✅ OK' if metricas['numero_iteracoes'] <= 2 else '⚠️ Acima',
                '✅ OK',
                '✅ OK',
                '✅ OK'
            ]
        })

        st.dataframe(
            df_performance,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("💡 Nenhuma execução disponível. Gere conteúdo na aba 'Product View' primeiro.")

# ===========================
# TAB 4: PROMPT LAB
# ===========================

with tab4:
    st.header("🧪 Prompt Laboratory")
    st.markdown("Visualize e teste os system prompts do sistema")

    # Fetch prompts from API
    prompts_data = make_api_request(api_url, "/prompts", method="GET")

    if prompts_data:
        prompts = prompts_data.get("prompts", {})

        # Display current prompts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("✍️ System Prompt - Redator")
            prompt_redator = prompts.get("redator", "Prompt não disponível")

            st.code(prompt_redator, language="markdown")

            if st.button("📋 Copy Redator Prompt", key="copy_redator"):
                st.success("✅ Prompt copiado! (funcionalidade visual)")
                # Note: Real clipboard copy requires st.components or JavaScript

        with col2:
            st.subheader("🔍 System Prompt - Revisor")
            prompt_revisor = prompts.get("revisor", "Prompt não disponível")

            st.code(prompt_revisor, language="markdown")

            if st.button("📋 Copy Revisor Prompt", key="copy_revisor"):
                st.success("✅ Prompt copiado! (funcionalidade visual)")

    else:
        st.error("❌ Não foi possível carregar os prompts do sistema")

# ===========================
# FOOTER
# ===========================

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([1, 1, 1])

with footer_col1:
    st.caption("🧠 AIOps Content Engine v2.0")

with footer_col2:
    st.caption("Powered by LangGraph & Claude Sonnet 4.6")

with footer_col3:
    st.caption("Developed by **Bruno Sousa**")

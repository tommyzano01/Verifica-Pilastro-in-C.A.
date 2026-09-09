import streamlit as st
import matplotlib.pyplot as plt
import math
import numpy as np

# Configurazione della pagina
st.set_page_config(page_title="Verifica Pilastro in C.A.", page_icon="🏗️", layout="centered")

# Intestazione personalizzata
st.markdown("""
<h2 style='color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;'>
    Verifica e Dominio M-N Pilastro in C.A.
</h2>
""", unsafe_allow_html=True)

# Creazione dei Tab per l'input dei dati
tab1, tab2 = st.tabs(["🧱 Materiali & Geometria", "⚖️ Carichi & Armature"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        fck_input = st.selectbox('Classe Cls (fck):', ['20', '25', '30', '35', '40', '45', '50'], index=1)
        fyk_input = st.selectbox('Acciaio (fyk MPa):', ['450'], index=0)
    with col2:
        b_input = st.number_input('Base b (cm):', value=30.0, step=1.0)
        h_input = st.number_input('Altezza h (cm):', value=30.0, step=1.0)

with tab2:
    col3, col4 = st.columns(2)
    with col3:
        G_input = st.number_input('Carico Perm. G (kN):', value=500.0, step=10.0)
        Q_input = st.number_input('Carico Var. Q (kN):', value=300.0, step=10.0)
        copriferro_input = st.number_input('Copriferro netto (cm):', value=3.0, step=0.5)
    with col4:
        n_bar_input = st.number_input('Num. tot. barre (pari):', value=4, min_value=2, step=2)
        phi_input = st.selectbox('Diametro ferri (mm):', ['12', '14', '16', '18', '20', '22', '24'], index=2)

st.write("") # Spazio

# Pulsante di esecuzione
if st.button("Esegui Verifica e Traccia Dominio", type="primary", use_container_width=True):
    
    # Acquisizione e conversione variabili
    b_mm, h_mm = b_input * 10, h_input * 10
    G, Q = G_input, Q_input
    fck, fyk = float(fck_input), float(fyk_input)
    n_bar = max(2, int(n_bar_input))
    if n_bar % 2 != 0: n_bar += 1
    phi, c_mm = float(phi_input), copriferro_input * 10

    d1 = c_mm + 8 + (phi / 2)
    d2 = h_mm - d1
    A_s_tot = n_bar * math.pi * (phi**2) / 4
    A_s1 = A_s2 = A_s_tot / 2

    N_Ed = 1.3 * G + 1.5 * Q
    N_Ed_N = N_Ed * 1000
    e_min = max(h_mm / 30, 20)
    M_Ed_Nmm = N_Ed_N * e_min
    M_Ed = M_Ed_Nmm / 1e6

    fcd = 0.85 * fck / 1.5
    fyd = fyk / 1.15
    Ac = b_mm * h_mm

    # --- CALCOLO DOMINIO M-N (Semplificato) ---
    M_dom, N_dom = [], []
    # Trazione semplice
    N_dom.append(-A_s_tot * fyd / 1000)
    M_dom.append(0)
    
    # Punti intermedi (variazione asse neutro x)
    x_vals = np.linspace(10, h_mm * 5, 200)
    for x in x_vals:
        eps_cu = 0.0035
        eps_s1 = eps_cu * (x - d1) / x
        eps_s2 = eps_cu * (x - d2) / x

        sig_1 = max(-fyd, min(fyd, eps_s1 * 200000))
        sig_2 = max(-fyd, min(fyd, eps_s2 * 200000))

        y = min(0.8 * x, h_mm)
        Fc = b_mm * y * fcd
        Fs1 = A_s1 * sig_1
        Fs2 = A_s2 * sig_2

        N_int = Fc + Fs1 + Fs2
        M_c = Fc * ((h_mm / 2) - (y / 2))
        M_s1 = Fs1 * ((h_mm / 2) - d1)
        M_s2 = Fs2 * ((h_mm / 2) - d2)
        M_int = M_c + M_s1 + M_s2
        
        N_dom.append(N_int / 1000)
        M_dom.append(M_int / 1e6)
        
    # Compressione semplice
    N_dom.append((Ac * fcd + A_s_tot * fyd) / 1000)
    M_dom.append(0)

    # Specchia per ottenere il dominio chiuso simmetrico
    M_dom_full = M_dom + [-m for m in reversed(M_dom)]
    N_dom_full = N_dom + list(reversed(N_dom))

    # --- VERIFICA PUNTO SPECIFICO ---
    esito, colore, bg_colore = "FALLITA", "#721c24", "#f8d7da"
    # Controllo grafico semplificato
    M_interp = np.interp(N_Ed, N_dom, M_dom) if N_Ed <= N_dom[-1] else 0
    if M_Ed <= M_interp and N_Ed <= N_dom[-1]:
        esito, colore, bg_colore = "SUPERATA", "#155724", "#d4edda"
        
    html_results = f"""
    <div style='background-color: {bg_colore}; color: {colore}; padding: 15px; border-radius: 5px; margin-top: 15px; margin-bottom: 20px;'>
        <h3 style='margin-top: 0;'>ESITO: {esito}</h3>
        <ul style='font-size: 14px; list-style-type: square;'>
            <li><b>Sforzo Normale (N<sub>Ed</sub>):</b> {N_Ed:.2f} kN</li>
            <li><b>Momento Sollecitante (M<sub>Ed</sub>):</b> {M_Ed:.2f} kNm <i>(e<sub>min</sub> = {e_min:.1f} mm)</i></li>
            <li><b>Momento Resistente (M<sub>Rd</sub> al Sforzo Normale N<sub>Ed</sub>):</b> {M_interp:.2f} kNm</li>
        </ul>
    </div>
    """
    
    st.markdown(html_results, unsafe_allow_html=True)
    
    # --- PLOT MATPLOTLIB A DUE PANNELLI ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))
    
    # Pannello 1: Sezione
    ax1.add_patch(plt.Rectangle((0, 0), b_mm, h_mm, fill=True, color='#e0e0e0', ec='black', lw=2))
    ax1.add_patch(plt.Rectangle((c_mm, c_mm), b_mm - 2*c_mm, h_mm - 2*c_mm, fill=False, ec='#2980b9', lw=1.5, ls='--'))
    n_lato = int(n_bar / 2)
    spazio_b = (b_mm - 2*c_mm - phi) / (n_lato - 1) if n_lato > 1 else 0
    for i in range(n_lato):
        cx = c_mm + phi/2 + i*spazio_b
        ax1.add_patch(plt.Circle((cx, h_mm - d1), phi/2, color='#c0392b', ec='black', lw=0.5))
        ax1.add_patch(plt.Circle((cx, d1), phi/2, color='#c0392b', ec='black', lw=0.5))
    ax1.text(b_mm / 2, -30, f"{int(b_input)} cm", ha='center', va='center', fontsize=10, style='italic')
    ax1.text(-30, h_mm / 2, f"{int(h_input)} cm", ha='center', va='center', rotation=90, fontsize=10, style='italic')
    ax1.set_xlim(-60, b_mm + 60); ax1.set_ylim(-60, h_mm + 60)
    ax1.set_aspect('equal'); ax1.axis('off'); ax1.set_title("Sezione in C.A.")

    # Pannello 2: Dominio M-N
    ax2.plot(M_dom_full, N_dom_full, 'b-', lw=2, label='Dominio Resistente')
    ax2.plot(M_Ed, N_Ed, 'ro', markersize=8, label='Punto di Progetto $(M_{Ed}, N_{Ed})$')
    ax2.fill(M_dom_full, N_dom_full, color='blue', alpha=0.1)
    ax2.axhline(0, color='black', lw=1); ax2.axvline(0, color='black', lw=1)
    ax2.set_xlabel("Momento Flettente M [kNm]"); ax2.set_ylabel("Sforzo Normale N [kN]")
    ax2.set_title("Dominio di Interazione M-N")
    ax2.grid(True, linestyle='--', alpha=0.6); ax2.legend()
    
    plt.tight_layout()
    st.pyplot(fig)

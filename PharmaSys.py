import sys, os 
import tkinter as tk
from tkinter import messagebox, filedialog
import shutil
from datetime import datetime
import locale
import tkinter.font as tkFont
from PIL import Image, ImageTk


# ---------- Paleta de cores ----------
BG_PRINCIPAL = "#1e1e1e"      # fundo geral
BG_SECUNDARIO = "#2a2a2a"    # frames
COR_BOTAO = "#3a6ea5"        # azul profissional
HOVER_BOTAO = "#4a85c5"
CLICK_BOTAO = "#2f5b8a"
TEXTO = "#ffffff"

# ---------- Configurar locale ----------
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except locale.Error:
    pass

# ---------- Função para PyInstaller ----------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

icone_path = resource_path("Image_PharmaSys.png")

# ---------- Estado de pendência ----------
pending_files = []  # Lista de tuplas: (arquivo, tipo)
todas_pastas = []
historico_movimentos = []
job_atualizacao = None

# ---------- Funções de navegação ----------
def mostrar_frame(frame):
    for f in [menu_frame, criar_pastas_frame, colar_arquivos_frame]:
        f.pack_forget()
    frame.pack(fill="both", expand=True)

def voltar_menu(frame_atual):
    frame_atual.pack_forget()
    menu_frame.pack(fill="both", expand=True)

# ---------- Botões modernos ----------
def estilo_botao_moderno(btn):
    btn.config(
        bg=COR_BOTAO,
        fg="white",
        font=("Segoe UI", 10, "bold"),
        relief="flat",
        bd=0,
        padx=10,
        pady=6,
        cursor="arrow"
    )

    def on_enter(e):
        btn.config(bg=HOVER_BOTAO, cursor="hand2")

    def on_leave(e):
        btn.config(bg=COR_BOTAO, cursor="arrow")

    def on_click(e):
        btn.config(bg=CLICK_BOTAO)

    def on_release(e):
        btn.config(bg=HOVER_BOTAO)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    btn.bind("<ButtonPress-1>", on_click)
    btn.bind("<ButtonRelease-1>", on_release)

# ---------- Criar Pastas ----------
nome_widgets = []

def proximo_entry(event, current_index):
    if current_index + 1 < len(nome_widgets):
        nome_widgets[current_index + 1][1].focus()

def atualizar_campos_nomes():
    if not messagebox.askyesno("Confirmação",
        "Tem certeza que deseja atualizar os campos? Campos atuais serão apagados se ainda não criou as pastas."):
        return
    for label, entry in nome_widgets:
        label.destroy()
        entry.destroy()
    nome_widgets.clear()
    try:
        quantidade = int(quantidade_entry.get())
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira um número válido.")
        return
    for i in range(quantidade):
        nome_label = tk.Label(frame_criar_inner, text=f"Pasta {i+1}:", bg=BG_PRINCIPAL, fg=TEXTO, font=("Arial", 10))
        nome_label.pack(pady=5)
        nome_entry = tk.Entry(frame_criar_inner, width=25, bg=BG_SECUNDARIO, fg=TEXTO, insertbackground=TEXTO)
        nome_entry.pack(pady=5)
        nome_entry.bind("<Return>", lambda e, idx=i: proximo_entry(e, idx))
        nome_widgets.append((nome_label, nome_entry))
    canvas_criar.update_idletasks()
    canvas_criar.configure(scrollregion=canvas_criar.bbox("all"))
    canvas_criar.yview_moveto(0)

def selecionar_diretorio():
    caminho = filedialog.askdirectory()
    if caminho:
        caminho_entry.delete(0, tk.END)
        caminho_entry.insert(0, caminho)

def criar_pastas():
    if not messagebox.askyesno("Confirmação", "Tem certeza que deseja criar as pastas?"):
        return
    caminho = caminho_entry.get().strip()
    if not caminho:
        messagebox.showerror("Erro", "Selecione o diretório para criar as pastas.")
        return
    os.makedirs(caminho, exist_ok=True)
    for label, entry in nome_widgets:
        nome_pasta = entry.get().strip()
        if nome_pasta:
            os.makedirs(os.path.join(caminho, nome_pasta), exist_ok=True)
    caminho_entry.delete(0, tk.END)
    quantidade_entry.delete(0, tk.END)
    for label, entry in nome_widgets:
        label.destroy()
        entry.destroy()
    nome_widgets.clear()
    canvas_criar.update_idletasks()
    canvas_criar.configure(scrollregion=canvas_criar.bbox("all"))
    canvas_criar.yview_moveto(0)
    messagebox.showinfo("Sucesso", "Pastas criadas com sucesso!")

# ---------- Colar Arquivos ----------
def selecionar_diretorio_colar():
    caminho = filedialog.askdirectory()
    if caminho:
        caminho_colar_entry.delete(0, tk.END)
        caminho_colar_entry.insert(0, caminho)
        atualizar_lista_pastas(diretorio=caminho)
        iniciar_atualizacao_ao_vivo(diretorio=caminho)

# ---------- Atualização ao vivo ----------
pastas_anteriores = set()

def atualizar_lista_pastas(diretorio):
    global todas_pastas

    try:
        pastas = sorted([
            p for p in os.listdir(diretorio)
            if os.path.isdir(os.path.join(diretorio, p))
        ])
    except Exception:
        pastas = []

    todas_pastas = pastas
    aplicar_filtro()

def aplicar_filtro():
    termo = busca_entry.get().lower()

    for widget in frame_colar_inner.winfo_children():
        widget.destroy()

    filtradas = [p for p in todas_pastas if termo in p.lower()]

    if not filtradas:
        tk.Label(frame_colar_inner, text="Nenhuma pasta encontrada.", bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=10)
    else:
        font_btn = tkFont.Font(family="Arial", size=10)
        for pasta in filtradas:
            btn = tk.Button(frame_colar_inner, text=pasta, font=font_btn,
                            anchor="w", command=lambda p=pasta: escolher_pasta(p))
            btn.pack(pady=5, fill="x")
            estilo_botao_moderno(btn)

    canvas_colar.update_idletasks()
    canvas_colar.configure(scrollregion=canvas_colar.bbox("all"))

def iniciar_atualizacao_ao_vivo(diretorio):
    global job_atualizacao

    if job_atualizacao:
        canvas_colar.after_cancel(job_atualizacao)

    def loop():
        global job_atualizacao
        atualizar_lista_pastas(diretorio)
        job_atualizacao = canvas_colar.after(2000, loop)

    loop()

# ---------- Desfazer ação ----------
def desfazer_ultima_acao():
    if not historico_movimentos:
        messagebox.showinfo("Nada para desfazer", "Nenhuma ação recente.")
        return
    
    destino, origem = historico_movimentos.pop()

    try:
        shutil.move(destino, origem)
        atualizar_botao_undo()
        messagebox.showinfo("Desfeito", "Última ação desfeita com sucesso.")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao desfazer: {e}")


# ---------- Desfazer + Contagem ----------
def atualizar_botao_undo():
    qtd = len(historico_movimentos)
    btn_undo.config(text=f"Desfazer ({qtd})")

# ---------- Preview de imagem ----------
def preview_imagem(arquivo):
    preview_confirmado = True
    if not arquivo.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
        return messagebox.askyesno("Confirmar arquivo", f"O arquivo selecionado não é imagem.\nDeseja prosseguir com:\n{os.path.basename(arquivo)}?")
    try:
        janela_preview = tk.Toplevel()
        janela_preview.title("Visualizar Imagem")
        janela_preview.state("zoomed")
        canvas = tk.Canvas(janela_preview, bg="black")
        canvas.pack(fill="both", expand=True)
        img_original = Image.open(arquivo)
        img_copy = img_original.copy()
        tk_img = ImageTk.PhotoImage(img_copy)
        canvas.image_ref = tk_img
        img_id = canvas.create_image(500, 350, image=tk_img)
        pan_data = {"x":0, "y":0, "dragging":False}

        def zoom(event):
            nonlocal tk_img, img_copy
            scale = 1.1 if event.delta > 0 else 0.9
            w, h = img_copy.size
            img_copy = img_original.resize((max(1,int(w*scale)), max(1,int(h*scale))), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(img_copy)
            canvas.image_ref = tk_img
            canvas.itemconfig(img_id, image=tk_img)

        def start_pan(event):
            pan_data["dragging"] = True
            pan_data["x"], pan_data["y"] = event.x, event.y
        def do_pan(event):
            if pan_data["dragging"]:
                dx, dy = event.x - pan_data["x"], event.y - pan_data["y"]
                canvas.move(img_id, dx, dy)
                pan_data["x"], pan_data["y"] = event.x, event.y
        def end_pan(event):
            pan_data["dragging"] = False

        def confirmar():
            nonlocal preview_confirmado
            preview_confirmado = True
            janela_preview.destroy()
        def cancelar():
            nonlocal preview_confirmado
            preview_confirmado = False
            janela_preview.destroy()

        janela_preview.protocol("WM_DELETE_WINDOW", cancelar)
        canvas.bind("<MouseWheel>", zoom)
        canvas.bind("<ButtonPress-1>", start_pan)
        canvas.bind("<B1-Motion>", do_pan)
        canvas.bind("<ButtonRelease-1>", end_pan)

        btn_frame = tk.Frame(janela_preview)
        btn_frame.pack(pady=5)
        btn_confirmar = tk.Button(btn_frame, text="Confirmar (pronto para escolher pasta)", command=confirmar)
        btn_confirmar.pack(side="left", padx=30)
        estilo_botao_moderno(btn_confirmar)
        btn_cancelar = tk.Button(btn_frame, text="Cancelar", command=cancelar)
        btn_cancelar.pack(side="right", padx=30)
        estilo_botao_moderno(btn_cancelar)
        janela_preview.grab_set()
        janela_preview.wait_window()
        return preview_confirmado
    except Exception as e:
        return messagebox.askyesno("Preview falhou", f"Não foi possível abrir preview: {e}\nDeseja prosseguir mesmo assim?")

# ---------- Adicionar Arquivos ----------
def adicionar_arquivos(tipo):
    arquivos = filedialog.askopenfilenames(title=f"Selecione os arquivos de {tipo.capitalize()}")
    if not arquivos:
        return
    diretorio = caminho_colar_entry.get().strip()
    if not diretorio:
        messagebox.showerror("Erro", "Selecione o diretório base primeiro.")
        return
    for arquivo in arquivos:
        confirmado = preview_imagem(arquivo)
        if confirmado and (arquivo, tipo) not in pending_files:
            pending_files.append((arquivo, tipo))
    atualizar_label_pendencia()
    atualizar_lista_pastas(diretorio)

def atualizar_label_pendencia():
    if not pending_files:
        pending_label.config(text="Nenhum arquivo pendente.")
    else:
        texto = "Pendentes:\n"
        for f, t in pending_files:
            texto += f"{t.upper()} -> {os.path.basename(f)}\n"
        pending_label.config(text=texto)

def limpar_pendencia():
    pending_files.clear()
    atualizar_label_pendencia()

def escolher_pasta(nome_pasta):
    if not pending_files:
        messagebox.showwarning("Sem arquivo", "Nenhum arquivo pendente.")
        return
    diretorio = caminho_colar_entry.get().strip()
    if not diretorio:
        messagebox.showerror("Erro", "Selecione o diretório base primeiro.")
        return
    for arquivo, tipo in pending_files.copy():
        pasta_destino = os.path.join(diretorio, nome_pasta)
        os.makedirs(pasta_destino, exist_ok=True)
        extensao = os.path.splitext(arquivo)[1]
        if tipo == 'receita':
            nome_base = "Receita"
        else:
            meses_pt = ["Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                        "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
            data_atual = datetime.now()
            mes_capitalizado = meses_pt[data_atual.month - 1]
            ano = data_atual.year
            nome_base = f"{mes_capitalizado} {ano}"
        nome_arquivo = f"{nome_base}{extensao}"
        destino_final = os.path.join(pasta_destino, nome_arquivo)
        contador = 1
        while os.path.exists(destino_final):
            nome_arquivo = f"{nome_base} ({contador}){extensao}"
            destino_final = os.path.join(pasta_destino, nome_arquivo)
            contador += 1
        try:
            shutil.move(arquivo, destino_final)
            historico_movimentos.append((destino_final, arquivo))
            atualizar_botao_undo()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao mover arquivo {arquivo}: {e}")
        pending_files.remove((arquivo, tipo))
    atualizar_label_pendencia()
    atualizar_lista_pastas(diretorio)
    messagebox.showinfo("Sucesso", f"Arquivos movidos para a pasta {nome_pasta}.")

# ---------- Scroll ----------
def scroll_criar(event):
    canvas_criar.yview_scroll(int(-1*(event.delta/120)), "units")
def centralizar_criar(event):
    canvas_criar.itemconfig(frame_criar_inner_id, width=canvas_criar.winfo_width())

def scroll_colar(event):
    canvas_colar.yview_scroll(int(-1*(event.delta/120)), "units")
def centralizar_colar(event):
    canvas_colar.itemconfig(frame_colar_inner_id, width=canvas_colar.winfo_width())
    canvas_colar.update_idletasks()
    canvas_colar.configure(scrollregion=canvas_colar.bbox("all"))
    

# ---------- Função "Informações do Sistema" ----------
def mostrar_info():
    info_texto = (
        "💻 Criado por: Leonardo Davi\n"
        "📱 Telefone: 35 98425-0721\n"
        "✉️ Email: leonardodavioliveiraguiar@gmail.com\n"
        "🛠️ Ferramentas usadas: Python, Tkinter, PIL (Pillow)\n"
        "🆚 Versão do sistema: 6.0\n\n"
        "📌 Suporte:\n"
        "Qualquer dúvida ou problema, entre em contato via telefone ou email.\n"
    )

    janela_info = tk.Toplevel()
    janela_info.title("Informações do Sistema")
    janela_info.configure(bg=BG_PRINCIPAL)

    largura_janela = 450
    altura_janela = 300
    largura_tela = janela_info.winfo_screenwidth()
    altura_tela = janela_info.winfo_screenheight()
    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2
    janela_info.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    janela_info.resizable(False, False)

    tk.Label(janela_info, text=info_texto, bg=BG_PRINCIPAL, fg=TEXTO, justify="left", anchor="nw", wraplength=400, font=("Arial", 10)).pack(
        fill="both", expand=True, padx=10, pady=10
    )

    btn_ok = tk.Button(janela_info, text="OK", command=janela_info.destroy)
    btn_ok.pack(pady=10)
    estilo_botao_moderno(btn_ok)
    janela_info.grab_set()

# ---------- Como Usar ----------

def mostrar_como_usar():
    texto_uso = (
        "🚀 PharmaSys\n"
        "Sistema inteligente para organização de arquivos farmacêuticos\n\n"

        "🗂️ CRIAR PASTAS\n"
        "Crie várias pastas de uma vez:\n"
        "• Selecione o diretório\n"
        "• Defina a quantidade\n"
        "• Nomeie e confirme\n"
        "✔ Ideal para agilizar organização em lote\n\n"

        "📥 COLAR ARQUIVOS\n"
        "Mova arquivos para as pastas corretas:\n"
        "• Escolha o diretório base\n"
        "• Selecione Receitas ou Notas\n"
        "• Visualize antes de mover\n"
        "• Clique na pasta desejada\n"
        "✔ Evita erros e perda de arquivos\n\n"

        "🔙 NAVEGAÇÃO\n"
        "Use 'Voltar ao Menu' para retornar a qualquer momento\n\n"

        "⚠️ IMPORTANTE\n"
        "• Revise antes de confirmar ações\n"
        "• Nomes duplicados são ajustados automaticamente\n"
        "• Use sempre o diretório correto\n"
    )

    # Criar janela
    janela_uso = tk.Toplevel()
    janela_uso.title("Como Usar")
    janela_uso.configure(bg=BG_PRINCIPAL)

    # Centralizar a janela
    largura_janela = 650
    altura_janela = 550
    largura_tela = janela_uso.winfo_screenwidth()
    altura_tela = janela_uso.winfo_screenheight()
    pos_x = (largura_tela - largura_janela) // 2
    pos_y = (altura_tela - altura_janela) // 2
    janela_uso.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
    janela_uso.resizable(False, False)

    # Frame principal com scroll
    frame_principal = tk.Frame(janela_uso, bg=BG_PRINCIPAL)
    frame_principal.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(frame_principal, bg=BG_PRINCIPAL, highlightthickness=0)
    scrollbar = tk.Scrollbar(frame_principal, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas, bg=BG_PRINCIPAL)

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0,0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Label do texto
    tk.Label(scroll_frame, text=texto_uso, bg=BG_PRINCIPAL, fg=TEXTO, justify="left", anchor="nw", wraplength=600).pack(
        fill="both", expand=True, padx=5, pady=5
    )

    # Botão OK
    btn_ok = tk.Button(janela_uso, text="OK", command=janela_uso.destroy)
    btn_ok.pack(pady=10)
    estilo_botao_moderno(btn_ok)

    janela_uso.grab_set()

# ---------- Janela ----------
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

janela = tk.Tk()
janela.title("PharmaSys")
janela.iconbitmap(resource_path("Icon_PharmaSys256x256.ico"))
largura_janela = 600
altura_janela = 700
janela.update_idletasks()
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
pos_x = (largura_tela // 2) - (largura_janela // 2)
pos_y = (altura_tela // 2) - (altura_janela // 2)
janela.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
janela.configure(bg=BG_PRINCIPAL)
janela.resizable(False, False)

# ---------- Menu ----------
menu_frame = tk.Frame(janela, bg=BG_PRINCIPAL)
menu_frame.pack(fill="both", expand=True)

if os.path.exists(icone_path):
    try:
        img = Image.open(icone_path)
        img = img.resize((400, 150), Image.Resampling.LANCZOS)
        icone_img = ImageTk.PhotoImage(img)
        tk.Label(menu_frame, image=icone_img, bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=80)
    except Exception:
        icone_img = tk.PhotoImage(file=icone_path)
        tk.Label(menu_frame, image=icone_img, bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=10)

btn_criar = tk.Button(menu_frame, text="CRIAR PASTAS", width=20, command=lambda: mostrar_frame(criar_pastas_frame))
btn_criar.pack(pady=10)
estilo_botao_moderno(btn_criar)

btn_colar = tk.Button(menu_frame, text="COLAR ARQUIVOS", width=20, command=lambda: mostrar_frame(colar_arquivos_frame))
btn_colar.pack(pady=10)
estilo_botao_moderno(btn_colar)

btn_como_usar = tk.Button(menu_frame, text="COMO USAR", width=20, command=mostrar_como_usar)
btn_como_usar.pack(pady=10)
estilo_botao_moderno(btn_como_usar)

btn_info = tk.Button(menu_frame, text="INFO SISTEMA", width=20, command=mostrar_info)
btn_info.pack(pady=10)
estilo_botao_moderno(btn_info)


# ---------- Criar Pastas Frame ----------
criar_pastas_frame = tk.Frame(janela, bg=BG_PRINCIPAL)
frame_criar_top = tk.Frame(criar_pastas_frame, bg=BG_PRINCIPAL)
frame_criar_top.pack(pady=5)

tk.Label(frame_criar_top, text="Diretório:", bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=5)
caminho_entry = tk.Entry(frame_criar_top, width=50, bg=BG_SECUNDARIO, fg=TEXTO, insertbackground=TEXTO)
caminho_entry.pack(pady=5)
btn_sel_dir = tk.Button(frame_criar_top, text="Selecionar Diretório", command=selecionar_diretorio)
btn_sel_dir.pack(pady=5)
estilo_botao_moderno(btn_sel_dir)

tk.Label(frame_criar_top, text="Quantidade de pastas:", bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=5)
quantidade_entry = tk.Entry(frame_criar_top, width=8, bg=BG_SECUNDARIO, fg=TEXTO, insertbackground=TEXTO)
quantidade_entry.pack(pady=5)

btn_atualizar = tk.Button(frame_criar_top, text="Atualizar Campos", command=atualizar_campos_nomes)
btn_atualizar.pack(pady=5)
estilo_botao_moderno(btn_atualizar)

btn_criar_pastas = tk.Button(frame_criar_top, text="Criar Pastas", command=criar_pastas)
btn_criar_pastas.pack(pady=5)
estilo_botao_moderno(btn_criar_pastas)

btn_voltar_menu_criar = tk.Button(frame_criar_top, text="Voltar ao Menu", command=lambda: voltar_menu(criar_pastas_frame))
btn_voltar_menu_criar.pack(pady=5)
estilo_botao_moderno(btn_voltar_menu_criar)

frame_criar_scroll = tk.Frame(criar_pastas_frame, bg=BG_PRINCIPAL)
frame_criar_scroll.pack(fill="both", expand=True)
canvas_criar = tk.Canvas(frame_criar_scroll, bg=BG_PRINCIPAL, highlightthickness=0)
canvas_criar.pack(fill="both", expand=True, side="left")
scrollbar_criar = tk.Scrollbar(frame_criar_scroll, orient="vertical", command=canvas_criar.yview)
scrollbar_criar.pack(side="right", fill="y")
canvas_criar.configure(yscrollcommand=scrollbar_criar.set)
frame_criar_inner = tk.Frame(canvas_criar, bg=BG_PRINCIPAL)
frame_criar_inner_id = canvas_criar.create_window((0,0), window=frame_criar_inner, anchor="nw")
tk.Frame(frame_criar_inner, height=10, bg=BG_PRINCIPAL).pack()
canvas_criar.bind("<Enter>", lambda e: canvas_criar.bind_all("<MouseWheel>", scroll_criar))
canvas_criar.bind("<Leave>", lambda e: canvas_criar.unbind_all("<MouseWheel>"))
canvas_criar.bind("<Configure>", centralizar_criar)

# ---------- Colar Arquivos Frame ----------
colar_arquivos_frame = tk.Frame(janela, bg=BG_PRINCIPAL)
tk.Label(colar_arquivos_frame, text="Diretório base:", bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=5)
caminho_colar_entry = tk.Entry(colar_arquivos_frame, width=50, bg=BG_SECUNDARIO, fg=TEXTO, insertbackground=TEXTO)
caminho_colar_entry.pack(pady=5)
btn_sel_dir_colar = tk.Button(colar_arquivos_frame, text="Selecionar Diretório", command=selecionar_diretorio_colar)
btn_sel_dir_colar.pack(pady=5)
tk.Label(colar_arquivos_frame, text="Pesquisar pasta:", bg=BG_PRINCIPAL, fg=TEXTO).pack(pady=2)
busca_entry = tk.Entry(colar_arquivos_frame, width=40, bg=BG_SECUNDARIO, fg=TEXTO, insertbackground=TEXTO)
busca_entry.pack(pady=5)
busca_entry.bind("<KeyRelease>", lambda e: aplicar_filtro())
estilo_botao_moderno(btn_sel_dir_colar)

frame_colar_scroll = tk.Frame(colar_arquivos_frame, bg=BG_PRINCIPAL, height=220)
frame_colar_scroll.pack(fill="both", expand=True, padx=10, pady=5)
canvas_colar = tk.Canvas(frame_colar_scroll, bg=BG_PRINCIPAL, highlightthickness=0, height=220)
canvas_colar.pack(side="left", fill="both", expand=True)
scrollbar_colar = tk.Scrollbar(frame_colar_scroll, orient="vertical", command=canvas_colar.yview)
scrollbar_colar.pack(side="right", fill="y")
canvas_colar.configure(yscrollcommand=scrollbar_colar.set)
frame_colar_inner = tk.Frame(canvas_colar, bg=BG_PRINCIPAL)
frame_colar_inner_id = canvas_colar.create_window((0,0), window=frame_colar_inner, anchor="nw")
tk.Frame(frame_colar_inner, height=10, bg=BG_PRINCIPAL).pack()
canvas_colar.bind("<Enter>", lambda e: canvas_colar.bind_all("<MouseWheel>", scroll_colar))
canvas_colar.bind("<Leave>", lambda e: canvas_colar.unbind_all("<MouseWheel>"))
canvas_colar.bind("<Configure>", centralizar_colar)

frame_botoes = tk.Frame(colar_arquivos_frame, bg=BG_PRINCIPAL)
frame_botoes.pack(pady=10, fill="x")
frame_botoes.columnconfigure(0, weight=1)
frame_botoes.columnconfigure(1, weight=1)

btn_colar_receita = tk.Button(frame_botoes, text="Colar Receitas", width=25, command=lambda: adicionar_arquivos('receita'))
btn_colar_receita.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
estilo_botao_moderno(btn_colar_receita)

btn_colar_notas = tk.Button(frame_botoes, text="Colar Notas", width=25, command=lambda: adicionar_arquivos('nota'))
btn_colar_notas.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
estilo_botao_moderno(btn_colar_notas)

btn_limpar = tk.Button(frame_botoes, text="Limpar Pendência", width=25, command=limpar_pendencia)
btn_limpar.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
estilo_botao_moderno(btn_limpar)

btn_undo = tk.Button(frame_botoes, text="Desfazer Ação (0)", width=25, command=desfazer_ultima_acao)
btn_undo.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
estilo_botao_moderno(btn_undo)

# ---------- Área de pendentes com scroll ----------
frame_pendentes = tk.Frame(colar_arquivos_frame, bg=BG_PRINCIPAL)
frame_pendentes.pack(fill="x", padx=10, pady=5)

canvas_pendentes = tk.Canvas(frame_pendentes, bg=BG_SECUNDARIO, height=120, highlightthickness=0)
canvas_pendentes.pack(side="left", fill="both", expand=True)

scrollbar_pendentes = tk.Scrollbar(frame_pendentes, orient="vertical", command=canvas_pendentes.yview)
scrollbar_pendentes.pack(side="right", fill="y")

canvas_pendentes.configure(yscrollcommand=scrollbar_pendentes.set)

frame_pendentes_inner = tk.Frame(canvas_pendentes, bg=BG_SECUNDARIO)
canvas_pendentes.create_window((0, 0), window=frame_pendentes_inner, anchor="nw")

def atualizar_scroll_pendentes(event):
    canvas_pendentes.configure(scrollregion=canvas_pendentes.bbox("all"))

frame_pendentes_inner.bind("<Configure>", atualizar_scroll_pendentes)

def scroll_pendentes(event):
    canvas_pendentes.yview_scroll(int(-1*(event.delta/120)), "units")

canvas_pendentes.bind("<Enter>", lambda e: canvas_pendentes.bind_all("<MouseWheel>", scroll_pendentes))
canvas_pendentes.bind("<Leave>", lambda e: canvas_pendentes.unbind_all("<MouseWheel>"))

# Label dentro do scroll
pending_label = tk.Label(
    frame_pendentes_inner,
    text="Nenhum arquivo pendente.",
    bg=BG_SECUNDARIO,
    fg=TEXTO,
    justify="left",
    anchor="nw"
)
pending_label.pack(fill="both", expand=True, padx=5, pady=5)

btn_voltar_menu_colar = tk.Button(colar_arquivos_frame, text="Voltar ao Menu", command=lambda: voltar_menu(colar_arquivos_frame))
btn_voltar_menu_colar.pack(pady=0)
estilo_botao_moderno(btn_voltar_menu_colar)

# ---------- Rodapé ----------  
tk.Label(janela, text="Desenvolvido por Leonardo Aguiar • 2024–2026 • Versão 7.0",
         bg=BG_PRINCIPAL, fg=TEXTO, font=("Arial", 8)).pack(side="bottom", fill="x", pady=10)

# ---------- Iniciar com menu ----------
menu_frame.pack(fill="both", expand=True)
janela.mainloop()

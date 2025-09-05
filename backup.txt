from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox
from db import get_ativos_collection, get_espera_collection

# -------------------------------
# CONFIGURAÇÕES
# -------------------------------
MAX_ASSENTOS = 2
DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex"]

ativos_col = get_ativos_collection()
espera_col = get_espera_collection()

# -------------------------------
# FUNÇÕES DO BANCO
# -------------------------------
def adicionar_espera(nome, dias, data_adicao):
    dias_str = ",".join(dias)
    espera_col.insert_one({
        "nome": nome,
        "dias": dias_str,
        "data_adicao": data_adicao
    })

def adicionar_ativo(nome, dias):
    dias_str = ",".join(dias)
    ativos_col.insert_one({
        "nome": nome,
        "dias": dias_str
    })

def vagas_por_dia():
    todos = list(ativos_col.find({}, {"dias": 1, "_id": 0}))
    vagas = {}
    for dia in DIAS_SEMANA:
        ocupados = sum(dia in a["dias"].split(",") for a in todos)
        vagas[dia] = MAX_ASSENTOS - ocupados
    return vagas

# -------------------------------
# FUNÇÕES DE REALOCAÇÃO/REMOÇÃO
# -------------------------------
def realocar_selecionado():
    selecionado = tabela_espera.selection()
    if not selecionado:
        messagebox.showwarning("Erro", "Selecione um aluno na lista de espera para realocar.")
        return

    aluno_item = tabela_espera.item(selecionado)
    nome = aluno_item['values'][1]
    dias_str = aluno_item['values'][2]
    aluno_dias = dias_str.split(",")

    vagas = vagas_por_dia()

    dias_sem_vaga = []
    for dia in DIAS_SEMANA:
        if dia in aluno_dias:
            if vagas[dia] > 0:
                ativo = ativos_col.find_one({"nome": nome})
                if ativo:
                    dias_ativos = ativo["dias"].split(",")
                    if dia not in dias_ativos:
                        dias_ativos.append(dia)
                        dias_ativos.sort(key=lambda d: DIAS_SEMANA.index(d))
                        ativos_col.update_one({"nome": nome}, {"$set": {"dias": ",".join(dias_ativos)}})
                else:
                    ativos_col.insert_one({"nome": nome, "dias": dia})
                aluno_dias.remove(dia)
            else:
                dias_sem_vaga.append(dia)

    if dias_sem_vaga:
        messagebox.showwarning("Vagas Cheias", f"Não foi possível realocar {nome} nos dias: {', '.join(dias_sem_vaga)}.")

    # Atualiza lista de espera
    if aluno_dias:
        espera_col.update_one({"nome": nome}, {"$set": {"dias": ",".join(aluno_dias)}})
    else:
        espera_col.delete_one({"nome": nome})

    atualizar_tabelas()

def remover_ativo():
    selecionado = tabela_ativos.selection()
    if not selecionado:
        messagebox.showwarning("Erro", "Selecione um aluno ativo para remover.")
        return

    aluno_item = tabela_ativos.item(selecionado)
    nome = aluno_item['values'][0]

    ativos_col.delete_one({"nome": nome})
    atualizar_tabelas()

# -------------------------------
# INTERFACE - FUNÇÕES
# -------------------------------
def atualizar_tabelas():
    for i in tabela_ativos.get_children():
        tabela_ativos.delete(i)
    for i in tabela_espera.get_children():
        tabela_espera.delete(i)

    for ativo in ativos_col.find():
        tabela_ativos.insert("", "end", values=(ativo["nome"], ativo["dias"]))

    lista = espera_col.find().sort("data_adicao", 1)
    for pos, aluno in enumerate(lista, start=1):
        tabela_espera.insert("", "end", values=(pos, aluno["nome"], aluno["dias"], aluno["data_adicao"]))

def adicionar_na_espera_gui():
    nome = entrada_nome.get()
    dias = [dia for dia, var in checkboxes_dias.items() if var.get()]
    data_adicao = entrada_data.get()
    if not nome or not dias or not data_adicao:
        messagebox.showwarning("Erro", "Preencha o nome, dias e data.")
        return
    adicionar_espera(nome, dias, data_adicao)
    entrada_nome.delete(0, tk.END)
    entrada_data.delete(0, tk.END)
    for var in checkboxes_dias.values():
        var.set(False)
    atualizar_tabelas()

def atualizar_dias_ativos():
    selecionado = tabela_ativos.selection()
    if not selecionado:
        messagebox.showwarning("Erro", "Selecione um aluno ativo para atualizar os dias.")
        return
    aluno_item = tabela_ativos.item(selecionado)
    nome = aluno_item['values'][0]

    top = tk.Toplevel()
    top.title(f"Atualizar dias de {nome}")
    vars_dias = {}
    for dia in DIAS_SEMANA:
        var = tk.BooleanVar()
        if dia in aluno_item['values'][1].split(","):
            var.set(True)
        chk = tk.Checkbutton(top, text=dia, variable=var)
        chk.pack(side="left", padx=5, pady=5)
        vars_dias[dia] = var

    def salvar():
        novos_dias = [d for d, v in vars_dias.items() if v.get()]
        if not novos_dias:
            messagebox.showwarning("Erro", "Selecione ao menos um dia.")
            return
        ativos_col.update_one({"nome": nome}, {"$set": {"dias": ",".join(novos_dias)}})
        top.destroy()
        atualizar_tabelas()

    tk.Button(top, text="Salvar", command=salvar).pack(pady=10)

# -------------------------------
# VISUALIZAÇÃO DO ÔNIBUS
# -------------------------------
def mostrar_onibus(dia):
    for widget in frame_onibus.winfo_children():
        widget.destroy()

    ativos = list(ativos_col.find())
    ocupados = []
    for ativo in ativos:
        if dia in ativo["dias"].split(","):
            ocupados.append(ativo["nome"])

    for i in range(MAX_ASSENTOS):
        if i < len(ocupados):
            btn = tk.Button(frame_onibus, text=ocupados[i], bg="red", fg="white", width=10, height=2)
        else:
            btn = tk.Button(frame_onibus, text=f"Vazio {i+1}", bg="green", fg="black", width=10, height=2)
        btn.grid(row=i//4, column=i%4, padx=5, pady=5)

# -------------------------------
# INTERFACE PRINCIPAL
# -------------------------------
janela = tk.Tk()
janela.title("Gerenciamento de Transporte - Faculdade")
janela.geometry("1000x700")

notebook = ttk.Notebook(janela)
notebook.pack(fill="both", expand=True)

# --- Aba Gerenciamento ---
aba_gerenciamento = tk.Frame(notebook)
notebook.add(aba_gerenciamento, text="Gerenciamento")

tk.Label(aba_gerenciamento, text="Nome do aluno:").pack()
entrada_nome = tk.Entry(aba_gerenciamento, width=30)
entrada_nome.pack()

tk.Label(aba_gerenciamento, text="Data de Adição (DD/MM/AAAA):").pack()
entrada_data = tk.Entry(aba_gerenciamento, width=15)
entrada_data.pack()

frame_dias = tk.Frame(aba_gerenciamento)
frame_dias.pack()
checkboxes_dias = {}
for dia in DIAS_SEMANA:
    var = tk.BooleanVar()
    chk = tk.Checkbutton(frame_dias, text=dia, variable=var)
    chk.pack(side="left")
    checkboxes_dias[dia] = var

frame_botoes = tk.Frame(aba_gerenciamento)
frame_botoes.pack(pady=10)
tk.Button(frame_botoes, text="Adicionar à Espera", command=adicionar_na_espera_gui).pack(side="left", padx=5)
tk.Button(frame_botoes, text="Realocar Selecionado", command=realocar_selecionado).pack(side="left", padx=5)
tk.Button(frame_botoes, text="Formou", command=remover_ativo).pack(side="left", padx=5)
tk.Button(frame_botoes, text="Atualizar Dias", command=atualizar_dias_ativos).pack(side="left", padx=5)

tk.Label(aba_gerenciamento, text="Alunos Ativos").pack()
tabela_ativos = ttk.Treeview(aba_gerenciamento, columns=("Nome", "Dias"), show="headings")
tabela_ativos.heading("Nome", text="Nome")
tabela_ativos.heading("Dias", text="Dias")
tabela_ativos.pack(pady=10, fill="x")

tk.Label(aba_gerenciamento, text="Lista de Espera").pack()
tabela_espera = ttk.Treeview(aba_gerenciamento, columns=("Pos", "Nome", "Dias", "Data"), show="headings")
tabela_espera.heading("Pos", text="Nº")
tabela_espera.heading("Nome", text="Nome")
tabela_espera.heading("Dias", text="Dias")
tabela_espera.heading("Data", text="Data")
tabela_espera.pack(pady=10, fill="x")

# --- Aba Ônibus ---
aba_onibus = tk.Frame(notebook)
notebook.add(aba_onibus, text="Ônibus")

tk.Label(aba_onibus, text="Visualização das Poltronas").pack()
frame_botoes_dias = tk.Frame(aba_onibus)
frame_botoes_dias.pack()
for dia in DIAS_SEMANA:
    tk.Button(frame_botoes_dias, text=dia, command=lambda d=dia: mostrar_onibus(d)).pack(side="left", padx=5)

container_onibus = tk.Frame(aba_onibus)
container_onibus.pack(pady=20, fill="both", expand=True)
canvas = tk.Canvas(container_onibus)
scrollbar_y = tk.Scrollbar(container_onibus, orient="vertical", command=canvas.yview)
scrollbar_x = tk.Scrollbar(container_onibus, orient="horizontal", command=canvas.xview)
canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
scrollbar_y.pack(side="right", fill="y")
scrollbar_x.pack(side="bottom", fill="x")
canvas.pack(side="left", fill="both", expand=True)
frame_onibus = tk.Frame(canvas)
canvas.create_window((0, 0), window=frame_onibus, anchor="nw")
frame_onibus.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

# -------------------------------
# INICIALIZAÇÃO
# -------------------------------
atualizar_tabelas()
janela.mainloop()

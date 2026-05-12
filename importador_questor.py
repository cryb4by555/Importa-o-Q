import os
import re
import pdfplumber
from datetime import datetime

# =========================================================
# CONFIGURAÇÕES
# =========================================================

PASTA = "."

BANCO_ID = "085"
AGENCIA = "0101"
CONTA = "9838112"

# =========================================================
# REGEX DO PDF
# =========================================================

PADRAO = re.compile(
    r"^(\d{2}/\d{2}/\d{4})\s+"
    r"(.+?)\s+"
    r"([\d\.\-]+)\s+"
    r"(-?[\d\.\,]+)\s+"
    r"([\d\.\,]+)$"
)

# =========================================================
# FUNÇÕES
# =========================================================

def converter_numero(valor):

    valor = valor.replace(".", "")
    valor = valor.replace(",", ".")

    return float(valor)


def limpar_documento(documento):

    return re.sub(r"\D", "", documento)


def formatar_data_ofx(data_br):

    data = datetime.strptime(data_br, "%d/%m/%Y")

    return data.strftime("%Y%m%d")


def linha_valida(linha):

    ignorar = [
        "EXTRATO",
        "Período",
        "Emitido em",
        "Nome:",
        "Cooperativa:",
        "DATA DESCRIÇÃO",
        "SALDO ANTERIOR",
        "TOTAL",
        "SAC -",
        "OUVIDORIA",
        "Os dados acima"
    ]

    for item in ignorar:

        if item in linha:
            return False

    return True

# =========================================================
# BUSCAR PDFs
# =========================================================

arquivos_pdf = [
    f for f in os.listdir(PASTA)
    if f.lower().endswith(".pdf")
]

# =========================================================
# PROCESSAR PDFs
# =========================================================

for arquivo_pdf in arquivos_pdf:

    print("=" * 60)
    print(f"PROCESSANDO: {arquivo_pdf}")
    print("=" * 60)

    nome_base = os.path.splitext(arquivo_pdf)[0]

    arquivo_ofx = f"{nome_base}.ofx"

    transacoes = []

    # =====================================================
    # LEITURA PDF
    # =====================================================

    with pdfplumber.open(arquivo_pdf) as pdf:

        for pagina in pdf.pages:

            texto = pagina.extract_text()

            if not texto:
                continue

            linhas = texto.split("\n")

            for linha in linhas:

                linha = linha.strip()

                if not linha_valida(linha):
                    continue

                resultado = PADRAO.search(linha)

                if resultado:

                    data = resultado.group(1).strip()
                    descricao = resultado.group(2).strip()
                    documento = resultado.group(3).strip()
                    valor = resultado.group(4).strip()

                    valor_float = converter_numero(valor)

                    tipo = "DEBIT"

                    if valor_float > 0:
                        tipo = "CREDIT"

                    transacoes.append({
                        "data": formatar_data_ofx(data),
                        "descricao": descricao,
                        "documento": limpar_documento(documento),
                        "valor": valor_float,
                        "tipo": tipo
                    })

    # =====================================================
    # CABEÇALHO OFX
    # =====================================================

    agora = datetime.now().strftime("%Y%m%d%H%M%S")

    ofx = f"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1>
<SONRS>
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<DTSERVER>{agora}
<LANGUAGE>POR
</SONRS>
</SIGNONMSGSRSV1>

<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1

<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>

<STMTRS>
<CURDEF>BRL

<BANKACCTFROM>
<BANKID>{BANCO_ID}
<BRANCHID>{AGENCIA}
<ACCTID>{CONTA}
<ACCTTYPE>CHECKING
</BANKACCTFROM>

<BANKTRANLIST>
"""

    # =====================================================
    # TRANSAÇÕES
    # =====================================================

    for t in transacoes:

        ofx += f"""
<STMTTRN>
<TRNTYPE>{t['tipo']}
<DTPOSTED>{t['data']}
<TRNAMT>{t['valor']}
<FITID>{t['documento']}
<CHECKNUM>{t['documento']}
<MEMO>{t['descricao']}
</STMTTRN>
"""

    # =====================================================
    # FINAL OFX
    # =====================================================

    ofx += """
</BANKTRANLIST>

<LEDGERBAL>
<BALAMT>0.00
<DTASOF>20260430000000
</LEDGERBAL>

</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""

    # =====================================================
    # SALVAR OFX
    # =====================================================

    with open(arquivo_ofx, "w", encoding="utf-8") as arquivo:

        arquivo.write(ofx)

    # =====================================================
    # RESULTADO
    # =====================================================

    print(f"OFX GERADO: {arquivo_ofx}")
    print(f"TOTAL TRANSAÇÕES: {len(transacoes)}")

# =========================================================
# FINAL
# =========================================================

print("\n")
print("=" * 60)
print("PROCESSAMENTO FINALIZADO")
print("=" * 60)
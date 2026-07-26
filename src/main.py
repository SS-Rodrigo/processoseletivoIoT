from machine import ADC, Pin
import math
import time

LDR_PIN = 34
BUTTON_PIN = 25

LUX_BLOQUEADO = 100
LUX_LIVRE = 500

MICRO_PARADA_MS = 5000

DEBOUNCE_MS = 50

GAMMA = 0.7
RL10 = 50

ldr = ADC(Pin(LDR_PIN))
ldr.atten(ADC.ATTN_11DB)

botao = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)

total_pecas = 0

sensor_bloqueado = False
inicio_bloqueio = None
micro_parada_reportada = False

ultimo_estado_lido_botao = botao.value()
estado_estavel_botao = ultimo_estado_lido_botao
momento_ultima_mudanca_botao = time.ticks_ms()

def ler_lux():
    # Lê o valor analógico do sensor e converte aproximadamente para lux.
    leitura = ldr.read()

    if leitura <= 0:
        return 100000.0

    if leitura >= 4095:
        leitura = 4094

    # Como o LDR está alimentado em 3,3 V, convertemos a leitura para tensão.
    tensao = leitura / 4095.0 * 3.3

    # Resistência aproximada do fotoresistor no divisor de tensão
    resistencia = 2000.0 * tensao / (3.3 - tensao)

    if resistencia <= 0:
        return 100000.0

    # Conversão aproximada de resistência para lux
    lux = math.pow(
        RL10 * 1000.0 * math.pow(10.0, GAMMA) / resistencia,
        1.0 / GAMMA
    )

    return lux

def resetar_turno():
    global total_pecas
    global sensor_bloqueado
    global inicio_bloqueio
    global micro_parada_reportada

    total_pecas = 0
    sensor_bloqueado = False
    inicio_bloqueio = None
    micro_parada_reportada = False

    print("Turno resetado com sucesso. Contadores zerados.")

def verificar_botao():
    """
    Realiza a leitura do botão com debounce.

    Como o botão usa PULL_UP:
    1 = solto
    0 = pressionado
    """
    global ultimo_estado_lido_botao
    global estado_estavel_botao
    global momento_ultima_mudanca_botao

    agora = time.ticks_ms()
    leitura_atual = botao.value()

    if leitura_atual != ultimo_estado_lido_botao:
        ultimo_estado_lido_botao = leitura_atual
        momento_ultima_mudanca_botao = agora

    tempo_estavel = time.ticks_diff(
        agora,
        momento_ultima_mudanca_botao
    )

    if tempo_estavel >= DEBOUNCE_MS:
        if leitura_atual != estado_estavel_botao:
            estado_estavel_botao = leitura_atual

            # Executa o reset somente na transição para pressionado
            if estado_estavel_botao == 0:
                resetar_turno()

def verificar_sensor():
    #Detecta a passsagem das peças e as micro-paradas.

    global total_pecas
    global sensor_bloqueado
    global inicio_bloqueio
    global micro_parada_reportada

    agora = time.ticks_ms()
    lux = ler_lux()

    # Transição: linha livre para sensor bloqueado
    if not sensor_bloqueado and lux < LUX_BLOQUEADO:
        sensor_bloqueado = True
        inicio_bloqueio = agora
        micro_parada_reportada = False
    elif sensor_bloqueado and lux < LUX_BLOQUEADO: # Sensor continua bloqueado
        if inicio_bloqueio is not None:
            tempo_bloqueado = time.ticks_diff(agora, inicio_bloqueio)

            if (tempo_bloqueado > MICRO_PARADA_MS and not micro_parada_reportada):
                print("Alerta: Micro-parada detectada!")
                micro_parada_reportada = True
    elif sensor_bloqueado and lux > LUX_LIVRE: # Transição: sensor bloqueado -> linha livre
        total_pecas += 1

        print("Peca detectada! Total: {}".format(total_pecas))

        sensor_bloqueado = False
        inicio_bloqueio = None
        micro_parada_reportada = False

# Programa principal
print("Sistema Kanban Inicializado")
print("Contador de Producao Inicializado")

while True:
    verificar_sensor()
    verificar_botao()
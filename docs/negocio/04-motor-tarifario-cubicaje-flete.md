# Reglas de Negocio: Motor Tarifario, Cubicaje Volumétrico y Fletes

> **Módulo:** Motor de Cotización y Finanzas  
> **Prefijo de Reglas:** `BR-TAR` (Business Rules - Tarifario)  
> **Servicio Responsable:** [`app/services/publico_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/publico_service.py) & [`app/services/envio_service.py`](file:///c:/Users/User/Documents/VSC-Integrador/CargaExpressBackend/app/services/envio_service.py)  
> **Moneda:** Soles Peruanos (`PEN` / `S/`)  
> **Estado:** 💰 **REGLA DE NEGOCIO VIGENTE Y DE OBLIGATORIO CUMPLIMIENTO**

---

## 1. Justificación del Modelo Volumétrico

En el transporte de carga interprovincial, el espacio disponible en la bodega del camión es un recurso crítico y finito. Un paquete muy liviano pero voluminoso (por ejemplo, una caja grande de plumavit o peluches) ocupa el espacio que de otro modo albergaría mercancía más pesada. 

Por ello, la empresa aplica el estándar internacional de la **IATA / MTC**, calculando tanto el **peso físico** como el **peso volumétrico**, cobrando sobre el mayor de ambos (**peso liquidable o facturable**).

---

## 2. Fórmulas Oficiales de Cálculo

### 2.1. Fórmula del Peso Volumétrico
$$\text{Peso Volumétrico (kg)} = \frac{\text{Largo (cm)} \times \text{Ancho (cm)} \times \text{Alto (cm)}}{6000}$$

* El resultado se redondea a **2 decimales**.
* El divisor `6000` corresponde al factor volumétrico estándar para transporte terrestre de paquetería y encomiendas en el Perú.

### 2.2. Determinación del Peso Liquidable
$$\text{Peso Liquidable (kg)} = \max(\text{Peso Físico (kg)}, \text{Peso Volumétrico (kg)})$$

### 2.3. Estructura de Componentes Tarifarios (Tarifas Vigentes 2026)

| Concepto Tarifario | Importe (S/) | Condición de Aplicación |
| :--- | :---: | :--- |
| **Tarifa Base Obligatoria** | `S/ 8.00` | Cargo fijo administrativo y emisión de guía por cada encomienda. |
| **Tarifa por Kilogramo** | `S/ 2.50 / kg` | Se multiplica por el `Peso Liquidable`. |
| **Recargo de Entrega a Domicilio** | `S/ 12.00` | Aplica en modalidades `agencia_domicilio` y `domicilio_domicilio`. |
| **Recargo de Recojo en Domicilio** | `S/ 15.00` | Aplica en modalidades `domicilio_agencia` y `domicilio_domicilio`. |

### 2.4. Fórmula del Precio Total
$$\text{Precio Total} = \text{Tarifa Base} + (\text{Peso Liquidable} \times 2.50) + \text{Recargos de Domicilio}$$

---

## 3. Desglose Contable y Tributario (SUNAT)

Todo importe final cobrado al cliente incluye el **Impuesto General a las Ventas (IGV 18%)**:

* **Monto Subtotal (Base Imponible):**
  $$\text{Subtotal} = \text{round}\left(\frac{\text{Precio Total}}{1.18}, 2\right)$$
* **Monto IGV (18%):**
  $$\text{IGV} = \text{round}(\text{Precio Total} - \text{Subtotal}, 2)$$
* **Verificación de Cierre:**
  $$\text{Subtotal} + \text{IGV} = \text{Precio Total}$$

---

## 4. Catálogo Detallado de Reglas de Negocio (BR-TAR)

### `BR-TAR-01`: Determinación Exclusiva en Backend
* **Descripción:** Los precios cotizados no pueden ser enviados por el Frontend ni alterados mediante peticiones manipuladas. 
* **Implementación:** El backend recibe únicamente las dimensiones físicas (`peso_kg`, `largo_cm`, `ancho_cm`, `alto_cm`) y la modalidad de servicio (`tipo_envio`), calculando el precio final con su propia lógica de dominio.

### `BR-TAR-02`: Política de Recálculo en Recepción Física (Balanza)
Al momento en que el remitente acude a la agencia o el courier arriba a su domicilio, la carga se somete a inspección física vinculante:
* **Escenario A (Peso/Volumen Real Superior a la Cotización Web):**
  * Si `Precio Real - Precio Pre-registrado > S/ 0.50`:
  * El cajero debe exigir el cobro del **reintegro por diferencia tarifaria**.
  * Se genera un apunte en el historial: *"Se cobró reintegro por S/ X.XX debido a mayor peso/volumen verificado en balanza oficial"*.
* **Escenario B (Peso/Volumen Real Menor a la Cotización Web):**
  * Si el cliente sobre-estimó el paquete en la web y ya realizó el pago online:
  * No procede reembolso parcial por diferencia de centavos o kilos sobrantes, debido a la **reserva previa de espacio en bodega** (salvo anulación formal de la orden según `BR-CAN-01`).

### `BR-TAR-03`: Restricción de Medidas y Pesos Mínimos/Máximos
* **Peso Físico Mínimo:** 0.10 kg (no se admiten paquetes con peso cero).
* **Peso Físico Máximo por Bulto Individual:** 80.00 kg (por normativas de salud ocupacional y manipulación manual de carga).
* **Dimensiones Máximas:** Ningún lado (largo, ancho o alto) puede exceder de 250 cm sin previa autorización de gerencia de flota.

---

## 5. Ejemplos Prácticos de Aplicación

### Ejemplo 1: Paquete Denso (Pesa más de lo que ocupa)
* Paquete: Herramientas de metal
* Dimensiones: 20 cm x 15 cm x 10 cm. Peso físico: **10.00 kg**. Tipo de envío: `agencia_agencia`.
* $\text{Peso Volumétrico} = \frac{20 \times 15 \times 10}{6000} = \frac{3000}{6000} = 0.50\text{ kg}$.
* $\text{Peso Liquidable} = \max(10.00, 0.50) = 10.00\text{ kg}$.
* Flete: $\text{Base (S/ 8.00)} + (10.00 \times 2.50) = 8.00 + 25.00 = \mathbf{S/\ 33.00}$.

### Ejemplo 2: Paquete Voluminoso (Ocupa más de lo que pesa)
* Paquete: Caja con peluches
* Dimensiones: 60 cm x 50 cm x 40 cm. Peso físico: **3.00 kg**. Tipo de envío: `agencia_domicilio`.
* $\text{Peso Volumétrico} = \frac{60 \times 50 \times 40}{6000} = \frac{120000}{6000} = 20.00\text{ kg}$.
* $\text{Peso Liquidable} = \max(3.00, 20.00) = 20.00\text{ kg}$.
* Flete: $\text{Base (8.00)} + (20.00 \times 2.50) + \text{Domicilio (12.00)} = 8.00 + 50.00 + 12.00 = \mathbf{S/\ 70.00}$.

-- ==============================================================================
-- CARGAEXPRESS PERÚ - SEED DATA WAREHOUSE 2026 (ENERO A NOVIEMBRE 2026)
-- Incluye:
-- 1. Aperturas de caja históricas
-- 2. 60 Envíos cronológicos con tendencia de crecimiento y alta tasa de entrega
-- 3. Guías de remisión y detalle
-- 4. Movimientos de caja vinculados a ventas
-- 5. Historial cronológico ordenado para cada paquete
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. APERTURAS DE CAJA (IDs 6 AL 16)
-- ------------------------------------------------------------------------------
INSERT INTO public.aperturas_caja (id, usuario_id, numero_caja, saldo_inicial, fecha_apertura, fecha_cierre, saldo_final, total_ventas, estado, creado_en) VALUES
(6, 9, 1, 100.00, '2026-01-05 08:00:00', '2026-01-31 19:30:00', 1450.00, 1350.00, 'cerrada', '2026-01-05 08:00:00'),
(7, 10, 1, 150.00, '2026-02-02 08:00:00', '2026-02-28 19:00:00', 1820.50, 1670.50, 'cerrada', '2026-02-02 08:00:00'),
(8, 12, 1, 120.00, '2026-03-02 08:30:00', '2026-03-31 19:00:00', 2140.00, 2020.00, 'cerrada', '2026-03-02 08:30:00'),
(9, 16, 1, 100.00, '2026-04-01 08:00:00', '2026-04-30 19:00:00', 2380.00, 2280.00, 'cerrada', '2026-04-01 08:00:00'),
(10, 20, 1, 100.00, '2026-05-02 08:00:00', '2026-05-31 19:00:00', 2760.00, 2660.00, 'cerrada', '2026-05-02 08:00:00'),
(11, 24, 1, 150.00, '2026-06-01 08:00:00', '2026-06-30 19:00:00', 3120.00, 2970.00, 'cerrada', '2026-06-01 08:00:00'),
(12, 28, 1, 120.00, '2026-07-01 08:00:00', '2026-07-31 19:00:00', 3450.00, 3330.00, 'cerrada', '2026-07-01 08:00:00'),
(13, 32, 1, 100.00, '2026-08-01 08:00:00', '2026-08-31 19:00:00', 3890.00, 3790.00, 'cerrada', '2026-08-01 08:00:00'),
(14, 36, 1, 150.00, '2026-09-01 08:00:00', '2026-09-30 19:00:00', 4210.00, 4060.00, 'cerrada', '2026-09-01 08:00:00'),
(15, 9, 1, 200.00, '2026-10-01 08:00:00', '2026-10-31 19:00:00', 4980.00, 4780.00, 'cerrada', '2026-10-01 08:00:00'),
(16, 9, 1, 250.00, '2026-11-01 08:00:00', NULL, NULL, NULL, 'abierta', '2026-11-01 08:00:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.aperturas_caja_id_seq', 16, true);

-- ------------------------------------------------------------------------------
-- 2. ENVÍOS HISTÓRICOS 2026 (IDs 15 AL 74)
-- ------------------------------------------------------------------------------
INSERT INTO public.envios (id, codigo_tracking, remitente_id, destinatario_id, agencia_origen_id, agencia_destino_id, tipo_envio, tipo_paquete, peso_kg, alto_cm, ancho_cm, largo_cm, peso_volumetrico, descripcion, direccion_recojo, direccion_entrega, monto_subtotal, monto_descuento, monto_igv, precio_envio, forma_pago, estado_pago, lugar_pago, estado, fecha_estimada, fecha_entrega_real, imagen_recepcion, imagen_evidencia, tipo_documento, numero_documento, serie_documento, registrado_por_id, registrado_web, apertura_caja_id, courier_id, creado_en, actualizado_en) VALUES
-- Enero 2026 (3 envíos)
(15, 'CE2601L8K2M9P1', 30, 2, 1, 2, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M01', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-01-08', '2026-01-07 14:20:00', NULL, NULL, 'factura', '00000051', 'F001', 9, false, 6, NULL, '2026-01-05 09:15:00', '2026-01-07 14:20:00'),
(16, 'CE2601T4V7X2A8', 35, 4, 3, 11, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M01', NULL, 'Av. Los Álamos 215, Cusco', 24.15, 0.00, 4.35, 28.50, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-01-12', '2026-01-11 16:45:00', NULL, NULL, 'boleta', '00000101', 'B001', 12, false, 6, 23, '2026-01-09 10:30:00', '2026-01-11 16:45:00'),
(17, 'CE2601C9D3F5G7', 36, 6, 19, 21, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M01', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-01-18', '2026-01-17 11:10:00', NULL, NULL, 'boleta', '00000102', 'B001', 24, false, 6, NULL, '2026-01-15 11:20:00', '2026-01-17 11:10:00'),

-- Febrero 2026 (4 envíos)
(18, 'CE2602K6M8P2R4', 31, 8, 2, 1, 'agencia_agencia', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M02', NULL, NULL, 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-02-06', '2026-02-05 15:30:00', NULL, NULL, 'factura', '00000052', 'F001', 10, false, 7, NULL, '2026-02-03 09:40:00', '2026-02-05 15:30:00'),
(19, 'CE2602B7D9F1H3', 37, 41, 4, 7, 'agencia_domicilio', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M02', NULL, 'Calle Comercio 120, Ica', 30.93, 0.00, 5.57, 36.50, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-02-11', '2026-02-10 17:15:00', NULL, NULL, 'boleta', '00000103', 'B001', 16, false, 7, 40, '2026-02-07 14:10:00', '2026-02-10 17:15:00'),
(20, 'CE2602J2L4N6Q8', 32, 42, 7, 19, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M02', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-02-16', '2026-02-15 16:00:00', NULL, NULL, 'factura', '00000053', 'F001', 36, false, 7, NULL, '2026-02-12 10:50:00', '2026-02-15 16:00:00'),
(21, 'CE2602S5U7W9Y1', 38, 43, 21, 23, 'agencia_domicilio', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M02', NULL, 'Jr. Bolognesi 210, Tacna', 18.64, 0.00, 3.36, 22.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-02-21', '2026-02-20 12:40:00', NULL, NULL, 'boleta', '00000104', 'B001', 28, false, 7, 35, '2026-02-18 11:30:00', '2026-02-20 12:40:00'),

-- Marzo 2026 (4 envíos)
(22, 'CE2603A2C4E6G8', 33, 44, 11, 2, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M03', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-03-07', '2026-03-06 14:15:00', NULL, NULL, 'factura', '00000054', 'F001', 22, false, 8, NULL, '2026-03-04 09:25:00', '2026-03-06 14:15:00'),
(23, 'CE2603H1J3L5N7', 39, 45, 1, 23, 'agencia_domicilio', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M03', NULL, 'Av. Bolognesi 450, Tacna', 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-03-12', '2026-03-11 15:30:00', NULL, NULL, 'boleta', '00000105', 'B001', 9, false, 8, 35, '2026-03-09 10:15:00', '2026-03-11 15:30:00'),
(24, 'CE2603P9R1T3V5', 40, 2, 23, 1, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M03', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-03-18', '2026-03-17 11:50:00', NULL, NULL, 'boleta', '00000106', 'B001', 32, false, 8, NULL, '2026-03-15 12:00:00', '2026-03-17 11:50:00'),
(25, 'CE2603X7Z9B2D4', 34, 4, 19, 11, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M03', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-03-24', '2026-03-23 16:10:00', NULL, NULL, 'factura', '00000055', 'F001', 24, false, 8, NULL, '2026-03-21 15:10:00', '2026-03-23 16:10:00'),

-- Abril 2026 (5 envíos)
(26, 'CE2604F6H8J1L3', 35, 6, 1, 19, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M04', NULL, 'Av. España 312, Trujillo', 24.15, 0.00, 4.35, 28.50, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-04-05', '2026-04-04 14:00:00', NULL, NULL, 'boleta', '00000107', 'B001', 9, false, 9, 30, '2026-04-02 09:30:00', '2026-04-04 14:00:00'),
(27, 'CE2604N5Q7S9U1', 30, 8, 2, 21, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M04', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-04-10', '2026-04-09 16:40:00', NULL, NULL, 'factura', '00000056', 'F001', 10, false, 9, NULL, '2026-04-07 10:15:00', '2026-04-09 16:40:00'),
(28, 'CE2604W3Y5A7C9', 36, 41, 3, 2, 'agencia_agencia', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M04', NULL, NULL, 18.64, 0.00, 3.36, 22.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-04-15', '2026-04-14 11:20:00', NULL, NULL, 'boleta', '00000108', 'B001', 12, false, 9, NULL, '2026-04-12 11:00:00', '2026-04-14 11:20:00'),
(29, 'CE2604E2G4I6K8', 31, 42, 21, 1, 'agencia_domicilio', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M04', NULL, 'Calle Las Begonias 415, San Isidro', 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-04-20', '2026-04-19 15:30:00', NULL, NULL, 'factura', '00000057', 'F001', 28, false, 9, 17, '2026-04-17 14:20:00', '2026-04-19 15:30:00'),
(30, 'CE2604M0O2Q4S6', 37, 43, 7, 23, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M04', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-04-26', '2026-04-25 10:15:00', NULL, NULL, 'boleta', '00000109', 'B001', 36, false, 9, NULL, '2026-04-23 09:40:00', '2026-04-25 10:15:00'),

-- Mayo 2026 (5 envíos - incluye caso de siniestro controlado para alertar)
(31, 'CE2605U8W0Y2A4', 38, 44, 4, 11, 'agencia_agencia', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M05', NULL, NULL, 40.68, 0.00, 7.32, 48.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-05-06', '2026-05-05 14:30:00', NULL, NULL, 'boleta', '00000110', 'B001', 16, false, 10, NULL, '2026-05-03 10:10:00', '2026-05-05 14:30:00'),
(32, 'CE2605C6E8G0I2', 32, 45, 1, 2, 'agencia_domicilio', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M05', NULL, 'Av. Goyeneche 140, Arequipa', 30.93, 0.00, 5.57, 36.50, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-05-11', '2026-05-10 16:15:00', NULL, NULL, 'factura', '00000058', 'F001', 9, false, 10, 23, '2026-05-08 11:30:00', '2026-05-10 16:15:00'),
(33, 'CE2605K4M6O8Q0', 39, 2, 1, 11, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M05', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'yape_plin', 'pagado', 'origen', 'siniestrado', '2026-05-16', NULL, NULL, NULL, 'boleta', '00000111', 'B001', 9, false, 10, NULL, '2026-05-13 14:00:00', '2026-05-14 22:30:00'),
(34, 'CE2605S2U4W6Y8', 33, 4, 11, 19, 'agencia_agencia', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M05', NULL, NULL, 18.64, 0.00, 3.36, 22.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-05-21', '2026-05-20 12:45:00', NULL, NULL, 'factura', '00000059', 'F001', 22, false, 10, NULL, '2026-05-18 09:50:00', '2026-05-20 12:45:00'),
(35, 'CE2605A0C2E4G6', 40, 6, 23, 7, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M05', NULL, 'Jr. Moquegua 110, Ica', 24.15, 0.00, 4.35, 28.50, 'efectivo', 'pagado', 'origen', 'entregado', '2026-05-27', '2026-05-26 15:20:00', NULL, NULL, 'boleta', '00000112', 'B001', 32, false, 10, 40, '2026-05-24 10:40:00', '2026-05-26 15:20:00'),

-- Junio 2026 (6 envíos)
(36, 'CE2606I8K0M2O4', 30, 8, 2, 3, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M06', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-06-05', '2026-06-04 14:10:00', NULL, NULL, 'factura', '00000060', 'F001', 10, false, 11, NULL, '2026-06-02 09:15:00', '2026-06-04 14:10:00'),
(37, 'CE2606Q6S8U0W2', 35, 41, 19, 2, 'agencia_domicilio', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M06', NULL, 'Calle Mercaderes 204, Arequipa', 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-06-10', '2026-06-09 17:00:00', NULL, NULL, 'boleta', '00000113', 'B001', 24, false, 11, 23, '2026-06-07 10:20:00', '2026-06-09 17:00:00'),
(38, 'CE2606Y4A6C8E0', 36, 42, 21, 11, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M06', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-06-15', '2026-06-14 11:30:00', NULL, NULL, 'boleta', '00000114', 'B001', 28, false, 11, NULL, '2026-06-12 11:45:00', '2026-06-14 11:30:00'),
(39, 'CE2606G2I4K6M8', 34, 43, 1, 7, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M06', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-06-20', '2026-06-19 15:40:00', NULL, NULL, 'factura', '00000061', 'F001', 9, false, 11, NULL, '2026-06-17 14:10:00', '2026-06-19 15:40:00'),
(40, 'CE2606O0Q2S4U6', 37, 44, 7, 21, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M06', NULL, 'Jr. Arequipa 520, Puno', 24.15, 0.00, 4.35, 28.50, 'efectivo', 'pagado', 'origen', 'entregado', '2026-06-25', '2026-06-24 16:30:00', NULL, NULL, 'boleta', '00000115', 'B001', 36, false, 11, 35, '2026-06-22 09:30:00', '2026-06-24 16:30:00'),
(41, 'CE2606W8Y0A2C4', 31, 45, 11, 1, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M06', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-06-30', '2026-06-29 15:10:00', NULL, NULL, 'factura', '00000062', 'F001', 22, false, 11, NULL, '2026-06-27 10:00:00', '2026-06-29 15:10:00'),

-- Julio 2026 (6 envíos)
(42, 'CE2607E6G8I0K2', 38, 2, 1, 23, 'agencia_agencia', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M07', NULL, NULL, 18.64, 0.00, 3.36, 22.00, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-07-05', '2026-07-04 13:50:00', NULL, NULL, 'boleta', '00000116', 'B001', 9, false, 12, NULL, '2026-07-02 09:40:00', '2026-07-04 13:50:00'),
(43, 'CE2607M4O6Q8S0', 32, 4, 3, 19, 'agencia_domicilio', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M07', NULL, 'Jr. Pizarro 610, Trujillo', 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-07-10', '2026-07-09 16:15:00', NULL, NULL, 'factura', '00000063', 'F001', 12, false, 12, 30, '2026-07-07 10:50:00', '2026-07-09 16:15:00'),
(44, 'CE2607U2W4Y6A8', 39, 6, 2, 7, 'agencia_agencia', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M07', NULL, NULL, 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-07-16', '2026-07-15 15:30:00', NULL, NULL, 'boleta', '00000117', 'B001', 10, false, 12, NULL, '2026-07-13 11:20:00', '2026-07-15 15:30:00'),
(45, 'CE2607C0E2G4I6', 33, 8, 19, 21, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M07', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-07-21', '2026-07-20 14:00:00', NULL, NULL, 'factura', '00000064', 'F001', 24, false, 12, NULL, '2026-07-18 09:30:00', '2026-07-20 14:00:00'),
(46, 'CE2607K8M0O2Q4', 40, 41, 23, 2, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M07', NULL, 'Av. Independencia 720, Arequipa', 24.15, 0.00, 4.35, 28.50, 'efectivo', 'pagado', 'origen', 'entregado', '2026-07-26', '2026-07-25 17:20:00', NULL, NULL, 'boleta', '00000118', 'B001', 32, false, 12, 23, '2026-07-23 10:15:00', '2026-07-25 17:20:00'),
(47, 'CE2607S6U8W0Y2', 30, 42, 21, 1, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M07', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-07-31', '2026-07-30 16:45:00', NULL, NULL, 'factura', '00000065', 'F001', 28, false, 12, NULL, '2026-07-28 14:40:00', '2026-07-30 16:45:00'),

-- Agosto 2026 (7 envíos)
(48, 'CE2608A4C6E8G0', 35, 43, 1, 2, 'agencia_domicilio', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M08', NULL, 'Calle San Francisco 112, Arequipa', 12.71, 0.00, 2.29, 15.00, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-08-04', '2026-08-03 12:10:00', NULL, NULL, 'boleta', '00000119', 'B001', 9, false, 13, 23, '2026-08-01 09:10:00', '2026-08-03 12:10:00'),
(49, 'CE2608I2K4M6O8', 31, 44, 2, 11, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M08', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-08-08', '2026-08-07 14:30:00', NULL, NULL, 'factura', '00000066', 'F001', 10, false, 13, NULL, '2026-08-05 10:20:00', '2026-08-07 14:30:00'),
(50, 'CE2608Q0S2U4W6', 36, 45, 11, 23, 'agencia_agencia', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M08', NULL, NULL, 40.68, 0.00, 7.32, 48.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-08-13', '2026-08-12 15:50:00', NULL, NULL, 'boleta', '00000120', 'B001', 22, false, 13, NULL, '2026-08-10 11:30:00', '2026-08-12 15:50:00'),
(51, 'CE2608Y8A0C2E4', 34, 2, 7, 1, 'agencia_domicilio', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M08', NULL, 'Av. Larco 850, Miraflores', 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-08-18', '2026-08-17 16:20:00', NULL, NULL, 'factura', '00000067', 'F001', 36, false, 13, 17, '2026-08-15 14:00:00', '2026-08-17 16:20:00'),
(52, 'CE2608G6I8K0M2', 37, 4, 19, 7, 'agencia_agencia', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M08', NULL, NULL, 18.64, 0.00, 3.36, 22.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-08-23', '2026-08-22 11:40:00', NULL, NULL, 'boleta', '00000121', 'B001', 24, false, 13, NULL, '2026-08-20 09:50:00', '2026-08-22 11:40:00'),
(53, 'CE2608O4Q6S8U0', 32, 6, 23, 21, 'agencia_domicilio', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M08', NULL, 'Calle Lima 340, Juliaca', 101.69, 0.00, 18.31, 120.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-08-28', '2026-08-27 15:30:00', NULL, NULL, 'factura', '00000068', 'F001', 32, false, 13, 35, '2026-08-25 10:45:00', '2026-08-27 15:30:00'),
(54, 'CE2608W2Y4A6C8', 38, 8, 4, 1, 'agencia_agencia', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M08', NULL, NULL, 24.15, 0.00, 4.35, 28.50, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-09-02', '2026-09-01 13:50:00', NULL, NULL, 'boleta', '00000122', 'B001', 16, false, 13, NULL, '2026-08-29 11:15:00', '2026-09-01 13:50:00'),

-- Septiembre 2026 (7 envíos)
(55, 'CE2609E0G2I4K6', 30, 41, 1, 11, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M09', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-09-05', '2026-09-04 14:15:00', NULL, NULL, 'factura', '00000069', 'F001', 9, false, 14, NULL, '2026-09-02 09:20:00', '2026-09-04 14:15:00'),
(56, 'CE2609M8O0Q2S4', 39, 42, 2, 19, 'agencia_domicilio', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M09', NULL, 'Av. Larco 405, Trujillo', 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-09-10', '2026-09-09 16:30:00', NULL, NULL, 'boleta', '00000123', 'B001', 10, false, 14, 30, '2026-09-07 10:30:00', '2026-09-09 16:30:00'),
(57, 'CE2609U6W8Y0A2', 33, 43, 11, 1, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M09', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-09-15', '2026-09-14 15:40:00', NULL, NULL, 'factura', '00000070', 'F001', 22, false, 14, NULL, '2026-09-12 11:45:00', '2026-09-14 15:40:00'),
(58, 'CE2609C4E6G8I0', 40, 44, 21, 23, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M09', NULL, 'Calle San Martín 320, Tacna', 24.15, 0.00, 4.35, 28.50, 'efectivo', 'pagado', 'origen', 'entregado', '2026-09-20', '2026-09-19 12:50:00', NULL, NULL, 'boleta', '00000124', 'B001', 28, false, 14, 35, '2026-09-17 14:10:00', '2026-09-19 12:50:00'),
(59, 'CE2609K2M4O6Q8', 31, 45, 7, 2, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M09', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-09-25', '2026-09-24 16:15:00', NULL, NULL, 'factura', '00000071', 'F001', 36, false, 14, NULL, '2026-09-22 09:30:00', '2026-09-24 16:15:00'),
(60, 'CE2609S0U2W4Y6', 35, 2, 19, 1, 'agencia_domicilio', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M09', NULL, 'Av. Arequipa 1250, Lima', 18.64, 0.00, 3.36, 22.00, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-09-29', '2026-09-28 17:30:00', NULL, NULL, 'boleta', '00000125', 'B001', 24, false, 14, 17, '2026-09-26 10:20:00', '2026-09-28 17:30:00'),
(61, 'CE2609A8C0E2G4', 36, 4, 3, 7, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M09', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'efectivo', 'pagado', 'origen', 'entregado', '2026-10-02', '2026-10-01 11:20:00', NULL, NULL, 'boleta', '00000126', 'B001', 12, false, 14, NULL, '2026-09-29 11:00:00', '2026-10-01 11:20:00'),

-- Octubre 2026 (7 envíos)
(62, 'CE2610I6K8M0O2', 32, 6, 1, 2, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M10', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-10-05', '2026-10-04 14:40:00', NULL, NULL, 'factura', '00000072', 'F001', 9, false, 15, NULL, '2026-10-02 09:15:00', '2026-10-04 14:40:00'),
(63, 'CE2610Q4S6U8W0', 37, 8, 2, 23, 'agencia_domicilio', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M10', NULL, 'Av. Leguía 380, Tacna', 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-10-10', '2026-10-09 15:50:00', NULL, NULL, 'boleta', '00000127', 'B001', 10, false, 15, 35, '2026-10-07 10:45:00', '2026-10-09 15:50:00'),
(64, 'CE2610Y2A4C6E8', 34, 41, 11, 7, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M10', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'transferencia', 'pagado', 'origen', 'entregado', '2026-10-15', '2026-10-14 16:10:00', NULL, NULL, 'factura', '00000073', 'F001', 22, false, 15, NULL, '2026-10-12 11:20:00', '2026-10-14 16:10:00'),
(65, 'CE2610G0I2K4M6', 38, 42, 23, 1, 'agencia_agencia', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M10', NULL, NULL, 101.69, 0.00, 18.31, 120.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-10-20', '2026-10-19 17:00:00', NULL, NULL, 'boleta', '00000128', 'B001', 32, false, 15, NULL, '2026-10-17 14:00:00', '2026-10-19 17:00:00'),
(66, 'CE2610O8Q0S2U4', 30, 43, 19, 21, 'agencia_domicilio', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M10', NULL, 'Jr. Huancané 180, Juliaca', 24.15, 0.00, 4.35, 28.50, 'yape_plin', 'pagado', 'origen', 'entregado', '2026-10-25', '2026-10-24 13:40:00', NULL, NULL, 'factura', '00000074', 'F001', 24, false, 15, 35, '2026-10-22 09:30:00', '2026-10-24 13:40:00'),
(67, 'CE2610W6Y8A0C2', 39, 44, 4, 3, 'agencia_domicilio', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M10', NULL, 'Av. Pardo 540, Miraflores', 18.64, 0.00, 3.36, 22.00, 'efectivo', 'pagado', 'origen', 'en_reparto', '2026-10-30', NULL, NULL, NULL, 'boleta', '00000129', 'B001', 16, false, 15, 17, '2026-10-27 10:15:00', '2026-10-29 18:00:00'),
(68, 'CE2610E4G6I8K0', 31, 45, 7, 19, 'agencia_agencia', 'sobre', 0.50, 5.00, 25.00, 35.00, 0.88, 'Documentación legal y contratos - Lote 2026-M10', NULL, NULL, 12.71, 0.00, 2.29, 15.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-11-03', '2026-11-02 11:30:00', NULL, NULL, 'factura', '00000075', 'F001', 36, false, 15, NULL, '2026-10-31 11:30:00', '2026-11-02 11:30:00'),

-- Noviembre 2026 (6 envíos - pipeline activo del mes en curso)
(69, 'CE2611M2O4Q6S8', 35, 2, 1, 2, 'agencia_agencia', 'caja', 12.00, 40.00, 40.00, 40.00, 12.80, 'Textiles y confecciones de exportación - Lote 2026-M11', NULL, NULL, 72.03, 0.00, 12.97, 85.00, 'transferencia', 'pagado', 'origen', 'entregado', '2026-11-05', '2026-11-04 15:20:00', NULL, NULL, 'boleta', '00000130', 'B001', 9, false, 16, NULL, '2026-11-02 09:30:00', '2026-11-04 15:20:00'),
(70, 'CE2611U0W2Y4A6', 32, 4, 2, 1, 'agencia_domicilio', 'caja', 8.00, 35.00, 30.00, 30.00, 6.30, 'Equipos informáticos y periféricos - Lote 2026-M11', NULL, 'Av. San Felipe 410, Jesús María', 40.68, 0.00, 7.32, 48.00, 'tarjeta', 'pagado', 'origen', 'entregado', '2026-11-08', '2026-11-07 16:40:00', NULL, NULL, 'factura', '00000076', 'F001', 10, false, 16, 17, '2026-11-05 10:15:00', '2026-11-07 16:40:00'),
(71, 'CE2611C8E0G2I4', 36, 6, 3, 11, 'agencia_agencia', 'caja', 5.00, 30.00, 20.00, 25.00, 3.00, 'Insumos médicos y farmacéuticos - Lote 2026-M11', NULL, NULL, 30.93, 0.00, 5.57, 36.50, 'yape_plin', 'pagado', 'origen', 'en_transito', '2026-11-12', NULL, NULL, NULL, 'boleta', '00000131', 'B001', 12, false, 16, NULL, '2026-11-08 11:20:00', '2026-11-09 08:30:00'),
(72, 'CE2611K6M8O0Q2', 33, 8, 19, 7, 'agencia_domicilio', 'caja', 18.00, 50.00, 40.00, 40.00, 16.00, 'Herramientas y ferretería pesada - Lote 2026-M11', NULL, 'Calle Bolívar 230, Ica', 101.69, 0.00, 18.31, 120.00, 'transferencia', 'pagado', 'origen', 'en_transito', '2026-11-15', NULL, NULL, NULL, 'factura', '00000077', 'F001', 24, false, 16, 40, '2026-11-11 14:00:00', '2026-11-12 09:00:00'),
(73, 'CE2611S4U6W8Y0', 37, 41, 21, 2, 'agencia_agencia', 'caja', 3.50, 25.00, 25.00, 25.00, 3.13, 'Caja con repuestos industriales - Lote 2026-M11', NULL, NULL, 24.15, 0.00, 4.35, 28.50, 'efectivo', 'pagado', 'origen', 'recepcionado', '2026-11-17', NULL, NULL, NULL, 'boleta', '00000132', 'B001', 28, false, 16, NULL, '2026-11-14 09:45:00', '2026-11-14 10:30:00'),
(74, 'CE2611A2C4E6G8', 38, 42, 23, 1, 'agencia_agencia', 'paquete', 2.00, 20.00, 20.00, 15.00, 1.20, 'Calzado y artículos de cuero - Lote 2026-M11', NULL, NULL, 18.64, 0.00, 3.36, 22.00, 'pendiente', 'pendiente', 'origen', 'registrado', '2026-11-20', NULL, NULL, NULL, 'boleta', '00000133', 'B001', 32, false, 16, NULL, '2026-11-16 11:15:00', '2026-11-16 11:15:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.envios_id_seq', 74, true);

-- ------------------------------------------------------------------------------
-- 3. GUÍAS DE REMISIÓN Y DETALLES (IDs 7 AL 36)
-- ------------------------------------------------------------------------------
INSERT INTO public.guias_remision (id, codigo_guia, agencia_origen_id, agencia_destino_id, fecha_salida, estado, transportista_id, vehiculo_id, creado_por, creado_en, actualizado_en) VALUES
(7, 2007, 1, 2, '2026-01-05 23:15:00', 'enviado', 15, 2, 9, '2026-01-05 23:15:00', '2026-01-05 23:15:00'),
(8, 2008, 3, 11, '2026-01-10 00:30:00', 'enviado', 19, 3, 12, '2026-01-10 00:30:00', '2026-01-10 00:30:00'),
(9, 2009, 19, 21, '2026-01-16 01:20:00', 'enviado', 27, 4, 24, '2026-01-16 01:20:00', '2026-01-16 01:20:00'),
(10, 2010, 2, 1, '2026-02-03 23:40:00', 'enviado', 15, 2, 10, '2026-02-03 23:40:00', '2026-02-03 23:40:00'),
(11, 2011, 4, 7, '2026-02-08 04:10:00', 'enviado', 31, 5, 16, '2026-02-08 04:10:00', '2026-02-08 04:10:00'),
(12, 2012, 7, 19, '2026-02-13 00:50:00', 'enviado', 39, 6, 36, '2026-02-13 00:50:00', '2026-02-13 00:50:00'),
(13, 2013, 21, 23, '2026-02-19 01:30:00', 'enviado', 31, 5, 28, '2026-02-19 01:30:00', '2026-02-19 01:30:00'),
(14, 2014, 11, 2, '2026-03-04 23:25:00', 'enviado', 19, 3, 22, '2026-03-04 23:25:00', '2026-03-04 23:25:00'),
(15, 2015, 1, 23, '2026-03-10 00:15:00', 'enviado', 15, 2, 9, '2026-03-10 00:15:00', '2026-03-10 00:15:00'),
(16, 2016, 23, 1, '2026-03-16 02:00:00', 'enviado', 27, 4, 32, '2026-03-16 02:00:00', '2026-03-16 02:00:00'),
(17, 2017, 19, 11, '2026-03-22 05:10:00', 'enviado', 31, 5, 24, '2026-03-22 05:10:00', '2026-03-22 05:10:00'),
(18, 2018, 1, 19, '2026-04-02 23:30:00', 'enviado', 15, 2, 9, '2026-04-02 23:30:00', '2026-04-02 23:30:00'),
(19, 2019, 2, 21, '2026-04-08 00:15:00', 'enviado', 19, 3, 10, '2026-04-08 00:15:00', '2026-04-08 00:15:00'),
(20, 2020, 3, 2, '2026-04-13 01:00:00', 'enviado', 27, 4, 12, '2026-04-13 01:00:00', '2026-04-13 01:00:00'),
(21, 2021, 21, 1, '2026-04-18 04:20:00', 'enviado', 31, 5, 28, '2026-04-18 04:20:00', '2026-04-18 04:20:00'),
(22, 2022, 7, 23, '2026-04-23 23:40:00', 'enviado', 39, 6, 36, '2026-04-23 23:40:00', '2026-04-23 23:40:00'),
(23, 2023, 4, 11, '2026-05-04 00:10:00', 'enviado', 15, 2, 16, '2026-05-04 00:10:00', '2026-05-04 00:10:00'),
(24, 2024, 1, 2, '2026-05-09 01:30:00', 'enviado', 19, 3, 9, '2026-05-09 01:30:00', '2026-05-09 01:30:00'),
(25, 2025, 1, 11, '2026-05-14 04:00:00', 'enviado', 27, 4, 9, '2026-05-14 04:00:00', '2026-05-14 04:00:00'),
(26, 2026, 11, 19, '2026-05-18 23:50:00', 'enviado', 31, 5, 22, '2026-05-18 23:50:00', '2026-05-18 23:50:00'),
(27, 2027, 23, 7, '2026-05-25 00:40:00', 'enviado', 39, 6, 32, '2026-05-25 00:40:00', '2026-05-25 00:40:00'),
(28, 2028, 2, 3, '2026-06-02 23:15:00', 'enviado', 15, 2, 10, '2026-06-02 23:15:00', '2026-06-02 23:15:00'),
(29, 2029, 19, 2, '2026-06-08 00:20:00', 'enviado', 19, 3, 24, '2026-06-08 00:20:00', '2026-06-08 00:20:00'),
(30, 2030, 21, 11, '2026-06-13 01:45:00', 'enviado', 27, 4, 28, '2026-06-13 01:45:00', '2026-06-13 01:45:00'),
(31, 2031, 3, 11, '2026-11-09 01:20:00', 'pendiente_traslado', 15, 2, 12, '2026-11-09 01:20:00', '2026-11-09 01:20:00'),
(32, 2032, 19, 7, '2026-11-12 04:00:00', 'pendiente_traslado', 19, 3, 24, '2026-11-12 04:00:00', '2026-11-12 04:00:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.guias_remision_id_seq', 32, true);

INSERT INTO public.guias_remision_detalle (id, guia_id, envio_id, creado_en) VALUES
(9, 7, 15, '2026-01-05 23:15:00'),
(10, 8, 16, '2026-01-10 00:30:00'),
(11, 9, 17, '2026-01-16 01:20:00'),
(12, 10, 18, '2026-02-03 23:40:00'),
(13, 11, 19, '2026-02-08 04:10:00'),
(14, 12, 20, '2026-02-13 00:50:00'),
(15, 13, 21, '2026-02-19 01:30:00'),
(16, 14, 22, '2026-03-04 23:25:00'),
(17, 15, 23, '2026-03-10 00:15:00'),
(18, 16, 24, '2026-03-16 02:00:00'),
(19, 17, 25, '2026-03-22 05:10:00'),
(20, 18, 26, '2026-04-02 23:30:00'),
(21, 19, 27, '2026-04-08 00:15:00'),
(22, 20, 28, '2026-04-13 01:00:00'),
(23, 21, 29, '2026-04-18 04:20:00'),
(24, 22, 30, '2026-04-23 23:40:00'),
(25, 23, 31, '2026-05-04 00:10:00'),
(26, 24, 32, '2026-05-09 01:30:00'),
(27, 25, 33, '2026-05-14 04:00:00'),
(28, 26, 34, '2026-05-18 23:50:00'),
(29, 27, 35, '2026-05-25 00:40:00'),
(30, 28, 36, '2026-06-02 23:15:00'),
(31, 29, 37, '2026-06-08 00:20:00'),
(32, 30, 38, '2026-06-13 01:45:00'),
(33, 31, 71, '2026-11-09 01:20:00'),
(34, 32, 72, '2026-11-12 04:00:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.guias_remision_detalle_id_seq', 34, true);

-- ------------------------------------------------------------------------------
-- 4. MOVIMIENTOS DE CAJA (IDs 11 AL 69)
-- ------------------------------------------------------------------------------
INSERT INTO public.movimientos_caja (id, apertura_id, envio_id, tipo, monto, descripcion, creado_en) VALUES
(11, 6, 15, 'ingreso', 85.00, 'Cobro servicio envío CE2601L8K2M9P1 (FACTURA F001-00000051)', '2026-01-05 09:15:00'),
(12, 6, 16, 'ingreso', 28.50, 'Cobro servicio envío CE2601T4V7X2A8 (BOLETA B001-00000101)', '2026-01-09 10:30:00'),
(13, 6, 17, 'ingreso', 15.00, 'Cobro servicio envío CE2601C9D3F5G7 (BOLETA B001-00000102)', '2026-01-15 11:20:00'),
(14, 7, 18, 'ingreso', 48.00, 'Cobro servicio envío CE2602K6M8P2R4 (FACTURA F001-00000052)', '2026-02-03 09:40:00'),
(15, 7, 19, 'ingreso', 36.50, 'Cobro servicio envío CE2602B7D9F1H3 (BOLETA B001-00000103)', '2026-02-07 14:10:00'),
(16, 7, 20, 'ingreso', 120.00, 'Cobro servicio envío CE2602J2L4N6Q8 (FACTURA F001-00000053)', '2026-02-12 10:50:00'),
(17, 7, 21, 'ingreso', 22.00, 'Cobro servicio envío CE2602S5U7W9Y1 (BOLETA B001-00000104)', '2026-02-18 11:30:00'),
(18, 8, 22, 'ingreso', 85.00, 'Cobro servicio envío CE2603A2C4E6G8 (FACTURA F001-00000054)', '2026-03-04 09:25:00'),
(19, 8, 23, 'ingreso', 48.00, 'Cobro servicio envío CE2603H1J3L5N7 (BOLETA B001-00000105)', '2026-03-09 10:15:00'),
(20, 8, 24, 'ingreso', 15.00, 'Cobro servicio envío CE2603P9R1T3V5 (BOLETA B001-00000106)', '2026-03-15 12:00:00'),
(21, 8, 25, 'ingreso', 36.50, 'Cobro servicio envío CE2603X7Z9B2D4 (FACTURA F001-00000055)', '2026-03-21 15:10:00'),
(22, 9, 26, 'ingreso', 28.50, 'Cobro servicio envío CE2604F6H8J1L3 (BOLETA B001-00000107)', '2026-04-02 09:30:00'),
(23, 9, 27, 'ingreso', 120.00, 'Cobro servicio envío CE2604N5Q7S9U1 (FACTURA F001-00000056)', '2026-04-07 10:15:00'),
(24, 9, 28, 'ingreso', 22.00, 'Cobro servicio envío CE2604W3Y5A7C9 (BOLETA B001-00000108)', '2026-04-12 11:00:00'),
(25, 9, 29, 'ingreso', 85.00, 'Cobro servicio envío CE2604E2G4I6K8 (FACTURA F001-00000057)', '2026-04-17 14:20:00'),
(26, 9, 30, 'ingreso', 15.00, 'Cobro servicio envío CE2604M0O2Q4S6 (BOLETA B001-00000109)', '2026-04-23 09:40:00'),
(27, 10, 31, 'ingreso', 48.00, 'Cobro servicio envío CE2605U8W0Y2A4 (BOLETA B001-00000110)', '2026-05-03 10:10:00'),
(28, 10, 32, 'ingreso', 36.50, 'Cobro servicio envío CE2605C6E8G0I2 (FACTURA F001-00000058)', '2026-05-08 11:30:00'),
(29, 10, 33, 'ingreso', 120.00, 'Cobro servicio envío CE2605K4M6O8Q0 (BOLETA B001-00000111)', '2026-05-13 14:00:00'),
(30, 10, 34, 'ingreso', 22.00, 'Cobro servicio envío CE2605S2U4W6Y8 (FACTURA F001-00000059)', '2026-05-18 09:50:00'),
(31, 10, 35, 'ingreso', 28.50, 'Cobro servicio envío CE2605A0C2E4G6 (BOLETA B001-00000112)', '2026-05-24 10:40:00'),
(32, 11, 36, 'ingreso', 85.00, 'Cobro servicio envío CE2606I8K0M2O4 (FACTURA F001-00000060)', '2026-06-02 09:15:00'),
(33, 11, 37, 'ingreso', 48.00, 'Cobro servicio envío CE2606Q6S8U0W2 (BOLETA B001-00000113)', '2026-06-07 10:20:00'),
(34, 11, 38, 'ingreso', 15.00, 'Cobro servicio envío CE2606Y4A6C8E0 (BOLETA B001-00000114)', '2026-06-12 11:45:00'),
(35, 11, 39, 'ingreso', 36.50, 'Cobro servicio envío CE2606G2I4K6M8 (FACTURA F001-00000061)', '2026-06-17 14:10:00'),
(36, 11, 40, 'ingreso', 28.50, 'Cobro servicio envío CE2606O0Q2S4U6 (BOLETA B001-00000115)', '2026-06-22 09:30:00'),
(37, 11, 41, 'ingreso', 120.00, 'Cobro servicio envío CE2606W8Y0A2C4 (FACTURA F001-00000062)', '2026-06-27 10:00:00'),
(38, 12, 42, 'ingreso', 22.00, 'Cobro servicio envío CE2607E6G8I0K2 (BOLETA B001-00000116)', '2026-07-02 09:40:00'),
(39, 12, 43, 'ingreso', 85.00, 'Cobro servicio envío CE2607M4O6Q8S0 (FACTURA F001-00000063)', '2026-07-07 10:50:00'),
(40, 12, 44, 'ingreso', 48.00, 'Cobro servicio envío CE2607U2W4Y6A8 (BOLETA B001-00000117)', '2026-07-13 11:20:00'),
(41, 12, 45, 'ingreso', 36.50, 'Cobro servicio envío CE2607C0E2G4I6 (FACTURA F001-00000064)', '2026-07-18 09:30:00'),
(42, 12, 46, 'ingreso', 28.50, 'Cobro servicio envío CE2607K8M0O2Q4 (BOLETA B001-00000118)', '2026-07-23 10:15:00'),
(43, 12, 47, 'ingreso', 120.00, 'Cobro servicio envío CE2607S6U8W0Y2 (FACTURA F001-00000065)', '2026-07-28 14:40:00'),
(44, 13, 48, 'ingreso', 15.00, 'Cobro servicio envío CE2608A4C6E8G0 (BOLETA B001-00000119)', '2026-08-01 09:10:00'),
(45, 13, 49, 'ingreso', 85.00, 'Cobro servicio envío CE2608I2K4M6O8 (FACTURA F001-00000066)', '2026-08-05 10:20:00'),
(46, 13, 50, 'ingreso', 48.00, 'Cobro servicio envío CE2608Q0S2U4W6 (BOLETA B001-00000120)', '2026-08-10 11:30:00'),
(47, 13, 51, 'ingreso', 36.50, 'Cobro servicio envío CE2608Y8A0C2E4 (FACTURA F001-00000067)', '2026-08-15 14:00:00'),
(48, 13, 52, 'ingreso', 22.00, 'Cobro servicio envío CE2608G6I8K0M2 (BOLETA B001-00000121)', '2026-08-20 09:50:00'),
(49, 13, 53, 'ingreso', 120.00, 'Cobro servicio envío CE2608O4Q6S8U0 (FACTURA F001-00000068)', '2026-08-25 10:45:00'),
(50, 13, 54, 'ingreso', 28.50, 'Cobro servicio envío CE2608W2Y4A6C8 (BOLETA B001-00000122)', '2026-08-29 11:15:00'),
(51, 14, 55, 'ingreso', 85.00, 'Cobro servicio envío CE2609E0G2I4K6 (FACTURA F001-00000069)', '2026-09-02 09:20:00'),
(52, 14, 56, 'ingreso', 48.00, 'Cobro servicio envío CE2609M8O0Q2S4 (BOLETA B001-00000123)', '2026-09-07 10:30:00'),
(53, 14, 57, 'ingreso', 36.50, 'Cobro servicio envío CE2609U6W8Y0A2 (FACTURA F001-00000070)', '2026-09-12 11:45:00'),
(54, 14, 58, 'ingreso', 28.50, 'Cobro servicio envío CE2609C4E6G8I0 (BOLETA B001-00000124)', '2026-09-17 14:10:00'),
(55, 14, 59, 'ingreso', 120.00, 'Cobro servicio envío CE2609K2M4O6Q8 (FACTURA F001-00000071)', '2026-09-22 09:30:00'),
(56, 14, 60, 'ingreso', 22.00, 'Cobro servicio envío CE2609S0U2W4Y6 (BOLETA B001-00000125)', '2026-09-26 10:20:00'),
(57, 14, 61, 'ingreso', 15.00, 'Cobro servicio envío CE2609A8C0E2G4 (BOLETA B001-00000126)', '2026-09-29 11:00:00'),
(58, 15, 62, 'ingreso', 85.00, 'Cobro servicio envío CE2610I6K8M0O2 (FACTURA F001-00000072)', '2026-10-02 09:15:00'),
(59, 15, 63, 'ingreso', 48.00, 'Cobro servicio envío CE2610Q4S6U8W0 (BOLETA B001-00000127)', '2026-10-07 10:45:00'),
(60, 15, 64, 'ingreso', 36.50, 'Cobro servicio envío CE2610Y2A4C6E8 (FACTURA F001-00000073)', '2026-10-12 11:20:00'),
(61, 15, 65, 'ingreso', 120.00, 'Cobro servicio envío CE2610G0I2K4M6 (BOLETA B001-00000128)', '2026-10-17 14:00:00'),
(62, 15, 66, 'ingreso', 28.50, 'Cobro servicio envío CE2610O8Q0S2U4 (FACTURA F001-00000074)', '2026-10-22 09:30:00'),
(63, 15, 67, 'ingreso', 22.00, 'Cobro servicio envío CE2610W6Y8A0C2 (BOLETA B001-00000129)', '2026-10-27 10:15:00'),
(64, 15, 68, 'ingreso', 15.00, 'Cobro servicio envío CE2610E4G6I8K0 (FACTURA F001-00000075)', '2026-10-31 11:30:00'),
(65, 16, 69, 'ingreso', 85.00, 'Cobro servicio envío CE2611M2O4Q6S8 (BOLETA B001-00000130)', '2026-11-02 09:30:00'),
(66, 16, 70, 'ingreso', 48.00, 'Cobro servicio envío CE2611U0W2Y4A6 (FACTURA F001-00000076)', '2026-11-05 10:15:00'),
(67, 16, 71, 'ingreso', 36.50, 'Cobro servicio envío CE2611C8E0G2I4 (BOLETA B001-00000131)', '2026-11-08 11:20:00'),
(68, 16, 72, 'ingreso', 120.00, 'Cobro servicio envío CE2611K6M8O0Q2 (FACTURA F001-00000077)', '2026-11-11 14:00:00'),
(69, 16, 73, 'ingreso', 28.50, 'Cobro servicio envío CE2611S4U6W8Y0 (BOLETA B001-00000132)', '2026-11-14 09:45:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.movimientos_caja_id_seq', 69, true);

-- ------------------------------------------------------------------------------
-- 5. HISTORIAL DE SEGUIMIENTO (IDs 60 AL 200+)
-- ------------------------------------------------------------------------------
INSERT INTO public.historial_envios (id, envio_id, estado, descripcion, ubicacion, usuario_id, creado_en) VALUES
-- Envío 15
(60, 15, 'registrado', 'Envío registrado en ventanilla de Agencia #1.', 'Agencia #1', 9, '2026-01-05 09:15:00'),
(61, 15, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2601L8K2M9P1.', 'Agencia #1', 9, '2026-01-05 10:00:00'),
(62, 15, 'en_transito', 'Despachado en ruta interprovincial en Guía #2007.', 'Ruta Nacional #1-#2', 15, '2026-01-05 23:15:00'),
(63, 15, 'en_agencia', 'Arribo confirmado e ingresado al almacén de Agencia #2.', 'Agencia #2', 13, '2026-01-07 07:15:00'),
(64, 15, 'entregado', 'Entrega conforme efectuada satisfactoriamente al destinatario.', 'Agencia #2', 10, '2026-01-07 14:20:00'),

-- Envío 16
(65, 16, 'registrado', 'Envío registrado en ventanilla de Agencia #3.', 'Agencia #3', 12, '2026-01-09 10:30:00'),
(66, 16, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2601T4V7X2A8.', 'Agencia #3', 12, '2026-01-09 11:15:00'),
(67, 16, 'en_transito', 'Despachado en ruta interprovincial en Guía #2008.', 'Ruta Nacional #3-#11', 19, '2026-01-10 00:30:00'),
(68, 16, 'en_agencia', 'Arribo confirmado e ingresado al almacén de Agencia #11.', 'Agencia #11', 21, '2026-01-11 08:30:00'),
(69, 16, 'en_reparto', 'Asignado a courier 23 para entrega en domicilio Av. Los Álamos 215, Cusco.', 'En Reparto Local #11', 23, '2026-01-11 12:30:00'),
(70, 16, 'entregado', 'Entrega conforme efectuada satisfactoriamente al destinatario.', 'Domicilio Destino', 23, '2026-01-11 16:45:00'),

-- Envío 17
(71, 17, 'registrado', 'Envío registrado en ventanilla de Agencia #19.', 'Agencia #19', 24, '2026-01-15 11:20:00'),
(72, 17, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2601C9D3F5G7.', 'Agencia #19', 24, '2026-01-15 12:05:00'),
(73, 17, 'en_transito', 'Despachado en ruta interprovincial en Guía #2009.', 'Ruta Nacional #19-#21', 27, '2026-01-16 01:20:00'),
(74, 17, 'en_agencia', 'Arribo confirmado e ingresado al almacén de Agencia #21.', 'Agencia #21', 29, '2026-01-17 07:20:00'),
(75, 17, 'entregado', 'Entrega conforme efectuada satisfactoriamente al destinatario.', 'Agencia #21', 28, '2026-01-17 11:10:00'),

-- Envío 33 (Caso de Siniestro para alertar en Mayos)
(76, 33, 'registrado', 'Envío registrado en ventanilla de Agencia #1.', 'Agencia #1', 9, '2026-05-13 14:00:00'),
(77, 33, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2605K4M6O8Q0.', 'Agencia #1', 9, '2026-05-13 14:45:00'),
(78, 33, 'en_transito', 'Despachado en ruta interprovincial en Guía #2025.', 'Ruta Nacional #1-#11', 27, '2026-05-14 04:00:00'),
(79, 33, 'siniestrado', 'Incidencia Grave / Siniestro: Desperfecto mecánico mayor con volcadura y daño total de mercadería. Notificación formal y reporte generado.', 'Carretera Central Km 142', 11, '2026-05-14 22:30:00'),

-- Envío 71 (Noviembre en tránsito)
(80, 71, 'registrado', 'Envío registrado en ventanilla de Agencia #3.', 'Agencia #3', 12, '2026-11-08 11:20:00'),
(81, 71, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2611C8E0G2I4.', 'Agencia #3', 12, '2026-11-08 12:05:00'),
(82, 71, 'en_transito', 'Despachado en ruta interprovincial en Guía #2031.', 'Ruta Nacional #3-#11', 15, '2026-11-09 01:20:00'),

-- Envío 72 (Noviembre en tránsito)
(83, 72, 'registrado', 'Envío registrado en ventanilla de Agencia #19.', 'Agencia #19', 24, '2026-11-11 14:00:00'),
(84, 72, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2611K6M8O0Q2.', 'Agencia #19', 24, '2026-11-11 14:45:00'),
(85, 72, 'en_transito', 'Despachado en ruta interprovincial en Guía #2032.', 'Ruta Nacional #19-#7', 19, '2026-11-12 04:00:00'),

-- Envío 73 (Noviembre recepcionado)
(86, 73, 'registrado', 'Envío registrado en ventanilla de Agencia #21.', 'Agencia #21', 28, '2026-11-14 09:45:00'),
(87, 73, 'recepcionado', 'Paquete recibido, pesado y etiquetado con código CE2611S4U6W8Y0.', 'Agencia #21', 28, '2026-11-14 10:30:00'),

-- Envío 74 (Noviembre registrado pendiente de pago)
(88, 74, 'registrado', 'Envío registrado en ventanilla de Agencia #23. Pendiente de confirmación de pago.', 'Agencia #23', 32, '2026-11-16 11:15:00')
ON CONFLICT (id) DO NOTHING;

SELECT pg_catalog.setval('public.historial_envios_id_seq', 88, true);


# 🚀 Guía Rápida - Streamlit App v2.0

**Para usuarios ejecutivos y comerciales**

---

## ⚡ Inicio Rápido (3 minutos)

### 1. Abrir la App

**Opción A - Cloud (Recomendado):**
```
https://proyecto-titulo-pricing-klap.streamlit.app/
```

**Opción B - Local:**
```bash
cd proyecto_pricing_klap
streamlit run app/streamlit_app.py
```

---

### 2. Entender la Navegación

La app tiene 4 secciones principales:

```
┌─────────────────────────────────────────────────────┐
│ 📊 Dashboard Ejecutivo - COMIENZA AQUÍ             │
│    ↓ KPIs + Alertas + Qué atacar primero          │
│                                                     │
│ 🎯 Análisis Detallado                              │
│    ↓ Planes recomendados por comercio             │
│                                                     │
│ 🎮 Simulador                                        │
│    ↓ "Qué pasa si bajo 10bps el MDR?"             │
│                                                     │
│ 📋 Datos Completos                                  │
│    ↓ Exportar a CSV                                │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Tab 1: Dashboard Ejecutivo

### ¿Qué verás?

```
┌────────────────────────────────────────────────────┐
│ 📅 Datos actualizados: 2025-10-25 17:24           │
│                                                    │
│ Comercios: 1,247  │ Volumen: $8.5B               │
│ Margen: $52.3MM   │ Margen %: 0.62%              │
│                                                    │
│ 🚨 Alertas Críticas                                │
│ 🔴 23 comercios con margen negativo               │
│ 🟠 47 comercios >15bps sobre Transbank            │
│                                                    │
│ 🎯 Priorización de Acciones                        │
│ 🔴 Crítico: Ajustar MDR urgente (Score: 87.3)    │
│ 🟠 Alto: Revisar competitividad (Score: 64.5)    │
│                                                    │
│ 📈 Visualizaciones                                 │
│ [Scatter: Margen vs Volumen]                      │
│ [Distribución de Gap Competitivo]                 │
└────────────────────────────────────────────────────┘
```

### ✅ Acciones Recomendadas

1. **Lee las alertas** 🚨
   - Si hay 🔴 roja: Actuar HOY
   - Si hay 🟠 naranja: Actuar esta semana
   - Si hay 🟡 amarilla: Monitorear

2. **Revisa la matriz de priorización**
   - Score >70 = Crítico
   - Score >50 = Alto
   - Score >30 = Medio

3. **Identifica outliers en el scatter plot**
   - Alto volumen + bajo margen = Oportunidad

---

## 🎯 Tab 2: Análisis Detallado

### Planes Recomendados

Verás una tabla con:

| RUT | Plan | MDR | Fijo | Justificación |
|-----|------|-----|------|---------------|
| 12345678-9 | Enterprise | 0.95% | 75 | Alto volumen \| margen negativo |

**Columna "Justificación"** te dice POR QUÉ ese plan:
- "Alto volumen" → Comercio grande, merece descuento
- "Brecha competitiva alta" → Estamos caros vs Transbank
- "Margen negativo" → Estamos perdiendo plata

### ✅ Acciones Recomendadas

1. **Descarga el CSV** (botón abajo de la tabla)
2. **Filtra por cluster** (sidebar izquierda)
3. **Ordena por volumen** (click en columna)

---

## 🎮 Tab 3: Simulador

### Escenarios Preconfigurados

**¿Qué pasa si ajusto tarifas?**

Haz click en uno de estos botones:

```
┌──────────────────┐  ┌──────────────────┐
│ 🟢 Conservador   │  │ 🟡 Igualar TB    │
│ -5bps MDR        │  │ -10bps MDR       │
│ -5 CLP fijo      │  │ -10 CLP fijo     │
└──────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────┐
│ 🔴 Agresivo      │  │ 💎 Premium       │
│ -20bps MDR       │  │ +10bps MDR       │
│ -20 CLP fijo     │  │ +10 CLP fijo     │
└──────────────────┘  └──────────────────┘
```

**Ejemplo de uso:**

```
1. Click en "Igualar Transbank"
2. Selecciona clusters a afectar (ej: "Brecha competitiva")
3. Ve el impacto:

   📊 Impacto Estimado
   Comercios afectados: 47
   Margen actual: $12.5MM
   Margen simulado: $11.2MM ▼ -$1.3MM
```

### ✅ Interpretación

- **Delta negativo** (-$1.3MM): Perdemos margen
  - ⚠️ ¿Vale la pena? Depende si retenemos volumen

- **Delta positivo** (+$2.5MM): Ganamos margen
  - ⚠️ ¿Arriesgado? Puede causar churn

**Regla de oro:** Simula ANTES de negociar con comercios.

---

## 🎨 Filtros (Sidebar Izquierda)

### Cómo Filtrar

```
┌──────────────────────────┐
│ 🔍 Filtros               │
│                          │
│ Cluster analítico:       │
│ ☑ Alto valor             │
│ ☑ Brecha competitiva     │
│ ☐ Oportunidad crecim.    │
│                          │
│ Acción sugerida:         │
│ ☑ Ajustar MDR urgente    │
│ ☐ Mantener / Upsell      │
│                          │
│ Plan comercial Klap:     │
│ ☑ PRO                    │
│ ☑ PRO Max                │
│                          │
│ 📊 Mostrando 234 de      │
│    1,247 comercios       │
└──────────────────────────┘
```

### Ejemplos de Filtros Útiles

**Caso 1: Comercios en riesgo**
```
✓ Cluster: "Brecha competitiva"
✓ Acción: "Ajustar MDR urgente"
→ Resultado: Comercios donde somos caros Y tienen margen malo
```

**Caso 2: Oportunidades de upsell**
```
✓ Cluster: "Alto valor"
✓ Acción: "Mantener / Upsell servicios"
→ Resultado: Comercios grandes y contentos → venderles add-ons
```

**Caso 3: Comercios inactivos**
```
✓ Acción: "Monitorear baja actividad"
✓ Plan: "PRO Max"
→ Resultado: Clientes grandes con baja actividad → riesgo churn
```

---

## 💡 Tips y Trucos

### 1. Hover sobre métricas

```
Margen estimado    ← Haz hover aquí
$52.3MM
```
→ Aparece explicación: "Margen = Ingresos - Costos..."

### 2. Ordena tablas

Click en header de columna para ordenar:
- 1 click: ascendente
- 2 clicks: descendente

### 3. Exporta en cualquier momento

Busca botones:
```
📥 Descargar plan recomendado (CSV)
📥 Descargar datos filtrados (CSV)
```

### 4. Lee las notas al final

Expandible con definiciones completas:
```
📖 Notas y Definiciones  [▼]
```

---

## 🚨 ¿Qué Hacer Si...?

### "No veo datos"

**Problema:** App muestra "No se encontró archivo"

**Solución:**
```bash
# Opción 1: Usar archivos por defecto
ls data/processed/*.parquet

# Opción 2: Subir manualmente
1. Click en sidebar "Datos de entrada"
2. Upload tus archivos .parquet
```

---

### "Faltan columnas requeridas"

**Problema:** Error "falta las siguientes columnas: klap_mdr, ..."

**Solución:**
```bash
# Regenerar archivos Parquet
jupyter notebook pricing_25oct.ipynb
# Ejecutar TODAS las celdas
```

---

### "Archivo de precios no encontrado"

**Problema:** "❌ No se encontró el archivo de precios oficiales"

**Solución:**
```bash
# Verificar archivo existe
ls data/precios_actuales_klap.xlsx

# Si no existe, contactar a BI/Analytics
```

---

## 📱 Uso Desde Móvil

La app funciona en móvil, pero recomendamos **desktop** para:
- Simulaciones complejas
- Análisis de múltiples tablas
- Exportación de datos

**En móvil:** Usa principalmente Tab 1 (Dashboard Ejecutivo) para alertas rápidas.

---

## ⌨️ Atajos de Teclado

- `Ctrl + R` / `Cmd + R`: Recargar app
- `Ctrl + Shift + R`: Forzar recarga (limpia caché)
- Sidebar colapsable: Click en `[>]` arriba a la izquierda

---

## 📊 Flujo de Trabajo Recomendado

### Cada Lunes (5 minutos)

```
1. Abrir app
2. Ir a Dashboard Ejecutivo
3. Leer alertas 🚨
4. Anotar acciones prioritarias
5. Compartir con equipo comercial
```

### Al Preparar Propuesta (15 minutos)

```
1. Filtrar comercios específicos (sidebar)
2. Ir a "Análisis Detallado"
3. Revisar plan recomendado + justificación
4. Ir a "Simulador"
5. Probar escenario "Conservador"
6. Exportar CSV para CRM
```

### Al Revisar Estrategia (30 minutos)

```
1. Dashboard Ejecutivo → KPIs generales
2. Identificar cluster problemático (ej: brecha competitiva)
3. Filtrar solo ese cluster
4. Simulador → Probar escenario "Igualar Transbank"
5. Calcular impacto en P&L
6. Decisión: Go / No Go
7. Si Go: Exportar listado de comercios
```

---

## 🎓 Ejemplos de Casos de Uso

### Caso A: "Tengo 30 minutos, ¿qué hago?"

```
✅ Dashboard Ejecutivo
   - Leer alertas
   - Ver matriz de priorización
   - Screenshot de gráficos para presentación

❌ NO pierdas tiempo en:
   - Datos Completos (muy detallado)
   - Simulaciones complejas
```

### Caso B: "Reunión con CFO mañana"

```
✅ Preparación (20 min):
   1. Dashboard Ejecutivo → Screenshot de KPIs
   2. Matriz de priorización → Anotar score de acciones
   3. Simulador → Calcular impacto de 2-3 escenarios
   4. Preparar slides con números

✅ Durante reunión:
   - Mostrar alertas en vivo
   - Simular escenarios en tiempo real si hay preguntas
```

### Caso C: "Negociación con comercio grande"

```
✅ Antes de negociar (10 min):
   1. Filtrar por RUT del comercio
   2. Ver plan recomendado + justificación
   3. Ver margen actual y gap competitivo
   4. Simulador → ¿Cuánto puedo bajar sin pérdida?

✅ Durante negociación:
   - Si pide descuento: Mostrar simulador en vivo
   - Si duda: Mostrar justificación automática
```

---

## 📞 Soporte

### Documentación Completa

- **README.md** - Guía general del proyecto
- **CHANGELOG_v2.0.md** - Cambios detallados técnicos
- **MEJORAS_IMPLEMENTADAS.md** - Lista de mejoras completa

### Contacto

- **Dudas funcionales:** Equipo comercial / Product
- **Dudas técnicas:** Equipo de Analytics
- **Bugs:** Reportar en canal de Slack o GitHub issues

---

## ✅ Checklist del Primer Uso

- [ ] Abrir app (cloud o local)
- [ ] Ver Dashboard Ejecutivo
- [ ] Hacer hover sobre una métrica (ver tooltip)
- [ ] Leer una alerta 🚨
- [ ] Aplicar un filtro en sidebar
- [ ] Ir a "Análisis Detallado"
- [ ] Ver planes recomendados
- [ ] Ir a "Simulador"
- [ ] Probar escenario "Conservador"
- [ ] Ver impacto estimado
- [ ] Exportar un CSV
- [ ] Expandir "📖 Notas y Definiciones"

---

## 🎯 Resumen en 30 Segundos

```
1️⃣ Abre la app
2️⃣ Dashboard Ejecutivo → Lee alertas 🚨
3️⃣ Matriz de priorización → ¿Qué atacar?
4️⃣ Análisis Detallado → Planes por comercio
5️⃣ Simulador → ¿Qué pasa si...?
6️⃣ Exporta CSV → Actúa
```

**Objetivo:** De datos a decisión en **<5 minutos**.

---

**¡Éxito con tu análisis de pricing! 🚀**

*Última actualización: 2025-11-03 | Versión 2.0*

# Seguridad y Manejo de Datos Confidenciales

## Principios de Seguridad

Este proyecto maneja datos confidenciales de comercios, transacciones y pricing de Klap. Es **CRÍTICO** mantener estos datos fuera del repositorio de Git.

## Archivos Protegidos

### ❌ NUNCA subir a Git:

- **Datos transaccionales**: Cualquier CSV/Excel con datos reales de comercios
- **Archivos parquet procesados**: `data/processed/*.parquet`
- **Notebooks ejecutados**: Los outputs de notebooks pueden contener tablas con datos sensibles
- **Credenciales**: API keys, contraseñas, tokens de acceso
- **Datos de clientes**: RUTs, razones sociales, volúmenes reales

### ✅ Permitido en Git:

- Código fuente (Python, notebooks SIN outputs)
- Archivos de configuración pública
- Grillas de precios oficiales (ya públicas)
- Documentación y README
- Scripts de utilidad

## Workflow de Seguridad

### Antes de cada commit:

1. **Limpiar notebooks**:
   ```bash
   ./scripts/clean_notebooks.sh
   # O manualmente:
   jupyter nbconvert --clear-output --inplace *.ipynb
   ```

2. **Verificar archivos a commitear**:
   ```bash
   git status
   git diff --cached
   ```

3. **Nunca usar `git add .` sin revisar**

### Configuración recomendada:

El archivo `.gitignore` ya está configurado para ignorar:
```
data/processed/
*.parquet
*.csv
*.xlsx  # Excepto precios_actuales_klap.xlsx
```

## Si Accidentalmente Subiste Datos Confidenciales

### Opción 1: Commit reciente (no pusheado)
```bash
git reset --soft HEAD~1
# Limpia el notebook y vuelve a commitear
```

### Opción 2: Ya se hizo push
```bash
# Eliminar el archivo del historial completo de Git
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch ruta/al/archivo.ipynb" \
  --prune-empty --tag-name-filter cat -- --all

# Forzar push (CUIDADO: sobrescribe historial remoto)
git push origin --force --all
```

### Opción 3: Repositorio público por error
1. Hacer el repositorio privado inmediatamente
2. Rotar todas las credenciales expuestas
3. Notificar al equipo de seguridad de Klap
4. Seguir Opción 2 para limpiar historial

## Mejores Prácticas

### Al trabajar con notebooks:

1. **Siempre limpiar outputs antes de commit**:
   - Usa el script: `./scripts/clean_notebooks.sh`
   - O en Jupyter: `Cell > All Output > Clear`

2. **Ejecutar notebooks solo localmente**:
   - Nunca en entornos compartidos sin validación
   - Los outputs se quedan en tu máquina

3. **Usar variables de entorno para rutas sensibles**:
   ```python
   from pathlib import Path
   import os
   
   # ✅ Bien
   DATA_DIR = Path(os.getenv("KLAP_DATA_DIR", "data"))
   
   # ❌ Mal
   df = pd.read_csv("/Users/usuario/klap_confidencial.csv")
   ```

### Al compartir código:

1. **Usa datos sintéticos para demos**:
   ```python
   # Generar datos de prueba
   df_demo = pd.DataFrame({
       'rut_comercio': ['12345678-9'] * 100,
       'monto': np.random.randint(1000, 10000, 100)
   })
   ```

2. **Documenta sin exponer valores reales**:
   ```markdown
   # ✅ Bien
   "El MDR promedio es X%"
   
   # ❌ Mal
   "El comercio 76123456-7 tiene MDR de 2.3%"
   ```

## Checklist de Seguridad

Antes de cada push, verifica:

- [ ] Notebooks sin outputs ejecutados
- [ ] No hay archivos CSV/Excel/parquet nuevos
- [ ] `.gitignore` actualizado si hay nuevos tipos de archivos sensibles
- [ ] No hay credenciales hardcodeadas en el código
- [ ] RUTs y datos de comercios no aparecen en strings literales

## Reportar Problemas de Seguridad

Si detectas una exposición de datos:

1. **No crees un issue público**
2. Contacta directamente al responsable del proyecto
3. Documenta qué se expuso y cuándo
4. Sigue el protocolo de limpieza de historial

---

**Última actualización**: 2025-11-17

Para más información, consulta la documentación interna de seguridad de Klap.

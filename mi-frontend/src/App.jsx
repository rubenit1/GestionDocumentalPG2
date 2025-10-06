// src/App.jsx

import { useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setSelectedFile(file);
    setIsLoading(true);
    setExtractedData(null); 

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/ocr/extract-data', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setExtractedData(response.data);
    } catch (error) {
      console.error('Error al extraer los datos:', error);
      alert('Hubo un error al procesar la imagen.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (event, section, field) => {
    const { value } = event.target;
    const newData = { ...extractedData };
    if (section) {
      newData[section][field] = value;
    } else {
      newData[field] = value;
    }
    setExtractedData(newData);
  };

  const handleSaveContract = async () => {
    if (!extractedData) {
      alert('No hay datos para guardar.');
      return;
    }
    
    // --- LÓGICA AJUSTADA PARA EL GUARDADO ---
    // El backend de /process espera un float, no el string "Q.16,000.00"
    // Lo convertimos de vuelta a número antes de enviar.
    const montoAsString = extractedData.datos_contrato.monto.replace('Q.', '').replace(/,/g, '');
    const montoAsFloat = parseFloat(montoAsString);

    const finalDataForSaving = {
        ...extractedData,
        datos_contrato: {
            ...extractedData.datos_contrato,
            monto: montoAsFloat
        }
    };
    
    // Eliminamos el campo 'monto_en_letras' que no es parte del modelo de guardado
    delete finalDataForSaving.datos_contrato.monto_en_letras;

    try {
      const response = await axios.post('http://localhost:8000/api/v1/contracts/process', finalDataForSaving);
      alert(`¡Contrato guardado con éxito! ID de MongoDB: ${response.data.id_contrato_mongo}`);
      setExtractedData(null);
      setSelectedFile(null);
    } catch (error) {
      console.error('Error al guardar el contrato:', error);
      alert('Hubo un error al guardar el contrato.');
    }
  };

  return (
    <div className="container">
      <h1>Generador Asistido de Contratos</h1>
      
      <div className="card">
        <h2>Paso 1: Cargar Captura de Pantalla</h2>
        <input type="file" accept="image/*" onChange={handleImageUpload} disabled={isLoading} />
        {isLoading && <p>Procesando imagen, por favor espera...</p>}
      </div>

      {extractedData && (
        <div className="card">
          <h2>Paso 2: Verificar y Corregir los Datos</h2>
          <form>
            <fieldset>
              <legend>Datos de la Persona</legend>
              <label>Nombre Completo:</label>
              <input type="text" value={extractedData.datos_persona.nombre_completo} onChange={(e) => handleInputChange(e, 'datos_persona', 'nombre_completo')} />
              <label>CUI (DPI/Pasaporte):</label>
              <input type="text" value={extractedData.datos_persona.cui} onChange={(e) => handleInputChange(e, 'datos_persona', 'cui')} />
              {/* Campo de Fecha de Nacimiento eliminado */}
              <label>Dirección:</label>
              <input type="text" value={extractedData.datos_persona.direccion} onChange={(e) => handleInputChange(e, 'datos_persona', 'direccion')} />
            </fieldset>

            <fieldset>
              <legend>Datos del Contrato</legend>
              <label>Empresa Contratante:</label>
              <input type="text" value={extractedData.empresa_contratante} onChange={(e) => handleInputChange(e, null, 'empresa_contratante')} />
              <label>Tipo de Contrato (Posición):</label>
              <input type="text" value={extractedData.datos_contrato.tipo_contrato} onChange={(e) => handleInputChange(e, 'datos_contrato', 'tipo_contrato')} />
              <label>Monto:</label>
              <input type="text" value={extractedData.datos_contrato.monto} onChange={(e) => handleInputChange(e, 'datos_contrato', 'monto')} />
              {/* Nuevo campo para Monto en Letras (solo lectura) */}
              <label>Monto en Letras:</label>
              <input type="text" value={extractedData.datos_contrato.monto_en_letras} readOnly style={{ backgroundColor: '#e9ecef' }} />
              <label>Fecha de Inicio:</label>
              <input type="text" value={extractedData.datos_contrato.fecha_inicio} onChange={(e) => handleInputChange(e, 'datos_contrato', 'fecha_inicio')} />
               <label>Fecha de Fin:</label>
              <input type="text" value={extractedData.datos_contrato.fecha_fin} onChange={(e) => handleInputChange(e, 'datos_contrato', 'fecha_fin')} />
            </fieldset>
            
            <button type="button" onClick={handleSaveContract}>
              Guardar Contrato
            </button>
          </form>
        </div>
      )}
    </div>
  );
}

export default App;
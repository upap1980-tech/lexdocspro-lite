#!/bin/bash

echo "🔧 Creando atajo 'Procesar Documento Legal Automático'..."

# Crear el atajo usando shortcuts CLI
shortcuts run "Crear nuevo atajo" <<EOF
{
  "name": "Procesar Documento Legal Automático",
  "actions": [
    {
      "type": "GetFile",
      "parameters": {}
    },
    {
      "type": "GetContentsOfURL",
      "parameters": {
        "URL": "http://localhost:5002/api/document/smart-analyze",
        "Method": "POST",
        "RequestBodyType": "Form",
        "FormFields": [
          {
            "Key": "file",
            "Value": "{{Input}}"
          }
        ]
      }
    },
    {
      "type": "GetDictionaryValue",
      "parameters": {
        "DictionaryKey": "cliente_propuesto"
      }
    },
    {
      "type": "GetDictionaryValue",
      "parameters": {
        "DictionaryKey": "carpeta"
      }
    },
    {
      "type": "GetDictionaryValue",
      "parameters": {
        "Input": "{{ContentsOfURL}}",
        "DictionaryKey": "ruta_completa"
      }
    },
    {
      "type": "GetDictionaryValue",
      "parameters": {
        "Input": "{{ContentsOfURL}}",
        "DictionaryKey": "temp_file_path"
      }
    },
    {
      "type": "GetDictionaryValue",
      "parameters": {
        "Input": "{{ContentsOfURL}}",
        "DictionaryKey": "nombre_archivo_sugerido"
      }
    },
    {
      "type": "ShowAlert",
      "parameters": {
        "Title": "📂 Guardar documento",
        "Message": "Cliente: {{DictionaryValue}}\nArchivo: {{DictionaryValue}}\n\n¿Confirmar?",
        "ShowCancelButton": true
      }
    },
    {
      "type": "GetContentsOfURL",
      "parameters": {
        "URL": "http://localhost:5002/api/document/save-organized",
        "Method": "POST",
        "RequestBodyType": "JSON",
        "Headers": {
          "Content-Type": "application/json"
        },
        "JSONBody": {
          "temp_file_path": "{{DictionaryValue}}",
          "dest_path": "{{DictionaryValue}}"
        }
      }
    },
    {
      "type": "ShowNotification",
      "parameters": {
        "Title": "✅ Documento Guardado",
        "Body": "{{DictionaryValue}}"
      }
    }
  ]
}
EOF

echo "✅ Atajo creado con éxito"
echo "📱 Abre la app Atajos para verlo"


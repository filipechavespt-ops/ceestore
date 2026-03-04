#!/bin/bash

# Caminho da pasta do App e do iCloud
APP_DIR="$HOME/GestaoApp"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Backups_Gestao"

# Cria a pasta no iCloud se não existir
mkdir -p "$ICLOUD_DIR"

# Nome do arquivo com data
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="gestao_backup_$TIMESTAMP.db"

# Copia o banco de dados
cp "$APP_DIR/gestao.db" "$ICLOUD_DIR/$BACKUP_NAME"

# Mantém apenas os últimos 7 backups para não lotar o iCloud
ls -t "$ICLOUD_DIR"/gestao_backup_* | tail -n +8 | xargs rm -f

echo "✅ Backup concluído em: $ICLOUD_DIR/$BACKUP_NAME"
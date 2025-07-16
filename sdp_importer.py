#!/usr/bin/env python3
"""
Importador Inteligente de Datos SDP
-----------------------------------
Maneja importación incremental de datos de Seguros del Pichincha
con soporte para nuevos clientes, pólizas variables y cuotas múltiples.
"""

import json
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

from app import app, db
from models import (
    Client, DocumentType, Product, Policy, PolicyInstallment,
    EmisionStatus, PaymentStatus, User
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SDPImporter:
    """Importador inteligente de datos SDP con manejo de duplicados y variaciones."""
    
    def __init__(self):
        self.sdp_agent = None
        self.sdp_product = None
        self.stats = {
            'total_records': 0,
            'unique_policies': 0,
            'new_clients': 0,
            'updated_clients': 0,
            'new_policies': 0,
            'updated_policies': 0,
            'installments_created': 0,
            'errors': 0
        }
        
    def initialize(self):
        """Inicializar agente y producto SDP."""
        self.sdp_agent = User.query.filter_by(email='sdp@previanza.com').first()
        if not self.sdp_agent:
            raise Exception("Agente SDP no encontrado. Ejecutar limpieza primero.")
            
        self.sdp_product = Product.query.filter_by(name='AHORRO PREV - SDP').first()
        if not self.sdp_product:
            raise Exception("Producto SDP no encontrado. Crear producto primero.")
            
        logger.info(f"✅ Inicializado - Agente ID: {self.sdp_agent.id}, Producto ID: {self.sdp_product.id}")
    
    def timestamp_to_date(self, timestamp: Optional[int]) -> Optional[date]:
        """Convertir timestamp de milisegundos a fecha."""
        try:
            if timestamp and timestamp > 0:
                return datetime.fromtimestamp(timestamp / 1000).date()
        except (ValueError, TypeError, OSError):
            pass
        return None
    
    def normalize_string(self, value) -> Optional[str]:
        """Normalizar strings eliminando espacios extra y convirtiendo a None si está vacío."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return str(value)
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized if normalized else None
    
    def parse_decimal(self, value) -> Optional[Decimal]:
        """Convertir valor a Decimal manejando errores."""
        try:
            if value is not None and str(value).strip():
                return Decimal(str(value))
        except (ValueError, TypeError):
            pass
        return None
    
    def map_emission_status(self, sdp_status: Optional[str]) -> EmisionStatus:
        """Mapear estado de póliza SDP a EmisionStatus de Previanza."""
        if not sdp_status:
            return EmisionStatus.PENDIENTE
            
        status_map = {
            'VIGENTE': EmisionStatus.EMITIDA,
            'RENOVADA': EmisionStatus.EMITIDA,
            'EMITIDA': EmisionStatus.EMITIDA,
            'CANCELADA': EmisionStatus.ANULADA,
            'ANULADA': EmisionStatus.ANULADA,
            'CADUCADA': EmisionStatus.CADUCADA,
            'PENDIENTE': EmisionStatus.PENDIENTE,
            'REQUERIMIENTO': EmisionStatus.REQUERIMIENTO
        }
        
        return status_map.get(sdp_status.upper(), EmisionStatus.OTROS)
    
    def map_payment_status(self, sdp_status: Optional[str]) -> PaymentStatus:
        """Mapear estado de cobro SDP a PaymentStatus de Previanza."""
        if not sdp_status:
            return PaymentStatus.PENDIENTE
            
        status_map = {
            # Estados SDP específicos
            'SI': PaymentStatus.PAGADO,
            'NO': PaymentStatus.PENDIENTE,
            # Estados estándar
            'PAGADO': PaymentStatus.PAGADO,
            'COBRADO': PaymentStatus.PAGADO,
            'FACTURADO': PaymentStatus.FACTURADO,
            'PENDIENTE': PaymentStatus.PENDIENTE,
            'REEMBOLSADO': PaymentStatus.REEMBOLSADO
        }
        
        return status_map.get(sdp_status.upper(), PaymentStatus.OTROS)
    
    def find_or_create_client(self, record: Dict) -> Client:
        """Buscar cliente existente o crear nuevo."""
        document_number = self.normalize_string(record.get('Identificación'))
        if not document_number:
            raise ValueError("Cliente sin número de identificación")
        
        # Buscar cliente existente
        client = Client.query.filter_by(document_number=document_number).first()
        
        if client:
            # Actualizar datos si han cambiado
            updated = False
            
            new_name = self.normalize_string(record.get('Cliente'))
            if new_name and client.name != new_name:
                client.name = new_name
                updated = True
                
            new_email = self.normalize_string(record.get('Email'))
            if new_email and client.email != new_email:
                client.email = new_email
                updated = True
                
            new_phone = self.normalize_string(record.get('Celular'))
            if new_phone and client.phone != new_phone:
                client.phone = new_phone
                updated = True
                
            new_address = self.normalize_string(record.get('Dirección'))
            if new_address and client.address != new_address:
                client.address = new_address
                updated = True
            
            if updated:
                self.stats['updated_clients'] += 1
                logger.info(f"Cliente actualizado: {client.name} ({document_number})")
        else:
            # Crear nuevo cliente
            email = self.normalize_string(record.get('Email'))
            if not email:
                email = f"cliente_{document_number}@sdp.previanza.com"  # Email por defecto
                
            client = Client(
                name=self.normalize_string(record.get('Cliente', 'Cliente SDP')),
                email=email,
                phone=self.normalize_string(record.get('Celular')),
                address=self.normalize_string(record.get('Dirección')),
                document_type=DocumentType.DNI,  # Por defecto, ajustar si es necesario
                document_number=document_number,
                is_active=True
            )
            db.session.add(client)
            db.session.flush()  # Obtener ID antes del commit
            self.stats['new_clients'] += 1
            logger.info(f"Cliente creado: {client.name} ({document_number})")
        
        return client
    
    def group_records_by_policy(self, records: List[Dict]) -> Dict[str, List[Dict]]:
        """Agrupar registros por número de póliza para manejar cuotas múltiples."""
        grouped = defaultdict(list)
        
        for record in records:
            policy_num = record.get('Nro Poliza')
            policy_number = str(policy_num) if policy_num is not None else None
            if policy_number:
                grouped[policy_number].append(record)
        
        return dict(grouped)
    
    def create_or_update_policy(self, policy_number: str, records: List[Dict]) -> Policy:
        """Crear o actualizar póliza con sus cuotas."""
        # Usar el primer registro como base para datos de la póliza
        base_record = records[0]
        
        # Buscar póliza existente
        policy = Policy.query.filter_by(policy_number=policy_number).first()
        
        client = self.find_or_create_client(base_record)
        
        if policy:
            # Actualizar póliza existente
            self.stats['updated_policies'] += 1
            logger.info(f"Actualizando póliza: {policy_number}")
        else:
            # Crear nueva póliza
            policy = Policy(
                policy_number=policy_number,
                client_id=client.id if client else None,
                product_id=self.sdp_product.id if self.sdp_product else None,
                agent_id=self.sdp_agent.id if self.sdp_agent else None
            )
            db.session.add(policy)
            self.stats['new_policies'] += 1
            logger.info(f"Creando póliza: {policy_number}")
        
        # Actualizar campos principales
        policy.start_date = self.timestamp_to_date(base_record.get('Vigencia desde')) or date.today()
        policy.end_date = self.timestamp_to_date(base_record.get('Vigencia hasta')) or date.today()
        policy.premium = self.parse_decimal(base_record.get('Prima Total')) or Decimal('0')
        policy.emision_status = self.map_emission_status(base_record.get('Estado Poliza'))
        policy.payment_status = self.map_payment_status(base_record.get('Estado Cobro'))

        # Campos SDP específicos
        policy.net_premium = self.parse_decimal(base_record.get('Prima Neta'))
        policy.savings_amount = self.parse_decimal(base_record.get('Ahorro'))
        policy.payment_method = self.normalize_string(base_record.get('Forma de pago'))
        policy.payment_frequency = self.normalize_string(base_record.get('Frecuencia de Pago'))
        policy.document_sent_date = self.timestamp_to_date(base_record.get('Fecha emisión'))
        policy.last_collection_date = self.timestamp_to_date(base_record.get('Fecha aplicación cobro'))
        policy.financial_entity = self.normalize_string(base_record.get('Entidad financiera'))
        policy.account_type = self.normalize_string(base_record.get('Tipo Cuenta'))
        policy.total_installments = len(records)  # Total de cuotas = registros agrupados
        policy.cause_description = self.normalize_string(base_record.get('Causal'))
        policy.commission_status_sdp = self.normalize_string(base_record.get('Estado comisión'))
        policy.estado_poliza_sdp = self.normalize_string(base_record.get('Estado Poliza'))  # Estado SDP original
        
        # Contar cuotas pagadas
        paid_count = sum(1 for r in records if self.map_payment_status(r.get('Estado Cobro')) == PaymentStatus.PAGADO)
        policy.paid_installments = paid_count
        
        return policy
    
    def create_installments(self, policy: Policy, records: List[Dict]):
        """Crear o actualizar cuotas individuales para la póliza."""
        for i, record in enumerate(records, 1):
            # Buscar cuota existente
            installment = PolicyInstallment.query.filter_by(
                policy_id=policy.id, 
                installment_number=i
            ).first()
            
            if not installment:
                installment = PolicyInstallment(
                    policy_id=policy.id,
                    installment_number=i
                )
                db.session.add(installment)
                self.stats['installments_created'] += 1
            
            # Actualizar datos de la cuota
            installment.amount = self.parse_decimal(record.get('Prima Total')) or Decimal('0')
            installment.payment_status = self.map_payment_status(record.get('Estado Cobro'))
            
            # Mapear fechas correctamente desde JSON SDP
            installment.due_date = self.timestamp_to_date(record.get('Vigencia desde'))  # Fecha vencimiento
            installment.collection_date = self.timestamp_to_date(record.get('Fecha aplicación cobro'))  # Fecha cobro SDP
            
            # Si está pagada, agregar fecha de pago
            if installment.payment_status == PaymentStatus.PAGADO and installment.collection_date:
                installment.payment_date = installment.collection_date
            elif installment.payment_status == PaymentStatus.PAGADO:
                installment.payment_date = date.today()
    
    def import_from_file(self, file_path: str, limit: Optional[int] = None):
        """Importar datos desde archivo JSON SDP."""
        logger.info(f"🚀 Iniciando importación desde: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("El archivo JSON debe contener una lista de registros")
            
            # Aplicar límite si se especifica
            if limit:
                data = data[:limit]
                logger.info(f"⚠️  Limitando importación a {limit} registros")
            
            self.stats['total_records'] = len(data)
            logger.info(f"📊 Registros totales a procesar: {len(data)}")
            
            # Agrupar por número de póliza
            grouped_policies = self.group_records_by_policy(data)
            self.stats['unique_policies'] = len(grouped_policies)
            logger.info(f"🔢 Pólizas únicas detectadas: {len(grouped_policies)}")
            
            # Procesar cada póliza
            for policy_number, records in grouped_policies.items():
                try:
                    logger.info(f"📄 Procesando póliza {policy_number} ({len(records)} cuotas)")
                    
                    # Crear/actualizar póliza
                    policy = self.create_or_update_policy(policy_number, records)
                    
                    # Crear/actualizar cuotas
                    self.create_installments(policy, records)
                    
                    # Commit por póliza para evitar pérdida masiva en caso de error
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"❌ Error procesando póliza {policy_number}: {str(e)}")
                    db.session.rollback()
                    self.stats['errors'] += 1
                    continue
            
            logger.info("✅ Importación completada")
            
        except Exception as e:
            logger.error(f"💥 Error crítico en importación: {str(e)}")
            db.session.rollback()
            raise
    
    def print_stats(self):
        """Imprimir estadísticas de la importación."""
        print("\n" + "="*50)
        print("📊 ESTADÍSTICAS DE IMPORTACIÓN SDP")
        print("="*50)
        print(f"Registros totales procesados: {self.stats['total_records']}")
        print(f"Pólizas únicas detectadas:    {self.stats['unique_policies']}")
        print(f"Clientes nuevos:              {self.stats['new_clients']}")
        print(f"Clientes actualizados:        {self.stats['updated_clients']}")
        print(f"Pólizas nuevas:               {self.stats['new_policies']}")
        print(f"Pólizas actualizadas:         {self.stats['updated_policies']}")
        print(f"Cuotas creadas:               {self.stats['installments_created']}")
        print(f"Errores:                      {self.stats['errors']}")
        print("="*50)

def main():
    """Función principal para ejecutar desde línea de comandos."""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python sdp_importer.py <archivo_json> [limite]")
        print("Ejemplo: python sdp_importer.py /path/to/data.json 100")
        return
    
    file_path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    with app.app_context():
        importer = SDPImporter()
        importer.initialize()
        importer.import_from_file(file_path, limit)
        importer.print_stats()

if __name__ == "__main__":
    main() 